from collections.abc import Sequence
from typing import Any

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.module_system.dept.crud import DeptCRUD
from app.api.v1.module_system.menu.crud import MenuCRUD
from app.api.v1.module_system.menu.schema import MenuOutSchema, MenuTreeOutSchema
from app.api.v1.module_system.position.crud import PositionCRUD
from app.api.v1.module_system.role.crud import RoleCRUD
from app.config.setting import settings
from app.core.base_schema import AuthSchema, BatchSetAvailable, PageResultSchema
from app.core.exceptions import CustomException
from app.core.logger import logger
from app.utils.common_util import search_to_dict, traversal_to_tree
from app.utils.excel_util import ExcelUtil
from app.utils.password_util import PwdUtil

from .crud import UserCRUD
from .model import UserModel
from .schema import (
    CurrentUserOutSchema,
    CurrentUserUpdateSchema,
    ResetPasswordSchema,
    UserChangePasswordSchema,
    UserCreateSchema,
    UserForgetPasswordSchema,
    UserOutSchema,
    UserQueryParam,
    UserRegisterSchema,
    UserUpdateSchema,
)

# 用户管理列表/详情预加载
_USER_PRELOAD = ["dept", "roles", "positions"]

# 当前用户信息预加载：需完整嵌套关联
_USER_CURRENT_PRELOAD = ["dept", "positions", "roles.menus", "roles.depts"]


