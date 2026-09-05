from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.base_schema import BaseQueryParam, BaseSchema
from app.core.validator import menu_request_validator


class MenuCreateSchema(BaseModel):
    """菜单创建模型"""

    name: str = Field(..., min_length=1, max_length=50, description="菜单名称")
    type: int = Field(..., ge=1, le=4, description="菜单类型(1:目录 2:菜单 3:按钮 4:外链)")
    order: int = Field(..., ge=0, description="显示顺序")
    permission: str | None = Field(default=None, max_length=100, description="权限标识")
    icon: str | None = Field(default=None, max_length=50, description="菜单图标")
    route_name: str | None = Field(default=None, max_length=100, description="路由名称")
    route_path: str | None = Field(default=None, max_length=200, description="路由地址")
    component_path: str | None = Field(default=None, max_length=200, description="组件路径")
    redirect: str | None = Field(default=None, max_length=200, description="重定向地址")
    hidden: bool = Field(default=False, description="是否隐藏")
    keep_alive: bool = Field(default=True, description="是否缓存")
    always_show: bool = Field(default=False, description="是否始终显示")
    title: str | None = Field(default=None, max_length=50, description="菜单标题")
    params: list[dict[str, str]] | None = Field(
        default=None,
        description="路由参数，格式为[{key: string, value: string}]",
    )
    affix: bool = Field(default=False, description="是否固定标签页")
    parent_id: int | None = Field(default=None, ge=1, description="父菜单ID")
    status: int = Field(default=0, ge=0, le=1, description="状态(0:启动 1:停用)")
    description: str | None = Field(default=None, max_length=255, description="描述")
    link: str | None = Field(default=None, max_length=500, description="外链地址(仅type=4)")
    is_iframe: bool = Field(default=False, description="是否嵌入iframe")
    is_hide_tab: bool = Field(default=False, description="是否隐藏标签页")
    active_path: str | None = Field(default=None, max_length=200, description="激活菜单路径")
    show_badge: bool = Field(default=False, description="是否显示红点角标")
    show_text_badge: str | None = Field(default=None, max_length=20, description="文字角标内容")
    scope: Literal["web", "app"] = Field(
        default="web",
        description="菜单可见范围(web:管理端 desktop app:移动端)",
    )
    @field_validator("show_text_badge")
    @classmethod
    def _trim_show_text_badge(cls, v: str | None) -> str | None:
        """文字角标：去除首尾空格，保留空串语义（空串 = 清除角标）。"""
        if v is None:
            return None
        return v.strip()

    @model_validator(mode="before")
    @classmethod
    def _normalize(cls, values):
        if isinstance(values, dict):
            for k in [
                "name",
                "icon",
                "permission",
                "route_name",
                "route_path",
                "component_path",
                "redirect",
                "title",
                "description",
                "link",
                "active_path",
            ]:
                if k in values and isinstance(values[k], str):
                    stripped = values[k].strip()
                    values[k] = stripped or None
            if "parent_id" in values and isinstance(values["parent_id"], str):
                try:
                    values["parent_id"] = int(values["parent_id"].strip())
                except (ValueError, TypeError):
                    pass
            if "component_path" in values and isinstance(values["component_path"], str):
                cp = values["component_path"]
                if cp and cp.startswith("/"):
                    raise ValueError("组件路径不能以 / 开头")
        return values

    @model_validator(mode="after")
    def validate_fields(self):
        """统一校验菜单请求字段（委托到 `menu_request_validator`）。

        返回:
        - MenuCreateSchema: 校验后的同一实例。

        异常:
        - CustomException: 字段不满足菜单类型约束时抛出。
        """
        return menu_request_validator(self)


