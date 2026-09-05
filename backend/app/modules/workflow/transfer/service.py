import asyncio
import os
import tempfile
from datetime import UTC, datetime

import aiofiles
from fastapi import UploadFile
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_schema import AuthSchema, PageResultSchema
from app.core.exceptions import CustomException
from app.modules.workflow.source.service import StorageSourceService
from app.modules.workflow.transfer.engine import _broadcast, execute_transfer_task
from app.modules.workflow.transfer.registry import transfer_task_registry
from app.utils.common_util import search_to_dict

from .crud import StorageTransferTaskCRUD
from .model import StorageTransferStepModel, StorageTransferTaskModel
from .schema import (
    LocalUploadInfoSchema,
    TransferStepCreateSchema,
    TransferStepOutSchema,
    TransferTargetSchema,
    TransferTaskCreateSchema,
    TransferTaskOutSchema,
    TransferTaskQueryParam,
    TransferTaskStoreSchema,
)


class StorageTransferService:
    """文件传输任务服务（创建 / 查询 / 取消 / 删除）"""

    # 后台传输任务强引用集合：asyncio 对未保存引用的 Task 可能随时 GC（官方文档警告），
    # 完成后通过 done callback 移除，避免泄漏
    _BG_TASKS: set[asyncio.Task] = set()

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        self.auth = auth
        self.db = db

    # ── 内部工具 ────────────────────────────────────────────────────

    def _crud(self) -> StorageTransferTaskCRUD:
        return StorageTransferTaskCRUD(self.auth, self.db)

    async def _validate_targets(self, targets: list[TransferTargetSchema]) -> None:
        """校验目标存储源均存在且启用（批量一次查询）。"""
        source_service = StorageSourceService(self.auth, self.db)
        await source_service.get_active_sources([t.target_id for t in targets])

    @staticmethod
    def _build_steps(data: TransferTaskCreateSchema, local_source_path: str | None = None) -> list[TransferStepCreateSchema]:
        """展开步骤：chain 下每步源继承上一步的目标；parallel 下每步源均为任务源。

        local 源时任务源为服务端临时文件，需显式传入 local_source_path。
        """
        steps: list[TransferStepCreateSchema] = []
        prev_id, prev_path = data.source_id, local_source_path or data.source_path
        for order, target in enumerate(data.targets):
            if data.task_type == "chain":
                source_id, source_path = prev_id, prev_path
            else:
                source_id, source_path = data.source_id, local_source_path or data.source_path
            steps.append(
                TransferStepCreateSchema(
                    step_order=order,
                    source_id=source_id,
                    source_path=source_path,
                    target_id=target.target_id,
                    target_path=target.target_path,
                    transfer_mode=data.transfer_mode,
                    multipart_part_size=data.multipart_part_size,
                    multipart_concurrency=data.multipart_concurrency,
                )
            )
            if data.task_type == "chain":
                prev_id, prev_path = target.target_id, target.target_path
        return steps

    async def _persist(self, data: TransferTaskCreateSchema, local_info: LocalUploadInfoSchema | None = None) -> int:
        """落库任务与步骤（pending），随后启动后台执行。"""
        task = await self._crud().create(
            TransferTaskStoreSchema(
                name=data.name,
                task_type=data.task_type,
                source_type=data.source_type,
                source_id=data.source_id,
                source_path=local_info.source_path if local_info else data.source_path,
                source_name=local_info.source_name if local_info else ((data.source_path or "").rsplit("/", 1)[-1] or None),
                source_size=local_info.source_size if local_info else None,
            ).model_dump()
        )
        local_source_path = local_info.source_path if local_info else None
        for step_data in self._build_steps(data, local_source_path=local_source_path):
            self.db.add(StorageTransferStepModel(task_id=task.id, **step_data.model_dump()))
        # 事务边界在 HTTP 层（db_getter 的 session.begin()），此处只 flush 不 commit
        await self.db.flush()
        self._launch_after_commit(task.id)
        return task.id

    def _launch_after_commit(self, task_id: int) -> None:
        """请求事务提交后再启动后台传输。

        后台任务使用独立会话，若提前启动会读不到未提交的任务行，
        execute_transfer_task 将静默返回，任务永久停留在 pending。
        事务回滚时 after_commit 不触发，任务既未落库也不会启动。
        """

        @event.listens_for(self.db.sync_session, "after_commit", once=True)
        def _launch_on_commit(_session) -> None:
            bg_task = asyncio.create_task(execute_transfer_task(task_id))
            StorageTransferService._BG_TASKS.add(bg_task)
            bg_task.add_done_callback(StorageTransferService._BG_TASKS.discard)

    # ── 创建 ────────────────────────────────────────────────────────

    async def create(self, data: TransferTaskCreateSchema) -> int:
        """创建远端源传输任务。"""
        source_service = StorageSourceService(self.auth, self.db)
        if data.source_type == "remote":
            await source_service.get_active_source(data.source_id)
        await self._validate_targets(data.targets)
        return await self._persist(data)

    async def create_local(self, data: TransferTaskCreateSchema, file: UploadFile) -> int:
        """创建本地源传输任务：文件保存到服务端临时目录，执行完毕后自动清理。"""
        if not file or not file.filename:
            raise CustomException(msg="请选择要上传的文件")
        await self._validate_targets(data.targets)
        fd, temp_path = tempfile.mkstemp(prefix="transfer_upload_", suffix=os.path.splitext(file.filename)[1])
        os.close(fd)
        try:
            async with aiofiles.open(temp_path, "wb") as f:
                while chunk := await file.read(1024 * 1024):
                    await f.write(chunk)
        except Exception:
            os.unlink(temp_path)
            raise
        finally:
            await file.seek(0)
        return await self._persist(
            data,
            local_info=LocalUploadInfoSchema(
                source_path=temp_path,
                source_name=file.filename,
                source_size=os.path.getsize(temp_path),
            ),
        )

    # ── 查询 ────────────────────────────────────────────────────────

    async def page(
        self,
        search: TransferTaskQueryParam | None,
        page_no: int,
        page_size: int,
        order_by: list[dict] | None = None,
    ) -> PageResultSchema[TransferTaskOutSchema]:
        result = await self._crud().page(
            offset=(page_no - 1) * page_size,
            limit=page_size,
            order_by=order_by or [{"id": "desc"}],
            search=search_to_dict(search),
        )
        items = [TransferTaskOutSchema.model_validate(obj) for obj in result.items]
        # 批量加载当前页任务的步骤（前端列表依赖 steps 展示目标/信息列）
        if items:
            task_ids = [item.id for item in items]
            step_result = await self.db.execute(
                select(StorageTransferStepModel)
                .where(
                    StorageTransferStepModel.task_id.in_(task_ids),
                    StorageTransferStepModel.is_deleted.is_(False),
                )
                .order_by(StorageTransferStepModel.step_order)
            )
            steps_map: dict[int, list[TransferStepOutSchema]] = {}
            for step in step_result.scalars().all():
                steps_map.setdefault(step.task_id, []).append(TransferStepOutSchema.model_validate(step))
            for item in items:
                if item.id is not None:
                    item.steps = steps_map.get(item.id, [])
        return PageResultSchema[TransferTaskOutSchema](
            page_no=result.page_no,
            page_size=result.page_size,
            total=result.total,
            has_next=result.has_next,
            items=items,
        )

    async def detail(self, task_id: int) -> TransferTaskOutSchema:
        task = await self._crud().get_or_404(id=task_id)
        out = TransferTaskOutSchema.model_validate(task)
        result = await self.db.execute(
            select(StorageTransferStepModel)
            .where(
                StorageTransferStepModel.task_id == task_id,
                StorageTransferStepModel.is_deleted.is_(False),
            )
            .order_by(StorageTransferStepModel.step_order)
        )
        out.steps = [TransferStepOutSchema.model_validate(step) for step in result.scalars().all()]
        return out

    # ── 操作 ────────────────────────────────────────────────────────

    @staticmethod
    def _remove_local_temp(task: StorageTransferTaskModel) -> None:
        """清理本地源任务的临时文件（幂等：文件不存在时静默忽略）。"""
        if task.source_type == "local" and task.source_path:
            try:
                os.unlink(task.source_path)
            except OSError:
                pass

    async def _push_task(self, task: StorageTransferTaskModel) -> None:
        """将任务最新状态推送到其创建者的 WebSocket（复用引擎广播逻辑）。"""
        result = await self.db.execute(
            select(StorageTransferStepModel)
            .where(
                StorageTransferStepModel.task_id == task.id,
                StorageTransferStepModel.is_deleted.is_(False),
            )
            .order_by(StorageTransferStepModel.step_order)
        )
        await _broadcast(task, list(result.scalars().all()))

    async def cancel(self, task_id: int) -> None:
        task = await self._crud().get_or_404(id=task_id)
        if task.status == "pending":
            # 走 CRUDBase.update：自动补 updated_id 审计字段（flush 由 HTTP 层统一提交）
            await self._crud().update(id=task_id, data={"status": "canceled", "finished_at": datetime.now(UTC)})
            # pending 任务未启动引擎，需在此清理本地源临时文件并即时推送状态
            self._remove_local_temp(task)
            await self._push_task(task)
        elif task.status == "running":
            transfer_task_registry.mark_cancel(task_id)

    async def delete(self, ids: list[int]) -> None:
        for task_id in ids:
            transfer_task_registry.mark_cancel(task_id)
        # 清理本地源任务的临时文件（pending 任务引擎不会执行，需兜底清理）
        result = await self.db.execute(
            select(StorageTransferTaskModel)
            .where(
                StorageTransferTaskModel.id.in_(ids),
                StorageTransferTaskModel.source_type == "local",
                StorageTransferTaskModel.is_deleted.is_(False),
            )
        )
        for task in result.scalars().all():
            self._remove_local_temp(task)
        await self._crud().delete(ids=ids)
