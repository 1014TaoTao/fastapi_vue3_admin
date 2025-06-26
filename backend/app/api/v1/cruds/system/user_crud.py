# -*- coding: utf-8 -*-

from typing import Dict, List, Sequence, Optional
from datetime import datetime


from app.core.base_crud import CRUDBase
from app.api.v1.models.system.user_model import UserModel
from app.api.v1.cruds.system.role_crud import RoleCRUD
from app.api.v1.cruds.system.position_crud import PositionCRUD
from app.api.v1.schemas.system.user_schema import (
    UserCreateSchema,
    UserForgetPasswordSchema,
    UserUpdateSchema
)
from app.api.v1.schemas.system.auth_schema import AuthSchema


class UserCRUD(CRUDBase[UserModel, UserCreateSchema, UserUpdateSchema]):
    """用户模块数据层"""

    def __init__(self, auth: AuthSchema) -> None:
        """初始化用户CRUD"""
        super().__init__(model=UserModel, auth=auth)

    async def get_by_id_crud(self, id: str) -> Optional[UserModel]:
        """
        根据id获取用户信息
        
        Args:
            id: 用户ID
            
        Returns:
            Optional[UserModel]: 用户信息
        """
        return await self.get(id=id)

    async def get_by_username_crud(self, username: str) -> Optional[UserModel]:
        """
        根据用户名获取用户信息
        
        Args:
            username: 用户名
            
        Returns:
            Optional[UserModel]: 用户信息
        """
        return await self.get(username=username)
    
    async def get_by_mobile_crud(self, mobile: str) -> Optional[UserModel]:
        """
        根据手机号获取用户信息
        
        Args:
            mobile: 手机号
            
        Returns:
            Optional[UserModel]: 用户信息
        """
        return await self.get(mobile=mobile)

    async def get_list_crud(self, search: Dict = None, order_by: List[Dict[str, str]] = None) -> Sequence[UserModel]:
        """
        获取用户列表
        
        Args:
            search: 搜索条件
            order_by: 排序字段
            
        Returns:
            Sequence[UserModel]: 用户列表
        """
        return await self.list(search=search, order_by=order_by)

    async def update_last_login_crud(self, id: str) -> Optional[UserModel]:
        """
        更新用户最后登录时间
        
        Args:
            id: 用户ID
            
        Returns:
            Optional[UserModel]: 更新后的用户信息
        """
        return await self.update(id=id, data={"last_login": datetime.now()})

    async def set_available_crud(self, ids: List[str], available: bool) -> None:
        """
        批量设置用户可用状态
        
        Args:
            ids: 用户ID列表
            available: 可用状态
        """
        await self.set(ids=ids, available=available)

    async def set_user_roles_crud(self, user_ids: List[str], role_ids: List[str]) -> None:
        """
        批量设置用户角色
        
        Args:
            user_ids: 用户ID列表
            role_ids: 角色ID列表
        """
        user_objs = await self.list(search={"id": ("in", user_ids)})
        if role_ids:
            role_objs = await RoleCRUD(self.auth).get_list_crud(search={"id": ("in", role_ids)})
        else:
            role_objs = []
        await self.update_relationships(
            objs_to_update=user_objs,
            relationship_field="roles",
            related_objs=role_objs
        )

    async def set_user_positions_crud(self, user_ids: List[str], position_ids: List[str]) -> None:
        """
        批量设置用户岗位
        
        Args:
            user_ids: 用户ID列表
            position_ids: 岗位ID列表
        """
        user_objs = await self.list(search={"id": ("in", user_ids)})
        if position_ids:
            position_objs = await PositionCRUD(self.auth).get_list_crud(search={"id": ("in", position_ids)})
        else:
            position_objs = []
        await self.update_relationships(
            objs_to_update=user_objs,
            relationship_field="positions",
            related_objs=position_objs
        )

    async def change_password_crud(self, id: str, password_hash: str) -> Optional[UserModel]:
        """
        修改用户密码
        
        Args:
            id: 用户ID
            password_hash: 密码哈希值
            
        Returns:
            Optional[UserModel]: 更新后的用户信息
        """
        return await self.update(id=id, data={"password": password_hash})

    async def forget_password_crud(self, id: str, password_hash: str) -> Optional[UserModel]:
        """
        重置密码
        
        Args:
            id: 用户ID
            password_hash: 密码哈希值
            
        Returns:
            Optional[UserModel]: 更新后的用户信息
        """
        return await self.update(id=id, data={"password": password_hash})

    async def register_user_crud(self, data: UserForgetPasswordSchema) -> Optional[UserModel]:
        """
        用户注册
        
        Args:
            data: 用户注册信息
            
        Returns:
            Optional[UserModel]: 注册成功的用户信息,如果用户名已存在则返回None
        """
        if await self.get_by_username_crud(username=data.username):
            return None
        
        return await self.create(data=data)
