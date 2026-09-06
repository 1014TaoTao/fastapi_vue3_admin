from enum import Enum, unique


@unique
class EnvironmentEnum(str, Enum):
    """应用运行环境（开发 / 生产）。"""

    DEV = "dev"
    PROD = "prod"


@unique
class BusinessType(Enum):
    """业务操作类型

    OTHER: 其它
    INSERT: 新增
    UPDATE: 修改
    DELETE: 删除
    GRANT: 授权
    EXPORT: 导出
    IMPORT: 导入
    FORCE: 强退
    GENCODE: 生成代码
    CLEAN: 清空数据
    """

    OTHER = 0
    INSERT = 1
    UPDATE = 2
    DELETE = 3
    GRANT = 4
    EXPORT = 5
    IMPORT = 6
    FORCE = 7
    GENCODE = 8
    CLEAN = 9


@unique
class RedisInitKeyConfig(Enum):
    """系统内置Redis键名枚举"""

    ACCESS_TOKEN = {"key": "access_token", "remark": "登录令牌信息"}
    REFRESH_TOKEN = {"key": "refresh_token", "remark": "刷新令牌信息"}
    USER_SESSION = {"key": "user_session", "remark": "用户会话信息"}
    CAPTCHA_CODES = {"key": "captcha_codes", "remark": "图片验证码"}
    SYSTEM_CONFIG = {"key": "system_config", "remark": "系统配置"}
    SYSTEM_DICT = {"key": "system_dict", "remark": "数据字典"}
    APSCHEDULER_LOCK_KEY = {"key": "scheduler_job_lock", "remark": "定时任务初始化锁"}
    AI_MODEL_CONFIG = {"key": "ai_model_config", "remark": "用户AI模型配置"}
    WX_MINI_ACCESS_TOKEN = {"key": "wx_mini_access_token", "remark": "微信小程序 access_token 缓存"}

    @property
    def key(self) -> str:
        """获取 Redis 键名。"""
        return self.value.get("key", "")

    @property
    def remark(self) -> str:
        """获取 Redis 键说明。"""
        return self.value.get("remark", "")


class SysParamKey(str, Enum):
    """系统参数 config_key 常量定义

    所有 sys_param 表的 config_key 值统一在此定义，避免前端/后端各处写死字符串导致拼写错误。
    """

    SYS_NAME = "sys_name"
    LOGO_URL = "logo_url"
    FAVICON = "favicon"
    LOGIN_BG = "login_bg"
    VERSION = "version"
    HELP_DOC = "help_doc"
    GIT_CODE = "git_code"
    COPYRIGHT = "copyright"
    KEEP_RECORD = "keep_record"
    PRIVACY = "privacy"
    CLAUSE = "clause"
    DEMO_ENABLE = "demo_enable"
    IP_WHITE_LIST = "ip_white_list"
    IP_BLACK_LIST = "ip_black_list"
    LOGIN_TITLE = "login_title"
    LOGIN_SUBTITLE = "login_subtitle"
    IP_LOCATION_ENABLE = "ip_location_enable"


@unique
class QueueEnum(str, Enum):
    """队列枚举"""

    none = "None"
    not_none = "not None"
    date = "date"
    month = "month"
    like = "like"
    eq = "eq"
    in_ = "in"
    between = "between"
    ne = "!="
    gt = ">"
    ge = ">="
    lt = "<"
    le = "<="


@unique
class OrderTypeEnum(str, Enum):
    """订单类型"""

    NEW = "new"
    RENEW = "renew"
    UPGRADE = "upgrade"
    DOWNGRADE = "downgrade"


@unique
class InvoiceTypeEnum(str, Enum):
    """发票类型"""

    VAT_NORMAL = "vat_normal"
    VAT_SPECIAL = "vat_special"


@unique
class TicketTypeEnum(str, Enum):
    """工单类型"""

    SUGGESTION = "suggestion"
    BUG = "bug"
    OPTIMIZE = "optimize"
    OTHER = "other"


# ==================== 系统返回码 ====================


class RET(Enum):
    """系统返回码枚举

    0~200: 成功状态码
    400~600: HTTP标准错误码
    4000+: 自定义业务错误码
    """

    # 成功状态码
    OK = (0, "成功")
    SUCCESS = (200, "操作成功")
    CREATED = (201, "创建成功")
    ACCEPTED = (202, "请求已接受")
    NO_CONTENT = (204, "操作成功,无返回数据")

    # HTTP标准错误码
    ERROR = (1, "请求错误")
    BAD_REQUEST = (400, "参数错误")
    UNAUTHORIZED = (401, "未授权")
    FORBIDDEN = (403, "访问受限")
    NOT_FOUND = (404, "资源不存在")
    BAD_METHOD = (405, "不支持的请求方法")
    NOT_ACCEPTABLE = (406, "不接受的请求")
    CONFLICT = (409, "资源冲突")
    GONE = (410, "资源已删除")
    PRECONDITION_FAILED = (412, "前提条件失败")
    UNSUPPORTED_MEDIA_TYPE = (415, "不支持的媒体类型")
    UNPROCESSABLE_ENTITY = (422, "无法处理的实体")
    TOO_MANY_REQUESTS = (429, "请求过于频繁")

    # 服务器错误码
    INTERNAL_SERVER_ERROR = (500, "服务器内部错误")
    NOT_IMPLEMENTED = (501, "功能未实现")
    BAD_GATEWAY = (502, "网关错误")
    SERVICE_UNAVAILABLE = (503, "服务不可用")
    GATEWAY_TIMEOUT = (504, "网关超时")
    HTTP_VERSION_NOT_SUPPORTED = (505, "HTTP版本不支持")

    # 自定义业务错误码
    EXCEPTION = (-1, "系统异常")
    DATAEXIST = (4003, "数据已存在")
    DATAERR = (4004, "数据错误")
    PARAMERR = (4103, "参数错误")
    IOERR = (4302, "IO错误")
    SERVERERR = (4500, "服务错误")
    UNKOWNERR = (4501, "未知错误")
    TIMEOUT = (4502, "请求超时")
    RATE_LIMIT_EXCEEDED = (4503, "访问频率超限")

    # Token相关错误码
    INVALID_TOKEN = (4504, "无效令牌")
    EXPIRED_TOKEN = (4505, "令牌过期")

    # 认证授权错误码
    INVALID_CREDENTIALS = (4506, "无效凭证")

    # 前后端约定的认证类业务码（对应前端 ResultEnum：TOKEN_EXPIRED / UNAUTHORIZED）
    TOKEN_EXPIRED = (10401, "认证过期,请重新登录")
    NO_PERMISSION = (10403, "无权限操作")

    def __init__(self, code: int, msg: str) -> None:
        self._code = code
        self._msg = msg

    @property
    def code(self) -> int:
        return self._code

    @property
    def msg(self) -> str:
        return self._msg
