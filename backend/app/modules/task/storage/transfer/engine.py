"""文件传输任务执行引擎

- parallel（多目标）：单源依次输出到多个目标端点
- chain（链式）：步骤串联，上一步目标端点即下一步源，链条长度不限
- 进度按步骤粒度统计（SDK 无逐字节回调），实时写入 DB 并经 SSE 推送；广播仅由
  任务生命周期事件驱动（终态只推一次收尾帧），前端按"有无进行中任务"维持连接
- 后台任务在独立 DB 会话中运行，不阻塞请求；取消采用内存标志（当前步骤执行完毕后生效）
"""

import asyncio
import os
import shutil
import tempfile
from datetime import UTC, datetime
from typing import cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_db_session
from app.core.logger import logger
from app.modules.task.storage.core.base import StorageAdapterConfig
from app.modules.task.storage.core.factory import StorageAdapterFactory
from app.modules.task.storage.node.model import StorageNodeModel
from app.modules.task.storage.node.service import StorageNodeService
from app.modules.task.storage.transfer.registry import transfer_task_registry
from app.modules.task.storage.transfer.sse_manager import transfer_stream_manager

from .model import StorageTransferStepModel, StorageTransferTaskModel
from .schema import TransferMode, TransferStepOutSchema, TransferTaskOutSchema

# 单步最大可显示进度（步骤执行中为流动状态，完成后置 100）
_STEP_RUNNING_PROGRESS = 50


def _step_payload(step: StorageTransferStepModel) -> dict:
    return TransferStepOutSchema.model_validate(step).model_dump(mode="json")


def _task_payload(task: StorageTransferTaskModel, steps: list[StorageTransferStepModel]) -> dict:
    out = TransferTaskOutSchema.model_validate(task)
    out.steps = [TransferStepOutSchema.model_validate(s) for s in steps]
    return out.model_dump(mode="json")


async def _broadcast(task: StorageTransferTaskModel, steps: list[StorageTransferStepModel]) -> None:
    # 进度广播是尽力而为：SSE 抖动/客户端断连不得中断传输流水线本身
    try:
        await transfer_stream_manager.send_to_user(
            task.created_id,
            {"type": "task_update", "data": _task_payload(task, steps)},
        )
    except Exception as e:
        logger.warning("传输任务 {} 进度广播失败（不影响传输）: {}", task.id, e)


async def _build_config(db: AsyncSession, source_id: int) -> StorageAdapterConfig | None:
    """获取存储源并构造适配器配置（复用存储源服务，含 SDK 高级配置）；不存在或停用返回 None。"""
    source = await db.get(StorageNodeModel, source_id)
    if source is None or source.status == 1:
        return None
    return StorageNodeService._build_config(source)


def _remove_local_temp(task: StorageTransferTaskModel) -> None:
    """清理本地源任务的临时文件（幂等：文件不存在时静默忽略）。目录源为本地真实目录，不删除。"""
    if task.source_type == "local" and task.source_path and os.path.isfile(task.source_path):
        try:
            os.unlink(task.source_path)
        except OSError:
            pass


def _local_path_size(path: str) -> int:
    """计算本地文件/目录总大小；目录需递归遍历，属阻塞操作，调用方须经 to_thread 执行。"""
    if os.path.isfile(path):
        return os.path.getsize(path)
    if os.path.isdir(path):
        return sum(os.path.getsize(os.path.join(r, f)) for r, _, files in os.walk(path) for f in files)
    return 0


async def _remove_local_temp_dir(temp_dir: str) -> None:
    """清理下载到临时目录的远端目录（递归删除属阻塞操作）。"""
    if temp_dir and os.path.isdir(temp_dir):
        await asyncio.to_thread(shutil.rmtree, temp_dir, ignore_errors=True)


async def _resolve_source_size(adapter, source_path: str) -> int:
    """尽力获取远端源大小：文件精确匹配，目录递归求和（各协议通用）。"""
    try:
        objects = await adapter.list_files(source_path)
        target = source_path.strip("/")
        for obj in objects:
            if obj.is_dir or obj.key.startswith(f"{target}/"):
                total = 0
                for e in await adapter.list_recursive(source_path):
                    if not e.is_dir and e.size:
                        total += e.size
                return total
        for obj in objects:
            if not obj.is_dir and obj.key == target and obj.size:
                return obj.size
    except Exception as e:
        logger.warning("获取远端源大小失败，进度不显示总大小: {}: {}", source_path, e)
    return 0


async def _is_dir_path(adapter, path: str) -> bool:
    """判断远端路径是否为目录。

    列目录失败直接抛出：若吞掉异常返回 False，目录源会被误判为单文件
    走进错误分支，网络抖动场景下造成静默的数据丢失/漏传。
    """
    objects = await adapter.list_files(path)
    target = path.strip("/")
    return any(o.is_dir or o.key.startswith(f"{target}/") for o in objects)