class MenuUpdateSchema(BaseModel):
    """菜单更新模型 — 所有字段可选"""

    name: str | None = Field(default=None, min_length=1, max_length=50, description="菜单名称")
    type: int | None = Field(default=None, ge=1, le=4, description="菜单类型(1:目录 2:菜单 3:按钮 4:外链)")
    order: int | None = Field(default=None, ge=0, description="显示顺序")
    permission: str | None = Field(default=None, max_length=100, description="权限标识")
    icon: str | None = Field(default=None, max_length=50, description="菜单图标")
    route_name: str | None = Field(default=None, max_length=100, description="路由名称")
    route_path: str | None = Field(default=None, max_length=200, description="路由地址")
    component_path: str | None = Field(default=None, max_length=200, description="组件路径")
    redirect: str | None = Field(default=None, max_length=200, description="重定向地址")
    hidden: bool | None = Field(default=None, description="是否隐藏")
    keep_alive: bool | None = Field(default=None, description="是否缓存")
    always_show: bool | None = Field(default=None, description="是否始终显示")
    title: str | None = Field(default=None, max_length=50, description="菜单标题")
    params: list[dict[str, str]] | None = Field(default=None, description="路由参数")
    affix: bool | None = Field(default=None, description="是否固定标签页")
    parent_id: int | None = Field(default=None, ge=1, description="父菜单ID")
    status: int | None = Field(default=None, ge=0, le=1, description="状态(0:启动 1:停用)")
    description: str | None = Field(default=None, max_length=255, description="描述")
    link: str | None = Field(default=None, max_length=500, description="外链地址(仅type=4)")
    is_iframe: bool | None = Field(default=None, description="是否嵌入iframe")
    is_hide_tab: bool | None = Field(default=None, description="是否隐藏标签页")
    active_path: str | None = Field(default=None, max_length=200, description="激活菜单路径")
    show_badge: bool | None = Field(default=None, description="是否显示红点角标")
    show_text_badge: str | None = Field(default=None, max_length=20, description="文字角标内容")
    scope: Literal["web", "app"] | None = Field(
        default=None,
        description="菜单可见范围(web:管理端 app:移动端)",
    )
    parent_name: str | None = Field(default=None, max_length=50, description="父菜单名称")
    @field_validator("show_text_badge")
    @classmethod
    def _trim_show_text_badge(cls, v: str | None) -> str | None:
        """文字角标：去除首尾空格，保留空串语义（空串 = 清除角标）。"""
        if v is None:
            return None
        return v.strip()

    @model_validator(mode="before")
    @classmethod
    def _normalize(cls, values):
        if isinstance(values, dict):
            for k in [
                "name",
                "icon",
                "permission",
                "route_name",
                "route_path",
                "component_path",
                "redirect",
                "title",
                "description",
                "link",
                "active_path",
            ]:
                if k in values and isinstance(values[k], str):
                    stripped = values[k].strip()
                    values[k] = stripped or None
            if "parent_id" in values and isinstance(values["parent_id"], str):
                try:
                    values["parent_id"] = int(values["parent_id"].strip())
                except (ValueError, TypeError):
                    pass
            if "component_path" in values and isinstance(values["component_path"], str) and values["component_path"]:
                if values["component_path"].startswith("/"):
                    raise ValueError("组件路径不能以 / 开头")
        return values

    @model_validator(mode="after")
    def validate_fields(self):
        if self.type is None:
            return self
        return menu_request_validator(self)


class MenuOutSchema(MenuCreateSchema, BaseSchema):
    """菜单详情响应模型（不含 children，用于详情和更新）"""

    model_config = ConfigDict(from_attributes=True)

    parent_name: str | None = Field(default=None, max_length=50, description="父菜单名称")


class MenuTreeOutSchema(MenuOutSchema):
    """菜单树形响应模型（含 children，用于树形列表）"""

    children: list["MenuTreeOutSchema"] | None = Field(default=None, description="子菜单列表")


class MenuQueryParam(BaseQueryParam):
    """菜单管理查询参数（菜单为平台级资源，无用户归属）"""

    name: str | None = Field(None, description="菜单名称", json_schema_extra={"q": "like"})
    route_path: str | None = Field(None, description="路由地址", json_schema_extra={"q": "like"})
    component_path: str | None = Field(None, description="组件路径", json_schema_extra={"q": "like"})
    type: int | None = Field(None, description="菜单类型(1:目录 2:菜单 3:按钮 4:外链)", json_schema_extra={"q": "eq"})
    permission: str | None = Field(None, description="权限标识", json_schema_extra={"q": "eq"})
    description: str | None = Field(None, description="描述", json_schema_extra={"q": "like"})
    status: int | None = Field(None, description="是否启用", json_schema_extra={"q": "eq"})
    scope: str | None = Field(
        None,
        description="菜单范围过滤(web:管理端 desktop app:移动端)",
        json_schema_extra={"q": "eq"},
    )


