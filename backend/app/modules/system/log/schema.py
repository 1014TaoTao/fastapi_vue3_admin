from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.base_schema import BaseQueryParam, BaseSchema

ALLOWED_REQUEST_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]


class LoginLogCreateSchema(BaseModel):
    """新增登录日志"""

    username: str = Field(..., min_length=1, max_length=64, description="用户名")
    status: int = Field(default=1, ge=1, le=2, description="登录状态(1成功 2失败)")
    login_ip: str | None = Field(default=None, max_length=50, description="登录IP地址")
    login_location: str | None = Field(default=None, max_length=255, description="登录位置")
    request_os: str | None = Field(default=None, max_length=64, description="操作系统")
    request_browser: str | None = Field(default=None, max_length=64, description="浏览器")
    msg: str | None = Field(default=None, max_length=255, description="提示消息")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("用户名不能为空")
        if len(v) > 64:
            raise ValueError("用户名长度不能超过64个字符")
        return v


class LoginLogOutSchema(LoginLogCreateSchema, BaseSchema):
    """登录日志响应"""

    model_config = ConfigDict(from_attributes=True)


class LoginLogDetailOutSchema(LoginLogOutSchema):
    """登录日志详情响应"""


class LoginLogQueryParam(BaseQueryParam):
    """登录日志查询参数"""

    username: str | None = Field(None, max_length=64, description="用户名", json_schema_extra={"q": "like"})
    status: int | None = Field(None, description="登录状态(1:成功 2:失败)", json_schema_extra={"q": "eq"})


class OperationLogQueryParam(BaseQueryParam):
    """操作日志查询参数"""

    request_path: str | None = Field(None, description="请求路径", json_schema_extra={"q": "like"})
    request_method: str | None = Field(None, description="请求方式", json_schema_extra={"q": "eq"})
    username: str | None = Field(None, description="用户名", json_schema_extra={"q": "like"})
    status: int | None = Field(None, ge=0, le=1, description="状态(0:成功 1:失败)", json_schema_extra={"q": "eq"})
    request_ip: str | None = Field(None, description="请求IP", json_schema_extra={"q": "eq"})


class OperationLogOutSchema(BaseSchema):
    """操作日志响应模型"""

    model_config = ConfigDict(from_attributes=True)

    username: str = Field(..., description="操作人用户名")
    status: int | None = Field(default=None, description="状态(0:启动 1:停用)")
    description: str | None = Field(default=None, description="描述")
    request_path: str = Field(..., description="请求路径")
    request_method: str = Field(..., description="请求方式")
    response_code: int = Field(..., description="响应状态码")
    process_time: str | None = Field(default=None, description="处理时间")
    request_ip: str | None = Field(default=None, description="请求IP")


class OperationLogDetailOutSchema(OperationLogOutSchema):
    """操作日志详情响应模型"""

    request_payload: str | None = Field(default=None, description="请求体")
    response_json: str | None = Field(default=None, description="响应体")


class OperationLogCreateSchema(BaseModel):
    username: str = Field(..., min_length=1, max_length=64, description="操作人用户名")
    request_path: str = Field(..., min_length=1, max_length=255, description="请求路径")
    request_method: str = Field(..., description="请求方式")
    request_payload: str | None = Field(None, description="请求体")
    response_code: int = Field(200, ge=100, le=599, description="响应状态码")
    response_json: str | None = Field(None, description="响应体")
    process_time: str | None = Field(None, max_length=20, description="处理时间")
    description: str | None = Field(None, description="备注")
    request_ip: str | None = Field(None, max_length=50, description="请求IP")

    @field_validator("request_method")
    @classmethod
    def validate_request_method(cls, value: str) -> str:
        upper_value = value.upper()
        if upper_value not in ALLOWED_REQUEST_METHODS:
            raise ValueError(f"请求方式必须是: {', '.join(ALLOWED_REQUEST_METHODS)}")
        return upper_value