def _list_local_files(root: str) -> list[tuple[str, str, int]]:
    """递归列出目录下全部文件，返回 (绝对路径, 相对路径, 字节数)。

    整棵树的一次性遍历属阻塞操作，调用方须经 to_thread 执行，避免大目录
    在事件循环里长时间占位。
    """
    files: list[tuple[str, str, int]] = []
    for dirpath, _, names in os.walk(root):
        for name in names:
            local_file = os.path.join(dirpath, name)
            try:
                size = os.path.getsize(local_file)
            except OSError:
                size = 0
            files.append((local_file, os.path.relpath(local_file, root).replace(os.sep, "/"), size))
    return files


def _prepare_local_dirs(paths: list[str]) -> None:
    """批量创建目标文件的父目录（去重，避免逐文件 mkdir 的重复系统调用）。"""
    for parent in {os.path.dirname(p) for p in paths if os.path.dirname(p)}:
        os.makedirs(parent, exist_ok=True)


async def _download_dir(adapter, source_path: str, local_dir: str) -> None:
    """递归下载远端目录到本地临时目录（保留相对结构）。"""
    base = source_path.strip("/")
    targets = [
        (
            e.key,
            os.path.join(
                local_dir,
                (e.key[len(base) + 1 :] if base and e.key.startswith(base + "/") else e.key).replace("/", os.sep),
            ),
        )
        for e in await adapter.list_recursive(source_path)
        if not e.is_dir
    ]
    await asyncio.to_thread(_prepare_local_dirs, [local_file for _, local_file in targets])
    for key, local_file in targets:
        await adapter.download(key, local_file)


async def _run_step(db: AsyncSession, task: StorageTransferTaskModel, step: StorageTransferStepModel) -> bool:
    """执行单个传输步骤，成功返回 True。"""
    started_at = datetime.now(UTC)
    step.status = "running"
    step.started_at = started_at
    step.progress = _STEP_RUNNING_PROGRESS
    await db.commit()
    await _broadcast(task, await _load_steps(db, task.id))

    temp_path: str | None = None
    temp_dir: str | None = None
    src_adapter = None
    dst_adapter = None
    try:
        # 解析源：目录（远端递归下载/本地直接引用）与单文件分别处理
        is_dir_source = False
        if step.source_id is not None:
            src_config = await _build_config(db, step.source_id)
            if src_config is None:
                raise RuntimeError(f"源存储源 {step.source_id} 不存在或已停用")
            src_adapter = StorageAdapterFactory.create(src_config)
            is_dir_source = await _is_dir_path(src_adapter, step.source_path or "")
            if is_dir_source:
                temp_dir = tempfile.mkdtemp(prefix="transfer_dir_")
                await _download_dir(src_adapter, step.source_path or "", temp_dir)
            else:
                fd, temp_path = tempfile.mkstemp(prefix="transfer_", suffix=os.path.splitext(step.target_path)[1])
                os.close(fd)
                await src_adapter.download(step.source_path or "", temp_path)
        elif os.path.isdir(step.source_path or ""):
            is_dir_source = True
            temp_dir = step.source_path or ""
        else:
            temp_path = step.source_path or ""

        if temp_path and not os.path.exists(temp_path):
            raise RuntimeError("源文件不存在")
        if temp_dir and not os.path.isdir(temp_dir):
            raise RuntimeError("源目录不存在")
        if not temp_path and not temp_dir:
            raise RuntimeError("源文件不存在")

        dst_config = await _build_config(db, step.target_id)
        if dst_config is None:
            raise RuntimeError(f"目标存储源 {step.target_id} 不存在或已停用")
        # 连线/任务级传输参数覆盖目标端点配置（分片上传发生在目标端点）；未指定则用存储源默认
        # DB 列以 str 保存传输方式（上游 schema 已按 Literal 校验），此处仅收窄静态类型
        if step.transfer_mode:
            dst_config.transfer_mode = cast(TransferMode | None, step.transfer_mode)
        if step.multipart_part_size:
            dst_config.multipart_part_size = step.multipart_part_size
        if step.multipart_concurrency:
            dst_config.multipart_concurrency = step.multipart_concurrency
        dst_adapter = StorageAdapterFactory.create(dst_config)

        size = 0
        if is_dir_source:
            # 目录上传：一次性列出本地临时目录结构（遍历在线程中完成），再按相对结构写回目标路径
            assert temp_dir is not None  # 目录源已落盘到临时目录或引用本地真实目录
            for local_file, rel, file_size in await asyncio.to_thread(_list_local_files, temp_dir):
                remote = f"{step.target_path}/{rel}".strip("/")
                await dst_adapter.upload(local_file, remote)
                size += file_size
        else:
            assert temp_path is not None  # 单文件源：已落盘或指向本地文件，且上面已校验存在
            size = os.path.getsize(temp_path)
            await dst_adapter.upload(temp_path, step.target_path)

        elapsed = (datetime.now(UTC) - started_at).total_seconds() or 0.01
        speed = size / elapsed
        step.total_size = size
        step.transferred_size = size
        step.speed = speed
        step.status = "success"
        step.progress = 100
        step.finished_at = datetime.now(UTC)
        task.transferred_size += size
        task.speed = speed
        if task.total_size > 0:
            task.progress = min(99, int(task.transferred_size * 100 / task.total_size))
        await db.commit()
        await _broadcast(task, await _load_steps(db, task.id))
        return True
    except Exception as e:
        msg = str(e) or e.__class__.__name__
        step.status = "failed"
        step.error_msg = msg
        step.finished_at = datetime.now(UTC)
        task.status = "failed"
        task.error_msg = msg
        task.finished_at = datetime.now(UTC)
        await db.commit()
        await _broadcast(task, await _load_steps(db, task.id))
        logger.warning("传输任务 {}(步骤 {}) 失败: {}", task.id, step.step_order, msg)
        return False
    finally:
        if src_adapter is not None:
            await src_adapter.close()
        if dst_adapter is not None:
            await dst_adapter.close()
        if temp_path and step.source_id is not None and os.path.exists(temp_path):
            os.unlink(temp_path)
        # 远端目录源下载到临时目录，必须清理；本地目录源为真实目录，不删除
        if step.source_id is not None:
            await _remove_local_temp_dir(temp_dir or "")


