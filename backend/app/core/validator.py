import re
from datetime import date, datetime, time
from typing import Annotated, Any

from pydantic import AfterValidator, PlainSerializer, WithJsonSchema

from app.common.constant import DATE_DISPLAY_FMT, DATETIME_DISPLAY_FMT, TIME_DISPLAY_FMT
from app.common.enums import RET
from app.config.setting import settings
from app.core.exceptions import CustomException
from app.utils.password_util import PwdUtil

# 自定义日期时间字符串类型
DateTimeStr = Annotated[
    datetime,
    AfterValidator(lambda x: datetime_validator(x)),
    PlainSerializer(
        lambda x: x.strftime(DATETIME_DISPLAY_FMT) if isinstance(x, datetime) else str(x),
        return_type=str,
        when_used="json",
    ),
    WithJsonSchema({"type": "string"}, mode="serialization"),
]

# 自定义日期字符串类型
DateStr = Annotated[
    date,
    AfterValidator(lambda x: date_validator(x)),
    PlainSerializer(
        lambda x: x.strftime(DATE_DISPLAY_FMT) if isinstance(x, date) else str(x),
        return_type=str,
        when_used="json",
    ),
    WithJsonSchema({"type": "string"}, mode="serialization"),
]

# 自定义时间字符串类型
TimeStr = Annotated[
    time,
    AfterValidator(lambda x: time_validator(x)),
    PlainSerializer(
        lambda x: x.strftime(TIME_DISPLAY_FMT) if isinstance(x, time) else str(x),
        return_type=str,
        when_used="json",
    ),
    WithJsonSchema({"type": "string"}, mode="serialization"),
]

# 自定义手机号类型
Telephone = Annotated[
    str,
    AfterValidator(lambda x: mobile_validator(x)),
    PlainSerializer(lambda x: x, return_type=str),
    WithJsonSchema({"type": "string"}, mode="serialization"),
]

# 自定义邮箱类型
Email = Annotated[
    str,
    AfterValidator(lambda x: email_validator(x)),
    PlainSerializer(lambda x: x, return_type=str),
    WithJsonSchema({"type": "string"}, mode="serialization"),
]


def datetime_validator(value: str | datetime) -> datetime:
    """日期格式验证器。

    参数:
    - value (str | datetime): 日期值。

    返回:
    - datetime: 格式化后的日期。

    异常:
    - CustomException: 日期格式无效时抛出。
    """
    try:
        if isinstance(value, str):
            return datetime.strptime(value, DATETIME_DISPLAY_FMT)
        if isinstance(value, datetime):
            return value
    except Exception:
        raise CustomException(code=RET.ERROR.code, msg="无效的日期格式")


def date_validator(value: str | date) -> date:
    """日期格式验证器。

    参数:
    - value (str | date): 日期值。

    返回:
    - date: 格式化后的日期。

    异常:
    - CustomException: 日期格式无效时抛出。
    """
    try:
        if isinstance(value, str):
            return datetime.strptime(value, DATE_DISPLAY_FMT).date()
        if isinstance(value, date):
            return value
    except Exception:
        raise CustomException(code=RET.ERROR.code, msg="无效的日期格式")


def time_validator(value: str | time) -> time:
    """时间格式验证器。

    参数:
    - value (str | time): 时间值。

    返回:
    - time: 格式化后的时间。

    异常:
    - CustomException: 时间格式无效时抛出。
    """
    try:
        if isinstance(value, str):
            return datetime.strptime(value, TIME_DISPLAY_FMT).time()
        if isinstance(value, time):
            return value
    except Exception:
        raise CustomException(code=RET.ERROR.code, msg="无效的时间格式")


def email_validator(value: str) -> str:
    """邮箱地址验证器。

    参数:
    - value (str): 邮箱地址。

    返回:
    - str: 验证后的邮箱地址。

    异常:
    - CustomException: 邮箱格式无效时抛出。
    """
    if not value:
        raise CustomException(code=RET.ERROR.code, msg="邮箱地址不能为空")

    regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not re.match(regex, value):
        raise CustomException(code=RET.ERROR.code, msg="邮箱地址格式不正确")

    return value


def password_validator(
    value: str | None,
    *,
    check_strength: bool = True,
    label: str = "密码",
) -> str | None:
    """口令验证器：长度区间 + 复杂度。

    参数:
    - value (str | None): 口令；``None`` 表示「本次不设置/不修改」，直接放行。
    - check_strength (bool): 是否校验复杂度。改密时的「旧密码」只校验长度——
      否则历史弱口令用户会被永远锁在系统里，无法主动换掉弱口令。
    - label (str): 报错文案中的字段名。

    返回:
    - str | None: 校验通过的口令原值。

    异常:
    - ValueError: 空串、长度越界或复杂度不足（由 pydantic 转成 422 提示给用户）。
    """
    if value is None:
        return None
    if not value.strip():
        raise ValueError(f"{label}不能为空")
    if len(value) < settings.PASSWORD_MIN_LENGTH:
        raise ValueError(f"{label}长度不能少于 {settings.PASSWORD_MIN_LENGTH} 位")
    if len(value) > settings.PASSWORD_MAX_LENGTH:
        raise ValueError(f"{label}长度不能超过 {settings.PASSWORD_MAX_LENGTH} 位")
    if check_strength:
        error = PwdUtil.check_password_strength(value)
        if error:
            raise ValueError(error)
    return value