class UserService:
    """用户管理服务"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        self.auth = auth
        self.db = db

    async def detail(self, id: int) -> UserOutSchema:
        user = await UserCRUD(self.auth, self.db).get_or_404(id=id, preload=_USER_PRELOAD)
        result = UserOutSchema.model_validate(user)
        if user.dept:
            result.dept_name = user.dept.name
        result.role_ids = [r.id for r in user.roles]
        result.position_ids = [p.id for p in user.positions]
        return result

    async def get_list(
        self,
        search: UserQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> list[UserOutSchema]:
        user_list = await UserCRUD(self.auth, self.db).get_list(search=search_to_dict(search), order_by=order_by, preload=_USER_PRELOAD)
        result = [UserOutSchema.model_validate(user) for user in user_list]
        for user, item in zip(user_list, result, strict=True):
            if user.dept:
                item.dept_name = user.dept.name
            item.role_ids = [r.id for r in user.roles]
            item.position_ids = [p.id for p in user.positions]
        return result

    async def page(
        self,
        page_no: int,
        page_size: int,
        search: UserQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> PageResultSchema[UserOutSchema]:
        offset = (page_no - 1) * page_size
        page_result = await UserCRUD(self.auth, self.db).page(
            offset=offset,
            limit=page_size,
            order_by=order_by or [{"id": "asc"}],
            search=search_to_dict(search),
            preload=_USER_PRELOAD,
        )
        items: list[UserOutSchema] = []
        for user in page_result.items:
            item = UserOutSchema.model_validate(user)
            if user.dept:
                item.dept_name = user.dept.name
            item.role_ids = [r.id for r in user.roles]
            item.position_ids = [p.id for p in user.positions]
            items.append(item)
        page_result.items = items
        return page_result  # type: ignore[return-value]

    async def create(self, data: UserCreateSchema) -> UserOutSchema:
        if data.is_superuser:
            raise CustomException(msg="不允许创建超级管理员")
        if await UserCRUD(self.auth, self.db).get(username=data.username):
            raise CustomException(msg="已存在相同用户名称的账号")

        if data.dept_id and not await DeptCRUD(self.auth, self.db).get(id=data.dept_id):
            raise CustomException(msg="该数据不存在")

        if data.password:
            data.password = await PwdUtil.ahash_password(password=data.password)

        create_data = data.model_dump(exclude_none=True, exclude={"role_ids", "position_ids"})
        new_user = await UserCRUD(self.auth, self.db).create(data=create_data)
        await self._set_user_roles(user_ids=[new_user.id], role_ids=data.role_ids or [])
        await self._set_user_positions(user_ids=[new_user.id], position_ids=data.position_ids or [])
        return await self.detail(id=new_user.id)

    async def update(self, id: int, data: UserUpdateSchema) -> UserOutSchema:
        if data.username:
            if exist_user := await UserCRUD(self.auth, self.db).get(username=data.username):
                if exist_user.id != id:
                    raise CustomException(msg="更新失败，账号已存在")

        if data.mobile:
            if exist_mobile := await UserCRUD(self.auth, self.db).get(mobile=data.mobile):
                if exist_mobile.id != id:
                    raise CustomException(msg="该数据已存在")
        if data.email:
            if exist_email := await UserCRUD(self.auth, self.db).get(email=data.email):
                if exist_email.id != id:
                    raise CustomException(msg="该数据已存在")

        if data.dept_id:
            dept = await DeptCRUD(self.auth, self.db).get(id=data.dept_id)
            if not dept:
                raise CustomException(msg="该数据不存在")
            if dept.status == 1:
                raise CustomException(msg="部门已被禁用")

        update_data = data.model_dump(exclude_unset=True, exclude_none=True, exclude={"role_ids", "position_ids"})
        await UserCRUD(self.auth, self.db).update(id=id, data=update_data)
        await self._set_user_roles(user_ids=[id], role_ids=data.role_ids or [])
        await self._set_user_positions(user_ids=[id], position_ids=data.position_ids or [])

        return await self.detail(id=id)

    async def delete(self, ids: list[int]) -> None:
        if not ids:
            raise CustomException(msg="删除失败，删除对象不能为空")
        users = await UserCRUD(self.auth, self.db).get_list(search={"id": ("in", ids)}, preload=["roles", "positions"])
        user_map = {u.id: u for u in users}
        errors: list[str] = []
        for uid in ids:
            user = user_map.get(uid)
            if not user:
                errors.append(f"用户[{uid}]不存在")
                continue
            if user.is_superuser:
                errors.append(f"用户[{uid}]是超级管理员，不能删除")
                continue
            if self.auth.user.id == uid:
                errors.append("不能删除当前登陆用户")
                continue
        if errors:
            raise CustomException(msg="; ".join(errors))

        # 先解除角色/岗位关联，再删除用户
        await UserCRUD(self.auth, self.db).set_user_roles(user_objs=users, role_objs=[])
        await UserCRUD(self.auth, self.db).set_user_positions(user_objs=users, position_objs=[])
        await UserCRUD(self.auth, self.db).delete(ids=ids)

    async def _load_users(self, user_ids: list[int], preload: list[str]) -> Sequence[UserModel]:
        """加载用户并校验存在性。"""
        if not user_ids:
            raise CustomException(msg="用户ID列表不能为空")
        users = await UserCRUD(self.auth, self.db).get_list(search={"id": ("in", user_ids)}, preload=preload)
        if len(users) != len(set(user_ids)):
            missing = sorted(set(user_ids) - {u.id for u in users})
            raise CustomException(msg=f"用户不存在: {missing}")
        return users

    async def _set_user_roles(self, user_ids: list[int], role_ids: list[int]) -> None:
        """替换用户角色关联：service 校验角色存在性与启用状态，CRUD 仅负责持久化。"""
        if not role_ids:
            return
        users = await self._load_users(user_ids, preload=["roles"])
        roles = await RoleCRUD(self.auth, self.db).get_list(search={"id": ("in", role_ids)})
        missing = set(role_ids) - {r.id for r in roles}
        if missing:
            raise CustomException(msg=f"角色不存在: {sorted(missing)}")
        if any(role.status != 0 for role in roles):
            raise CustomException(msg="部分角色已被禁用")
        await UserCRUD(self.auth, self.db).set_user_roles(user_objs=users, role_objs=roles)

    async def _set_user_positions(self, user_ids: list[int], position_ids: list[int]) -> None:
        """替换用户岗位关联：service 校验岗位存在性与启用状态，CRUD 仅负责持久化。"""
        if not position_ids:
            return
        users = await self._load_users(user_ids, preload=["positions"])
        positions = await PositionCRUD(self.auth, self.db).get_list(search={"id": ("in", position_ids)})
        missing = set(position_ids) - {p.id for p in positions}
        if missing:
            raise CustomException(msg=f"岗位不存在: {sorted(missing)}")
        if any(position.status != 0 for position in positions):
            raise CustomException(msg="部分岗位已被禁用")
        await UserCRUD(self.auth, self.db).set_user_positions(user_objs=users, position_objs=positions)

    async def current_info(self, check_data_scope: bool = True) -> CurrentUserOutSchema:
        user_id = self.auth.user.id
        if not user_id:
            raise CustomException(msg="该数据不存在")

        if not check_data_scope:
            # 轻量模式：只刷新菜单/权限，不加载用户嵌套数据
            menus_raw = await self._load_menus()
            menu_tree = [MenuTreeOutSchema(**item) for item in traversal_to_tree([menu.model_dump(mode="json") for menu in menus_raw])]
            return CurrentUserOutSchema(menus=menu_tree)

        user = await UserCRUD(self.auth, self.db).get(id=user_id, preload=_USER_CURRENT_PRELOAD)
        if user is None:
            raise CustomException(msg="该数据不存在")
        user_dict = CurrentUserOutSchema.model_validate(user)
        if user.dept:
            user_dict.dept_name = user.dept.name
        user_dict.is_superuser = user.is_superuser

        menu_tree = [MenuTreeOutSchema(**item) for item in traversal_to_tree([menu.model_dump(mode="json") for menu in await self._load_menus()])]
        user_dict.menus = menu_tree
        return user_dict

    async def _load_menus(self) -> list[MenuOutSchema]:
        """加载当前用户的菜单列表（不含树形转换）"""
        _pc_only = {"scope": "web"}
        if self.auth.user.is_superuser:
            menu_all = await MenuCRUD(self.auth, self.db).get_list(
                search={"type": ("in", [1, 2, 3, 4]), "status": 0, **_pc_only},
                order_by=[{"order": "asc"}],
            )
            return [MenuOutSchema.model_validate(menu) for menu in menu_all]
        else:
            menu_ids = set(self.auth.menu_ids)
            if not menu_ids:
                return []
            return [
                MenuOutSchema.model_validate(menu)
                for menu in await MenuCRUD(self.auth, self.db).get_list(
                    search={"id": ("in", list(menu_ids)), **_pc_only},
                    order_by=[{"order": "asc"}],
                )
            ]

    async def update_current_info(self, data: CurrentUserUpdateSchema) -> UserOutSchema:
        user_id = self.auth.user.id
        if not user_id:
            raise CustomException(msg="该数据不存在")

        if data.mobile:
            if exist_mobile := await UserCRUD(self.auth, self.db).get(mobile=data.mobile):
                if exist_mobile.id != user_id:
                    raise CustomException(msg="该数据已存在")
        if data.email:
            if exist_email := await UserCRUD(self.auth, self.db).get(email=data.email):
                if exist_email.id != user_id:
                    raise CustomException(msg="该数据已存在")

        user_update_data = UserUpdateSchema(**data.model_dump())
        await UserCRUD(self.auth, self.db).update(id=user_id, data=user_update_data)
        return await self.detail(id=user_id)

    async def set_available(self, data: BatchSetAvailable) -> None:
        users = await UserCRUD(self.auth, self.db).get_list(search={"id": ("in", data.ids)})
        for user in users:
            if user.is_superuser:
                raise CustomException(msg="超级管理员状态不能修改")
        await UserCRUD(self.auth, self.db).set(ids=data.ids, status=data.status)

    async def change_password(self, data: UserChangePasswordSchema) -> UserOutSchema:
        user_id = self.auth.user.id
        if not user_id:
            raise CustomException(msg="该数据不存在")

        user = await UserCRUD(self.auth, self.db).get_or_404(id=user_id)
        if not await PwdUtil.averify_password(plain_password=data.old_password, password_hash=user.password):
            raise CustomException(msg="原密码输入错误")

        new_password_hash = await PwdUtil.ahash_password(password=data.new_password)
        await UserCRUD(self.auth, self.db).change_password(id=user_id, password_hash=new_password_hash)
        return await self.detail(id=user_id)

    async def reset_password(self, data: ResetPasswordSchema) -> UserOutSchema:
        user = await UserCRUD(self.auth, self.db).get_or_404(id=data.id)
        if user.is_superuser:
            raise CustomException(msg="超级管理员密码不能重置")

        new_password_hash = await PwdUtil.ahash_password(password=data.password)
        await UserCRUD(self.auth, self.db).change_password(id=data.id, password_hash=new_password_hash)
        return await self.detail(id=data.id)

    async def forget_password(self, data: UserForgetPasswordSchema) -> UserOutSchema:
        user = await UserCRUD(self.auth, self.db).get_or_404(username=data.username)
        if user.status == 1:
            raise CustomException(msg="用户已停用")
        if user.is_superuser:
            raise CustomException(msg="超级管理员密码不能重置")

        new_password_hash = await PwdUtil.ahash_password(password=data.new_password)
        await UserCRUD(self.auth, self.db).change_password(id=user.id, password_hash=new_password_hash)
        return await self.detail(id=user.id)

    async def register(self, data: UserRegisterSchema) -> UserOutSchema:
        """用户注册"""
        exists_user = await UserCRUD(self.auth, self.db).get(username=data.username)
        if exists_user:
            raise CustomException(msg="已存在相同用户名称的账号")

        create_data = UserCreateSchema(
            username=data.username,
            password=await PwdUtil.ahash_password(password=data.password),
            name=data.name or data.username,
            status=0,
        )
        create_data_dict = create_data.model_dump(exclude_none=True, exclude={"role_ids", "position_ids"})
        new_user = await UserCRUD(self.auth, self.db).create(data=create_data_dict)
        if not new_user:
            raise CustomException(msg="注册失败")
        # 注册时 auth 无用户，created_id/updated_id 未设置，补充为自身ID
        await UserCRUD(self.auth, self.db).set([new_user.id], created_id=new_user.id, updated_id=new_user.id)
        logger.info(f"新用户注册成功: {data.username}")
        return await self.detail(id=new_user.id)

    async def batch_import(self, file: UploadFile, update_support: bool = False) -> str:
        header_dict = {
            "部门编号": "dept_id",
            "账号": "username",
            "昵称": "name",
            "邮箱": "email",
            "手机号": "mobile",
            "性别": "gender",
            "状态": "status",
        }

        try:
            contents = await file.read()
            rows = await ExcelUtil.aread_excel_to_dicts(contents)
            await file.close()

            if not rows:
                raise CustomException(msg="导入文件为空")

            missing_headers = [h for h in header_dict if h not in rows[0]]
            if missing_headers:
                raise CustomException(msg=f"导入文件缺少必要的列: {', '.join(missing_headers)}")

            # 将中文字段名映射为英文字段
            mapped_rows = []
            for row in rows:
                mapped_rows.append({en: row.get(ch) for ch, en in header_dict.items()})

            required_fields = ["username", "name", "dept_id"]
            errors = []
            for field in required_fields:
                missing_count = sum(1 for r in mapped_rows if r.get(field) is None)
                if missing_count:
                    errors.append(f"字段'{field}'有{missing_count}行缺少数据")

            if errors:
                raise CustomException(msg="\n".join(errors))

            success_count = 0
            error_msgs = []

            for i, row in enumerate(mapped_rows, start=2):
                count_delta, err = await self._process_import_row(i, row, update_support)
                if err:
                    error_msgs.append(err)
                else:
                    success_count += count_delta

            result = f"成功导入 {success_count} 条数据"
            if error_msgs:
                result += "\n错误信息:\n" + "\n".join(error_msgs)
            return result

        except Exception as e:
            logger.error(f"批量导入用户失败: {e!s}")
            raise CustomException(msg=f"导入失败: {e!s}") from e

    async def _process_import_row(
        self,
        row_num: int,
        row: dict,
        update_support: bool,
    ) -> tuple[int, str | None]:
        """处理单行导入数据

        验证字段合法性，执行创建或更新操作。

        参数:
        - row_num (int): Excel 行号（用于错误提示）
        - row (dict): 经过字段映射后的用户数据行
        - update_support (bool): 是否支持更新已存在用户

        返回:
        - tuple[int, str | None]: (成功计数增量, 错误信息或 None)
        """
        try:
            username = (str(row["username"]) if row["username"] is not None else "").strip()
            name = (str(row["name"]) if row["name"] is not None else "").strip()
            if not username:
                return 0, f"第{row_num}行: 账号不能为空"
            if not name:
                return 0, f"第{row_num}行: 昵称不能为空"

            dept_id = int(row["dept_id"])
            dept = await DeptCRUD(self.auth, self.db).get(id=dept_id)
            if not dept:
                return 0, f"第{row_num}行: 部门ID {dept_id} 不存在"

            user_data = {
                "username": username,
                "name": name,
                "email": str(row["email"]).strip() if row.get("email") is not None else None,
                "mobile": str(row["mobile"]).strip() if row.get("mobile") is not None else None,
                "gender": str(row["gender"]).strip() if row.get("gender") is not None else "1",
                "status": 0 if str(row["status"]).strip() == "正常" else 1,
                "dept_id": dept_id,
                "password": await PwdUtil.ahash_password(password=settings.PASSWORD_IMPORT_DEFAULT),
            }

            exists_user = await UserCRUD(self.auth, self.db).get(username=user_data["username"])
            if exists_user:
                if exists_user.is_superuser:
                    return 0, f"第{row_num}行: 超级管理员不允许修改"
                if update_support:
                    user_update_data = UserUpdateSchema(**user_data)
                    await UserCRUD(self.auth, self.db).update(id=exists_user.id, data=user_update_data)
                    return 1, None
                else:
                    return 0, f"第{row_num}行: 用户 {user_data['username']} 已存在"
            else:
                user_create_schema = UserCreateSchema(**user_data)
                new_user = await UserCRUD(self.auth, self.db).create(
                    data=user_create_schema.model_dump(exclude_none=True, exclude={"role_ids", "position_ids"})  # type: ignore[arg-type]
                )
                await self._set_user_roles(user_ids=[new_user.id], role_ids=user_create_schema.role_ids or [])
                await self._set_user_positions(user_ids=[new_user.id], position_ids=user_create_schema.position_ids or [])
                return 1, None

        except Exception as e:
            return 0, f"第{row_num}行: 异常{e!s}"

    @staticmethod
    def get_import_template() -> bytes:
        header_list = [
            "部门编号",
            "账号",
            "昵称",
            "邮箱",
            "手机号",
            "性别",
            "状态",
        ]
        selector_header_list = ["性别", "状态"]
        option_list = [
            {"性别": ["男", "女", "未知"]},
            {"状态": ["正常", "停用"]},
        ]
        return ExcelUtil.get_excel_template(
            header_list=header_list,
            selector_header_list=selector_header_list,
            option_list=option_list,
        )

    @staticmethod
    async def export_list(user_list: list[dict[str, Any]]) -> bytes:
        if not user_list:
            raise CustomException(msg="没有数据可导出")

        mapping_dict = {
            "id": "用户编号",
            "avatar": "头像",
            "username": "用户名称",
            "name": "用户昵称",
            "dept_name": "部门",
            "email": "邮箱",
            "mobile": "手机号",
            "gender": "性别",
            "status": "状态",
            "is_superuser": "是否超级管理员",
            "last_login": "最后登录时间",
            "description": "备注",
            "created_time": "创建时间",
            "updated_time": "更新时间",
            "updated_id": "更新者ID",
        }

        data = user_list.copy()
        for item in data:
            item["status"] = "启用" if item.get("status") == 0 else "停用"
            gender = item.get("gender")
            item["gender"] = "男" if gender == "1" else ("女" if gender == "2" else "未知")
            item["is_superuser"] = "是" if item.get("is_superuser") else "否"
            item["creator"] = item.get("created_by", {}).get("name", "未知") if isinstance(item.get("created_by"), dict) else "未知"

        return await ExcelUtil.aexport_list2excel(list_data=data, mapping_dict=mapping_dict)