async def _load_steps(db: AsyncSession, task_id: int) -> list[StorageTransferStepModel]:
    result = await db.execute(
        select(StorageTransferStepModel)
        .where(
            StorageTransferStepModel.task_id == task_id,
            StorageTransferStepModel.is_deleted.is_(False),
        )
        .order_by(StorageTransferStepModel.step_order)
    )
    return list(result.scalars().all())


async def execute_transfer_task(task_id: int) -> None:
    """后台执行传输任务（由创建接口在事务提交后启动）。

    外壳兜底：任何未预期异常（前置解析、db.refresh 等）都必须把任务从
    pending/running 落到 failed，否则任务永久卡在进行中状态无法收敛。
    """
    try:
        await _execute_transfer_task(task_id)
    except Exception as e:
        logger.exception("传输任务 {} 执行异常中断", task_id)
        try:
            async with async_db_session() as db:
                task = await db.get(StorageTransferTaskModel, task_id)
                if task is not None and task.status in ("pending", "running"):
                    task.status = "failed"
                    task.error_msg = f"任务执行异常中断: {e}"[:500]
                    task.finished_at = datetime.now(UTC)
                    await db.commit()
                    await _broadcast(task, await _load_steps(db, task_id))
        except Exception:
            logger.exception("传输任务 {} 失败状态回写异常", task_id)


async def _execute_transfer_task(task_id: int) -> None:
    """传输任务执行主体。"""
    async with async_db_session() as db:
        task = await db.get(StorageTransferTaskModel, task_id)
        if task is None or task.status != "pending":
            return
        steps = await _load_steps(db, task_id)
        if not steps:
            task.status = "failed"
            task.error_msg = "任务没有可执行的步骤"
            task.finished_at = datetime.now(UTC)
            await db.commit()
            return

        # 解析源文件大小，用于总进度估算
        if task.source_type == "local" and task.source_path:
            task.source_size = await asyncio.to_thread(_local_path_size, task.source_path)
        elif task.source_type == "remote" and task.source_id:
            config = await _build_config(db, task.source_id)
            if config is None:
                task.status = "failed"
                task.error_msg = f"源存储源 {task.source_id} 不存在或已停用"
                task.finished_at = datetime.now(UTC)
                await db.commit()
                await _broadcast(task, steps)
                return
            adapter = StorageAdapterFactory.create(config)
            try:
                task.source_size = await _resolve_source_size(adapter, task.source_path or "")
            finally:
                await adapter.close()
        # 总字节 = 源大小 × 步骤数（每步传输一次源文件，parallel 与 chain 相同）
        task.total_size = (task.source_size or 0) * len(steps)
        task.status = "running"
        task.started_at = datetime.now(UTC)
        await db.commit()
        await _broadcast(task, steps)

        completed = 0
        canceled = False
        deleted = False
        for step in steps:
            # 任务被软删除后中止执行（防竞态：删除请求已标记取消并软删记录）
            await db.refresh(task)
            if task.is_deleted:
                deleted = True
                break
            if transfer_task_registry.is_canceled(task_id):
                canceled = True
                break
            if await _run_step(db, task, step):
                completed += 1
            else:
                break

        transfer_task_registry.clear(task_id)
        if deleted:
            # 任务已删除：不再修改其状态，仅记录日志
            logger.info("传输任务 {} 已删除，中止执行", task_id)
            _remove_local_temp(task)
            return
        if canceled:
            task.status = "canceled"
            task.error_msg = None
            for step in steps:
                if step.status == "pending":
                    step.status = "canceled"
                    step.finished_at = datetime.now(UTC)
        elif completed == len(steps):
            task.status = "success"
            task.progress = 100
        task.finished_at = datetime.now(UTC)
        await db.commit()
        await _broadcast(task, steps)
        logger.info("传输任务 {} 结束: {}", task_id, task.status)

        # 清理本地源临时文件
        _remove_local_temp(task)
