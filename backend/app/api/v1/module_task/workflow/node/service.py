from typing import Any

from sqlalchemy import ColumnElement, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.module_task.workflow.core.base import (
    DEFAULT_PORTS,
    StorageAdapterConfig,
    StorageProtocol,
    decrypt_password,
    encrypt_password,
)
from app.api.v1.module_task.workflow.core.factory import StorageAdapterFactory
from app.core.base_schema import AuthSchema, PageResultSchema
from app.core.exceptions import CustomException
from app.utils.common_util import search_to_dict

from .crud import StorageSourceCRUD
from .model import StorageSourceModel
from .schema import StorageSourceCreateSchema, StorageSourceOutSchema, StorageSourceQueryParam, StorageSourceTestSchema, StorageSourceUpdateSchema


class StorageSourceService:
    """存储源管理服务"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        self.auth = auth
        self.db = db

    # ── 内部工具 ────────────────────────────────────────────────────

    def _crud(self) -> StorageSourceCRUD:
        return StorageSourceCRUD(self.auth, self.db)

    @staticmethod
    def _to_out(obj: StorageSourceModel) -> StorageSourceOutSchema:
        out = StorageSourceOutSchema.model_validate(obj)
        out.has_password = bool(obj.password)
        return out

    async def _clear_other_default(self, keep_id: int | None = None) -> None:
        """取消其他存储源的默认标记，保证同时只有一个默认源。"""
        conditions: list[ColumnElement[bool]] = [StorageSourceModel.is_default.is_(True)]
        if keep_id is not None:
            conditions.append(StorageSourceModel.id != keep_id)
        await self.db.execute(update(StorageSourceModel).where(*conditions).values(is_default=False))

    @staticmethod
    def _build_config_from(source: Any, password: str) -> StorageAdapterConfig:
        """从 ORM 或表单对象构造适配器配置（password 为明文，统一处理端口/高级配置）。"""
        return StorageAdapterConfig(
            protocol=StorageProtocol(source.protocol),
            host=source.host,
            port=source.port or DEFAULT_PORTS[StorageProtocol(source.protocol)],
            username=source.username,
            password=password,
            bucket=source.bucket,
            endpoint=source.endpoint,
            scheme=source.scheme,
            region=source.region,
            path_prefix=source.path_prefix,
            is_secure=source.is_secure,
            implicit_tls=source.implicit_tls,
            encrypt_type=source.encrypt_type,
            connection_mode=source.connection_mode,
            encoding=source.encoding,
            multipart_part_size=source.multipart_part_size,
            multipart_concurrency=source.multipart_concurrency,
            multipart_memory_budget=source.multipart_memory_budget,
            advanced_config=source.advanced_config or {},
        )

    @staticmethod
    def _build_config(obj: StorageSourceModel) -> StorageAdapterConfig:
        return StorageSourceService._build_config_from(obj, decrypt_password(obj.password))

    # ── 查询 ────────────────────────────────────────────────────────

    async def detail(self, id: int) -> StorageSourceOutSchema:
        obj = await self._crud().get_or_404(id=id)
        return self._to_out(obj)

    async def page(
        self,
        search: StorageSourceQueryParam | None,
        page_no: int,
        page_size: int,
        order_by: list[dict] | None = None,
    ) -> PageResultSchema[StorageSourceOutSchema]:
        result = await self._crud().page(
            offset=(page_no - 1) * page_size,
            limit=page_size,
            order_by=order_by or [{"id": "asc"}],
            search=search_to_dict(search),
        )
        return PageResultSchema[StorageSourceOutSchema](
            page_no=result.page_no,
            page_size=result.page_size,
            total=result.total,
            has_next=result.has_next,
            items=[self._to_out(obj) for obj in result.items],
        )

    async def get_list(self, search: StorageSourceQueryParam | None = None) -> list[StorageSourceOutSchema]:
        objs = await self._crud().get_list(search=search_to_dict(search), order_by=[{"id": "asc"}])
        return [self._to_out(obj) for obj in objs]

    # ── 写入 ────────────────────────────────────────────────────────

    async def create(self, data: StorageSourceCreateSchema) -> StorageSourceOutSchema:
        exist = await self._crud().get(name=data.name)
        if exist:
            raise CustomException(msg="创建失败，存储源名称已存在")

        payload = data.model_dump(exclude_none=True)
        if payload.get("password"):
            payload["password"] = encrypt_password(payload["password"])

        obj = await self._crud().create(data=payload)
        if data.is_default:
            await self._clear_other_default(keep_id=obj.id)
        return self._to_out(obj)

    async def update(self, id: int, data: StorageSourceUpdateSchema) -> StorageSourceOutSchema:
        await self._crud().get_or_404(id=id, msg="更新失败，该存储源不存在")
        exist = await self._crud().get(name=data.name)
        if exist and exist.id != id:
            raise CustomException(msg="更新失败，存储源名称已存在")

        # 不用 exclude_none：None 表示用户清空可选字段（description/path_prefix/region 等），需落库为 NULL
        payload = data.model_dump(exclude_unset=True)
        if payload.get("password"):
            payload["password"] = encrypt_password(payload["password"])
        else:
            payload.pop("password", None)  # 未传新密码则不修改

        await self._crud().update(id=id, data=payload)
        obj = await self._crud().get_or_404(id=id)
        if data.is_default:
            await self._clear_other_default(keep_id=id)
        return self._to_out(obj)

    async def delete(self, ids: list[int]) -> None:
        if not ids:
            raise CustomException(msg="删除失败，删除对象不能为空")
        await self._crud().delete(ids=ids)

    # ── 连接测试 ────────────────────────────────────────────────────

    async def test_connection(self, id: int) -> bool:
        obj = await self._crud().get_or_404(id=id, msg="该存储源不存在")
        adapter = StorageAdapterFactory.create(self._build_config(obj))
        try:
            ok = await adapter.test_connection()
        finally:
            await adapter.close()
        if not ok:
            raise CustomException(msg="连接失败，请检查存储源配置")
        return True

    async def test_config(self, data: StorageSourceTestSchema) -> bool:
        """使用表单提交的配置直接测试连接（不落库），密码留空且传 source_id 时回退已保存密码。"""
        password = data.password or ""
        if not password and data.source_id:
            obj = await self._crud().get_or_404(id=data.source_id, msg="该存储源不存在")
            password = decrypt_password(obj.password)
        adapter = StorageAdapterFactory.create(self._build_config_from(data, password))
        try:
            ok = await adapter.test_connection()
        finally:
            await adapter.close()
        if not ok:
            raise CustomException(msg="连接失败，请检查存储源配置")
        return True

    # ── 供文件模块复用 ──────────────────────────────────────────────

    async def get_active_source(self, source_id: int | None = None) -> StorageSourceModel:
        """获取可用存储源：优先指定 id；否则默认源；再退化为任一启用源。"""
        if source_id:
            source = await self._crud().get_or_404(id=source_id)
            if source.status == 1:
                raise CustomException(msg="该存储源已停用")
            return source
        source = await self._crud().get(status=0, is_default=True)
        if source:
            return source
        source = await self._crud().get(status=0)
        if source:
            return source
        raise CustomException(msg="未配置可用的存储源，请先在存储源管理中创建")

    async def get_active_sources(self, ids: list[int]) -> list[StorageSourceModel]:
        """批量获取可用存储源：全部存在且启用，任一无效即抛错（一次查询，避免 N+1）。"""
        if not ids:
            return []
        result = await self.db.execute(
            select(StorageSourceModel)
            .where(
                StorageSourceModel.id.in_(ids),
                StorageSourceModel.is_deleted.is_(False),
            )
        )
        objs = list(result.scalars().all())
        missing = [i for i in ids if i not in {o.id for o in objs}]
        if missing:
            raise CustomException(msg=f"存储源不存在: {missing}")
        disabled = [o.name for o in objs if o.status == 1]
        if disabled:
            raise CustomException(msg=f"存储源已停用: {', '.join(disabled)}")
        return objs
