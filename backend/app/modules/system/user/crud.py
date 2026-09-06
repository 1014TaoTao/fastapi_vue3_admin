from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import CRUDBase
from app.core.base_schema import AuthSchema

from .model import UserModel
from .schema import UserCreateSchema, UserUpdateSchema


class UserCRUD(CRUDBase[UserModel, UserCreateSchema, UserUpdateSchema]):
    """用户模块数据层"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        super().__init__(model=UserModel, auth=auth, db=db)

    async def create_obj_crud(self, data: UserCreateSchema) -> UserModel | None:
        """创建用户

        参数:
        - data (UserCreateSchema): 创建模型。

        返回:
        - UserModel | None: 新建实体。
        """
        return await self.create(data=data)

    async def update_last_login(self, id: int) -> UserModel | None:
        """更新用户最后登录时间并返回最新用户；用户不存在时返回 None。

        直接更新实例属性并 flush，保证返回对象内存值与数据库一致
        （set 走 UPDATE 不同步已加载实例，故此处不使用 set）。
        """
        user = await self.db.get(UserModel, id)
        if user is None:
            return None
        user.last_login = datetime.now()
        await self.db.flush()
        return user

    async def set_user_roles(self, user_objs: Sequence[UserModel], role_objs: Sequence[Any]) -> None:
        """替换用户的角色关联（纯数据操作；目标对象加载与校验由 Service 完成）"""
        for obj in user_objs:
            obj.roles.clear()
            obj.roles.extend(role_objs)
        await self.db.flush()

    async def set_user_positions(self, user_objs: Sequence[UserModel], position_objs: Sequence[Any]) -> None:
        """替换用户的岗位关联（纯数据操作；目标对象加载与校验由 Service 完成）"""
        for obj in user_objs:
            obj.positions.clear()
            obj.positions.extend(position_objs)
        await self.db.flush()

    async def change_password(self, id: int, password_hash: str) -> UserModel:
        """修改用户密码

        参数:
        - id (int): 用户ID
        - password_hash (str): 密码哈希值

        返回:
        - UserModel: 更新后的用户信息
        """
        return await self.update(id=id, data=UserUpdateSchema(password=password_hash))

    async def forget_password(self, id: int, password_hash: str) -> UserModel:
        """重置密码（与 change_password 逻辑相同）"""
        return await self.change_password(id=id, password_hash=password_hash)
