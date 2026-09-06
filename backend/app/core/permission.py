from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.core.base_schema import AuthSchema
from app.core.logger import logger
from app.utils.common_util import get_child_id_map, get_child_recursion


class Permission:
    """为业务模型提供数据权限过滤功能"""

    # 数据权限常量定义，提高代码可读性
    DATA_SCOPE_SELF = 1  # 仅本人数据
    DATA_SCOPE_DEPT_AND_CHILD = 2  # 本部门及以下数据
    DATA_SCOPE_ALL = 3  # 全部数据

    def __init__(self, model: Any, auth: AuthSchema, db: AsyncSession) -> None:
        self.model = model
        self.auth = auth
        self.db = db

    async def filter_query(self, query: Any) -> Any:
        condition = await self._permission_condition()
        return query.where(condition) if condition is not None else query

    async def _permission_condition(self) -> ColumnElement | None:
        if not self.auth.user or not self.auth.user.id:
            return None

        if self.auth.user.is_superuser:
            return None

        return await self._filter_by_data_scope()

    async def _filter_by_data_scope(self) -> ColumnElement | None:
        if not hasattr(self.model, "created_id"):
            return None
        if not self.auth.user or not self.auth.user.id:
            return None

        data_scopes = await self._load_user_data_scopes()

        if self.DATA_SCOPE_ALL in data_scopes:
            return None

        accessible_dept_ids = await self._get_accessible_dept_ids(data_scopes)

        if accessible_dept_ids:
            if self.model.__name__ == "UserModel" and hasattr(self.model, "dept_id"):
                dept_id_attr = getattr(self.model, "dept_id", None)
                if dept_id_attr is not None:
                    return dept_id_attr.in_(list(accessible_dept_ids))

            creator_rel = getattr(self.model, "created_by", None)
            creator_dept_col = Permission._relationship_column(creator_rel, "dept_id")
            if creator_rel is not None and creator_dept_col is not None:
                return creator_rel.has(creator_dept_col.in_(list(accessible_dept_ids)))

            created_id_attr = getattr(self.model, "created_id", None)
            if created_id_attr is not None and self.auth.user and self.auth.user.id:
                return created_id_attr == self.auth.user.id
            return None

        if self.DATA_SCOPE_SELF in data_scopes:
            if self.model.__name__ == "UserModel":
                id_attr = getattr(self.model, "id", None)
                if id_attr is not None and self.auth.user and self.auth.user.id:
                    return id_attr == self.auth.user.id
            created_id_attr = getattr(self.model, "created_id", None)
            if created_id_attr is not None and self.auth.user and self.auth.user.id:
                return created_id_attr == self.auth.user.id
            return None

        created_id_attr = getattr(self.model, "created_id", None)
        if created_id_attr is not None and self.auth.user and self.auth.user.id:
            return created_id_attr == self.auth.user.id
        return None

    @staticmethod
    def _relationship_column(rel: Any, column: str) -> Any | None:
        """取关系目标映射上的列对象（目标模型经 mapper 反射获得，与具体业务模型解耦）。"""
        try:
            target_model = rel.property.mapper.class_
        except (AttributeError, TypeError):
            return None
        if not hasattr(target_model, column):
            return None
        try:
            return getattr(target_model, column)
        except Exception:
            return None

    async def _load_user_data_scopes(self) -> set[int]:
        """读取当前用户角色的数据权限范围集合（data_scope 值）。"""
        from app.modules.system.role.model import RoleModel  # 延迟导入：core 导入期不依赖业务层（守卫不变式 3）
        from app.modules.system.user.model import UserModel

        stmt = select(RoleModel.data_scope).join(RoleModel.users).where(UserModel.id == self.auth.user.id)
        rows = (await self.db.execute(stmt)).scalars().all()
        return {int(scope) for scope in rows}

    async def _get_accessible_dept_ids(self, data_scopes: set) -> set[int]:
        accessible_dept_ids = set()
        user_dept_id = getattr(self.auth.user, "dept_id", None)

        if self.DATA_SCOPE_DEPT_AND_CHILD in data_scopes and user_dept_id is not None:
            try:
                accessible_dept_ids.update(await self._load_dept_children(user_dept_id))
            except Exception as e:
                # 降级为「仅本部门」（最小授权），留日志避免子部门越权范围被静默扩大/缩小不可见
                logger.warning(f"子部门数据权限计算失败，降级为本部门范围: {e}")
                accessible_dept_ids.add(user_dept_id)

        return accessible_dept_ids

    async def _load_dept_children(self, dept_id: int) -> set[int]:
        """按部门树计算某部门的子部门 ID 集合（含自身）。"""
        from app.modules.system.dept.model import DeptModel  # 延迟导入：core 导入期不依赖业务层（守卫不变式 3）

        dept_objs = (await self.db.execute(select(DeptModel))).scalars().all()
        return set(get_child_recursion(id=dept_id, id_map=get_child_id_map(dept_objs)))
