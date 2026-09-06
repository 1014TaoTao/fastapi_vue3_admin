from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.core.base_schema import BaseQueryParam, BaseSchema, UserByQueryParam, UserBySchema
from app.core.validator import (
    role_permission_request_validator,
    validate_required_code,
)
from app.modules.system.dept.schema import DeptOutSchema
from app.modules.system.menu.schema import MenuOutSchema


class RoleCreateSchema(BaseModel):
    """角色创建模型
    """

    name: str = Field(..., min_length=1, max_length=64, description="角色名称")
    code: str = Field(..., min_length=2, max_length=64, description="角色编码")
    order: int | None = Field(default=1, ge=0, description="显示排序")
    data_scope: int | None = Field(
        default=1,
        ge=1,
        le=3,
        description="数据权限范围(1:仅本人 2:本部门及以下 3:全部)",
    )
    status: int = Field(default=0, ge=0, le=1, description="状态(0:启动 1:停用)")
    description: str | None = Field(default=None, max_length=255, description="描述")

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str):
        """校验角色编码：字母开头，2-64 位，仅含字母/数字/下划线"""
        return validate_required_code(value)
    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str):
        """校验角色名称：不能为空"""
        v = value.strip()
        if not v:
            raise ValueError("角色名称不能为空")
        return v


class RolePermissionSettingSchema(BaseModel):
    """角色权限配置模型
    """

    data_scope: int = Field(
        default=1,
        ge=1,
        le=3,
        description="数据权限范围(1:仅本人 2:本部门及以下 3:全部)",
    )
    role_ids: list[int] = Field(default_factory=list, description="角色ID列表")
    menu_ids: list[int] = Field(default_factory=list, description="菜单ID列表")
    dept_ids: list[int] = Field(default_factory=list, description="部门ID列表")

    @model_validator(mode="after")
    def validate_fields(self):
        """校验角色权限配置字段（数据范围与关联 ID 等）。

        返回:
        - RolePermissionSettingSchema: 通过 `role_permission_request_validator` 校验后的同一实例。
        """
        return role_permission_request_validator(self)


class RoleUpdateSchema(RoleCreateSchema):
    """角色更新模型
    """


class RoleOutSchema(RoleCreateSchema, BaseSchema, UserBySchema):
    """角色信息响应模型
    """

    model_config = ConfigDict(from_attributes=True)

    menus: list[MenuOutSchema] = Field(default_factory=list, description="角色菜单列表")
    depts: list[DeptOutSchema] = Field(default_factory=list, description="角色部门列表")


class RoleQueryParam(BaseQueryParam, UserByQueryParam):
    """角色管理查询参数
    """

    name: str | None = Field(None, description="角色名称", json_schema_extra={"q": "like"})
    code: str | None = Field(None, description="角色编码", json_schema_extra={"q": "eq"})
    status: int | None = Field(None, description="状态(0:启动 1:停用)", json_schema_extra={"q": "eq"})