def mobile_validator(value: str | None) -> str | None:
    """手机号验证器。

    参数:
    - value (str | None): 手机号。

    返回:
    - str | None: 验证后的手机号。

    异常:
    - CustomException: 手机号格式无效时抛出。
    """
    if not value:
        return value

    if len(value) != 11 or not value.isdigit():
        raise CustomException(code=RET.ERROR.code, msg="手机号格式不正确")

    regex = r"^1(3\d|4[4-9]|5[0-35-9]|6[67]|7[013-8]|8[0-9]|9[0-9])\d{8}$"

    if not re.match(regex, value):
        raise CustomException(code=RET.ERROR.code, msg="手机号格式不正确")

    return value


def validate_required_code(value: str | None) -> str:
    """必填编码校验：字母开头，总长 2–64，仅含字母/数字/下划线。

    参数:
    - value (str | None): 编码。

    返回:
    - str: 去空白后的编码。

    异常:
    - ValueError: 为空或格式不合法。
    """
    if value is None or not str(value).strip():
        raise ValueError("编码不能为空")
    v = value.strip()
    if len(v) < 2 or len(v) > 64:
        raise ValueError("编码长度需在 2-64 个字符之间")
    if not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", v):
        raise ValueError("编码需以字母开头，仅允许字母、数字、下划线")
    return v


def code_validator(value: str | None) -> str | None:
    """可选编码验证器（为空则跳过）。

    参数:
    - value (str | None): 编码。

    返回:
    - str | None: 验证后的编码；未填写时返回 None。

    异常:
    - CustomException: 已填写但格式无效时抛出。
    """
    if not value:
        return value
    v = value.strip()
    if not v:
        return None
    if not re.match(r"^[A-Za-z][A-Za-z0-9_]{1,15}$", v):
        raise CustomException(
            code=RET.ERROR.code,
            msg="编码需字母开头，允许字母/数字/下划线，长度2-16",
        )
    return v


def menu_request_validator(data: Any) -> Any:
    """菜单请求数据验证器。

    参数:
    - data (Any): 请求数据。

    返回:
    - Any: 验证后的请求数据。

    异常:
    - CustomException: 请求数据无效时抛出。
    """
    menu_types = {1: "目录", 2: "功能", 3: "权限", 4: "外链"}

    if data.type not in menu_types:
        raise CustomException(
            code=RET.ERROR.code,
            msg=f"菜单类型必须为: {','.join(map(str, menu_types.keys()))}",
        )

    if data.type in [1, 2]:
        if not data.route_name:
            raise CustomException(code=RET.ERROR.code, msg="路由名称不能为空")
        if not data.route_path:
            raise CustomException(code=RET.ERROR.code, msg="路由路径不能为空")

    if data.type == 1 and not (data.redirect and str(data.redirect).strip()):
        raise CustomException(code=RET.ERROR.code, msg="目录类型必须填写重定向地址")

    if data.type == 2 and not data.component_path:
        raise CustomException(code=RET.ERROR.code, msg="组件路径不能为空")

    if data.type == 4 and not getattr(data, "link", None):
        raise CustomException(code=RET.ERROR.code, msg="外链类型必须填写链接地址")

    c = getattr(data, "client", None) or "pc"
    if c not in ("pc", "app"):
        raise CustomException(code=RET.ERROR.code, msg="终端 client 仅允许 pc 或 app")

    return data


def role_permission_request_validator(data: Any) -> Any:
    """角色权限设置数据验证器。

    参数:
    - data (Any): 请求数据。

    返回:
    - Any: 验证后的请求数据。

    异常:
    - CustomException: 请求数据无效时抛出。
    """
    data_scopes = {
        1: "仅本人数据权限",
        2: "本部门数据权限",
        3: "本部门及以下数据权限",
        4: "全部数据权限",
        5: "自定义数据权限",
    }

    if data.data_scope not in data_scopes:
        raise CustomException(
            code=RET.ERROR.code,
            msg=f"数据权限范围必须为: {','.join(map(str, data_scopes.keys()))}",
        )

    if not data.role_ids:
        raise CustomException(code=RET.ERROR.code, msg="角色不能为空")

    return data
