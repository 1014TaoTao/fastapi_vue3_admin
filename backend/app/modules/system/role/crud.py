from collections.abc import Sequence
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import CRUDBase
from app.core.base_schema import AuthSchema

from .model import RoleModel
from .schema import RoleCreateSchema, RoleUpdateSchema


class RoleCRUD(CRUDBase[RoleModel, RoleCreateSchema, RoleUpdateSchema]):
    """角色模块数据层"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        super().__init__(model=RoleModel, auth=auth, db=db)

    async def set_role_menus_crud(self, role_objs: Sequence[RoleModel], menu_objs: Sequence[Any]) -> None:
        """替换角色的菜单关联（纯数据操作；存在性校验与编排由 Service 完成）

        参数:
        - role_objs (Sequence[RoleModel]): 待更新角色（需预加载 menus）
        - menu_objs (Sequence[Any]): 目标菜单对象列表
        """
        for obj in role_objs:
            obj.menus.clear()
            obj.menus.extend(menu_objs)
        await self.db.flush()

    async def set_role_depts_crud(self, role_objs: Sequence[RoleModel], dept_objs: Sequence[Any]) -> None:
        """替换角色的部门关联（纯数据操作；存在性校验与编排由 Service 完成）

        参数:
        - role_objs (Sequence[RoleModel]): 待更新角色（需预加载 depts）
        - dept_objs (Sequence[Any]): 目标部门对象列表
        """
        for obj in role_objs:
            relationship = obj.depts
            relationship.clear()
            relationship.extend(dept_objs)
        await self.db.flush()

    async def get_options(self) -> list[dict[str, Any]]:
        """获取角色下拉选项，返回 [{value, label}]（自动按状态过滤）"""
        items = await self.get_list(search={"status": 0})
        return [{"value": item.id, "label": item.name} for item in items]
