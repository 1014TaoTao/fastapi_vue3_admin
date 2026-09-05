from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.config.setting import settings
from app.core.base_model import ModelMixin


def get_log_text_column_type():
    """根据数据库类型选择适合存储大文本的列类型。
    """
    db_type = settings.DATABASE_TYPE
    if db_type == "mysql":
        from sqlalchemy.dialects.mysql import LONGTEXT

        return LONGTEXT
    if db_type == "postgres":
        from sqlalchemy.dialects.postgresql import TEXT

        return TEXT
    return Text


class LoginLogModel(ModelMixin):
    """登录日志模型
    """

    __tablename__: str = "sys_login_log"
    __table_args__: dict[str, str] = {"comment": "登录日志表"}
    
    status: Mapped[int] = mapped_column(Integer, default=1, index=True, comment="登录状态(1成功 2失败)")
    description: Mapped[str | None] = mapped_column(Text, default=None, nullable=True, comment="备注")
    username: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="用户名")
    login_location: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="登录位置")
    login_ip: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="登录IP地址")
    request_os: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="操作系统")
    request_browser: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="浏览器")
    msg: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="提示消息")


class OperationLogModel(ModelMixin):
    """操作日志模型"""

    __tablename__: str = "sys_operation_log"
    __table_args__: dict[str, str] = {"comment": "操作日志表"}

    username: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="操作人用户名")
    status: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="操作状态(0:成功 1:失败)")
    description: Mapped[str | None] = mapped_column(Text, default=None, nullable=True, comment="备注")
    request_path: Mapped[str] = mapped_column(String(255), index=True, comment="请求路径")
    request_method: Mapped[str] = mapped_column(String(10), comment="请求方式")
    request_payload: Mapped[str | None] = mapped_column(get_log_text_column_type(), comment="请求体")
    response_code: Mapped[int] = mapped_column(Integer, comment="响应状态码")
    response_json: Mapped[str | None] = mapped_column(get_log_text_column_type(), nullable=True, comment="响应体")
    process_time: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="处理时间")
    request_ip: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True, comment="请求IP")
