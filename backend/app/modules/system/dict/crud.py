from collections.abc import Sequence
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import CRUDBase
from app.core.base_schema import AuthSchema
from app.modules.system.dict.model import DictDataModel, DictTypeModel
from app.modules.system.dict.schema import (
    DictDataCreateSchema,
    DictDataUpdateSchema,
    DictTypeCreateSchema,
    DictTypeUpdateSchema,
)


class DictTypeCRUD(CRUDBase[DictTypeModel, DictTypeCreateSchema, DictTypeUpdateSchema]):
    """数据字典类型数据层"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        """初始化数据字典类型数据层。

        参数:
        - auth (AuthSchema): 认证信息模型（含 DB 会话等上下文）。
        - db (AsyncSession): 数据库会话。

        返回:
        - None
        """
        super().__init__(model=DictTypeModel, auth=auth, db=db)


class DictDataCRUD(CRUDBase[DictDataModel, DictDataCreateSchema, DictDataUpdateSchema]):
    """数据字典数据层"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        """初始化数据字典项数据层。

        参数:
        - auth (AuthSchema): 认证信息模型（含 DB 会话等上下文）。
        - db (AsyncSession): 数据库会话。

        返回:
        - None
        """
        super().__init__(model=DictDataModel, auth=auth, db=db)

    async def batch_delete(self, ids: list[int], exclude_system: bool = True) -> int:
        """批量删除数据字典数据

        参数:
        - ids (list[int]): 数据字典数据ID列表
        - exclude_system (bool): 是否排除系统默认数据，默认为True

        返回:
        - int: 删除的记录数量
        """
        if exclude_system:
            system_data = await self.get_list(
                search={
                    "id__in": ids,
                    "remark__contains": "系统默认",
                },
            )
            system_ids = [item.id for item in system_data]
            ids = [id for id in ids if id not in system_ids]

        if ids:
            await self.delete(ids=ids)
        return len(ids)

    async def get_list_by_dict_type(self, dict_type: str, status: int | None = 0) -> Sequence[DictDataModel]:
        """根据字典类型获取字典数据列表

        参数:
        - dict_type (str): 字典类型
        - status (str | None): 状态过滤，None表示不过滤

        返回:
        - Sequence[DictDataModel]: 数据字典数据模型序列
        """
        search: dict[str, Any] = {"dict_type": dict_type}
        if status is not None:
            search["status"] = status
        return await self.get_list(search=search, order_by=[{"id": "asc"}])
