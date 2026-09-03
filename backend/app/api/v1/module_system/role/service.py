from collections.abc import Sequence
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.module_system.dept.crud import DeptCRUD
from app.api.v1.module_system.menu.crud import MenuCRUD
from app.core.base_schema import AuthSchema, BatchSetAvailable, PageResultSchema
from app.core.exceptions import CustomException
from app.utils.common_util import search_to_dict
from app.utils.excel_util import ExcelUtil

from .crud import RoleCRUD
from .model import RoleModel
from .schema import (
    RoleCreateSchema,
    RoleOutSchema,
    RolePermissionSettingSchema,
    RoleQueryParam,
    RoleUpdateSchema,
)

_ROLE_PRELOAD = ["menus", "depts"]


class RoleService:
    """角色管理服务

    提供角色 CRUD、权限配置、数据权限范围设置、批量启/禁用、Excel 导出等业务能力。
    """

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        self.auth = auth
        self.db = db

    async def detail(self, id: int) -> RoleOutSchema:
        """获取角色详情

        参数:
        - id (int): 角色ID

        返回:
        - RoleOutSchema: 角色详情响应模型
        """
        obj = await RoleCRUD(self.auth, self.db).get_or_404(id=id, preload=_ROLE_PRELOAD)
        return RoleOutSchema.model_validate(obj)

    async def get_options(self) -> list[dict[str, Any]]:
        """获取角色下拉选项，委托给 RoleCRUD"""
        return await RoleCRUD(self.auth, self.db).get_options()

    async def get_list(
        self,
        search: RoleQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> list[RoleOutSchema]:
        """获取角色列表

        参数:
        - search (RoleQueryParam | None): 查询参数模型
        - order_by (list[dict[str, str]] | None): 排序参数列表

        返回:
        - list[RoleOutSchema]: 角色响应模型列表
        """
        role_list = await RoleCRUD(self.auth, self.db).get_list(search=search_to_dict(search), order_by=order_by, preload=_ROLE_PRELOAD)
        return [RoleOutSchema.model_validate(role) for role in role_list]

    async def page(
        self,
        page_no: int,
        page_size: int,
        search: RoleQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> PageResultSchema[RoleOutSchema]:
        """分页查询角色（数据库 OFFSET/LIMIT）。

        参数:
        - page_no (int): 页码（从 1 开始）
        - page_size (int): 每页条数
        - search (RoleQueryParam | None): 查询条件
        - order_by (list[dict[str, str]] | None): 排序字段列表

        返回:
        - dict: 分页结果（结构由 ``CRUD.page`` 返回约定）
        """
        offset = (page_no - 1) * page_size
        return await RoleCRUD(self.auth, self.db).page(
            offset=offset,
            limit=page_size,
            order_by=order_by or [{"id": "asc"}],
            search=search_to_dict(search),
            out_schema=RoleOutSchema,
            preload=_ROLE_PRELOAD,
        )

    async def create(self, data: RoleCreateSchema) -> RoleOutSchema:
        """
        创建角色

        参数:
        - data (RoleCreateSchema): 创建角色模型

        返回:
        - RoleOutSchema: 新创建的角色响应模型
        """
        role = await RoleCRUD(self.auth, self.db).get(name=data.name)
        if role:
            raise CustomException(msg="创建失败，该数据已存在")
        obj = await RoleCRUD(self.auth, self.db).get(code=data.code)
        if obj:
            raise CustomException(msg="创建失败，编码已存在")

        new_role = await RoleCRUD(self.auth, self.db).create(data=data)
        return await self.detail(id=new_role.id)

    async def update(self, id: int, data: RoleUpdateSchema) -> RoleOutSchema:
        """更新角色

        参数:
        - id (int): 角色ID
        - data (RoleUpdateSchema): 更新角色模型

        返回:
        - RoleOutSchema: 更新后的角色响应模型
        """
        _ = await RoleCRUD(self.auth, self.db).get_or_404(id=id, msg="更新失败，该数据不存在")
        exist_role = await RoleCRUD(self.auth, self.db).get(name=data.name)
        if exist_role and exist_role.id != id:
            raise CustomException(msg="更新失败，名称已存在")
        exist_code = await RoleCRUD(self.auth, self.db).get(code=data.code)
        if exist_code and exist_code.id != id:
            raise CustomException(msg="更新失败，角色编码已存在")
        await RoleCRUD(self.auth, self.db).update(id=id, data=data)
        return await self.detail(id=id)

    async def delete(self, ids: list[int]) -> None:
        """删除角色

        参数:
        - ids (list[int]): 角色ID列表

        返回:
        - None
        """
        if not ids:
            raise CustomException(msg="删除失败，删除对象不能为空")

        # 批量校验角色存在性
        roles = await RoleCRUD(self.auth, self.db).get_list(search={"id": ("in", ids)})
        if len(roles) != len(ids):
            raise CustomException(msg="删除失败，部分ID不存在")

        await RoleCRUD(self.auth, self.db).delete(ids=ids)

    async def set_permission(self, data: RolePermissionSettingSchema) -> None:
        """设置角色权限（菜单 + 数据权限范围）

        存在性校验与跨模块编排在 service 层完成，CRUD 仅做替换持久化。
        """
        await self._set_role_menus(role_ids=data.role_ids, menu_ids=data.menu_ids)

        # 设置数据权限范围（自定义部门关联已废弃，直接清空）
        await RoleCRUD(self.auth, self.db).set(ids=data.role_ids, data_scope=data.data_scope)
        await self._set_role_depts(role_ids=data.role_ids, dept_ids=[])

    async def _load_roles(self, role_ids: list[int], preload: list[str]) -> Sequence[RoleModel]:
        """加载角色并校验存在性。"""
        if not role_ids:
            raise CustomException(msg="角色ID列表不能为空")
        roles = await RoleCRUD(self.auth, self.db).get_list(search={"id": ("in", role_ids)}, preload=preload)
        if len(roles) != len(set(role_ids)):
            missing = sorted(set(role_ids) - {r.id for r in roles})
            raise CustomException(msg=f"角色不存在: {missing}")
        return roles

    async def _set_role_menus(self, role_ids: list[int], menu_ids: list[int]) -> None:
        """替换角色菜单关联：service 校验存在性，CRUD 只负责持久化。"""
        roles = await self._load_roles(role_ids, preload=["menus"])
        menus = [] if not menu_ids else await MenuCRUD(self.auth, self.db).get_list(search={"id": ("in", menu_ids)})
        if menu_ids and len(menus) != len(set(menu_ids)):
            missing = sorted(set(menu_ids) - {m.id for m in menus})
            raise CustomException(msg=f"菜单不存在: {missing}")
        await RoleCRUD(self.auth, self.db).set_role_menus_crud(role_objs=roles, menu_objs=menus)

    async def _set_role_depts(self, role_ids: list[int], dept_ids: list[int]) -> None:
        """替换角色部门关联：service 校验存在性，CRUD 只负责持久化。"""
        roles = await self._load_roles(role_ids, preload=["depts"])
        depts = [] if not dept_ids else await DeptCRUD(self.auth, self.db).get_list(search={"id": ("in", dept_ids)})
        if dept_ids and len(depts) != len(set(dept_ids)):
            missing = sorted(set(dept_ids) - {d.id for d in depts})
            raise CustomException(msg=f"部门不存在: {missing}")
        await RoleCRUD(self.auth, self.db).set_role_depts_crud(role_objs=roles, dept_objs=depts)

    async def set_available(self, data: BatchSetAvailable) -> None:
        """设置角色可用状态

        参数:
        - data (BatchSetAvailable): 批量设置可用状态模型

        返回:
        - None
        """
        roles = await RoleCRUD(self.auth, self.db).get_list(search={"id": ("in", data.ids)})
        role_map = {r.id: r for r in roles}
        for rid in data.ids:
            if rid not in role_map:
                raise CustomException(msg="该数据不存在")
        await RoleCRUD(self.auth, self.db).set(ids=data.ids, status=data.status)

    @staticmethod
    async def export_list(role_list: list[dict[str, Any]]) -> bytes:
        """导出角色列表

        参数:
        - role_list (list[dict[str, Any]]): 角色详情字典列表

        返回:
        - bytes: Excel文件字节流
        """
        # 字段映射配置
        mapping_dict = {
            "id": "角色编号",
            "name": "角色名称",
            "order": "显示顺序",
            "data_scope": "数据权限",
            "status": "状态",
            "description": "备注",
            "created_time": "创建时间",
            "updated_time": "更新时间",
            "created_id": "创建者ID",
            "updated_id": "更新者ID",
        }

        # 数据权限映射
        data_scope_map = {
            1: "仅本人数据权限",
            2: "本部门及以下数据权限",
            3: "全部数据权限",
        }

        # 处理数据
        data = role_list.copy()
        for item in data:
            item["status"] = "启用" if item.get("status") == 0 else "停用"
            item["data_scope"] = data_scope_map.get(item.get("data_scope", 1), "")

        return await ExcelUtil.aexport_list2excel(list_data=data, mapping_dict=mapping_dict)
