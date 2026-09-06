from collections.abc import Sequence
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import CRUDBase
from app.core.base_schema import AuthSchema

from .model import NodeModel
from .schema import NodeCreateSchema, NodeUpdateSchema


class NodeCRUD(CRUDBase[NodeModel, NodeCreateSchema, NodeUpdateSchema]):
    """节点数据层"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        """初始化节点CRUD

        参数:
        - auth (AuthSchema): 认证信息模型
        - db (AsyncSession): 数据库会话
        """
        super().__init__(model=NodeModel, auth=auth, db=db)

    async def get_obj_by_id_crud(self, id: int, preload: list[str | Any] | None = None) -> NodeModel | None:
        """获取节点详情

        参数:
        - id (int): 节点ID
        - preload (list[str | Any] | None): 预加载关系，未提供时使用模型默认项

        返回:
        - NodeModel | None: 节点模型,如果不存在则为None
        """
        return await self.get(id=id, preload=preload)

    async def get_obj_list_crud(
        self,
        search: dict | None = None,
        order_by: list[dict[str, str]] | None = None,
        preload: list[str | Any] | None = None,
    ) -> Sequence[NodeModel]:
        """获取节点列表

        参数:
        - search (dict | None): 查询参数字典
        - order_by (list[dict[str, str]] | None): 排序参数列表
        - preload (list[str | Any] | None): 预加载关系，未提供时使用模型默认项

        返回:
        - Sequence[NodeModel]: 节点模型序列
        """
        return await self.get_list(search=search, order_by=order_by, preload=preload)

    async def create_obj_crud(self, data: NodeCreateSchema) -> NodeModel | None:
        """创建节点

        参数:
        - data (NodeCreateSchema): 创建节点模型

        返回:
        - NodeModel | None: 创建的节点模型,如果创建失败则为None
        """
        return await self.create(data=data)

    async def update_obj_crud(self, id: int, data: NodeUpdateSchema) -> NodeModel | None:
        """更新节点

        参数:
        - id (int): 节点ID
        - data (NodeUpdateSchema): 更新节点模型

        返回:
        - NodeModel | None: 更新后的节点模型,如果更新失败则为None
        """
        return await self.update(id=id, data=data)

    async def delete_obj_crud(self, ids: list[int]) -> None:
        """删除节点

        参数:
        - ids (list[int]): 节点ID列表

        返回:
        - None
        """
        return await self.delete(ids=ids)

    async def set_obj_field_crud(self, ids: list[int], **kwargs) -> None:
        """设置节点的可用状态

        参数:
        - ids (list[int]): 节点ID列表
        - kwargs: 其他要设置的字段,例如 available=True 或 available=False

        返回:
        - None
        """
        return await self.set(ids=ids, **kwargs)

    async def clear_obj_crud(self) -> None:
        """清除节点日志

        注意:
        - 此操作会删除所有节点日志,请谨慎操作

        返回:
        - None
        """
        return await self.clear()
