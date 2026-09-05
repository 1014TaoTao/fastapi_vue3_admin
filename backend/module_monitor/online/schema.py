from datetime import datetime

from pydantic import BaseModel, Field

from app.core.base_schema import SessionInfoSchema


class OnlineOutSchema(SessionInfoSchema):
    """在线用户响应模型 — ``SessionInfoSchema`` 的公开子集。"""


class OnlineQueryParam(BaseModel):
    """在线用户查询参数"""

    name: str | None = Field(None, description="登录名称")
    ipaddr: str | None = Field(None, description="登陆IP地址")
    login_location: str | None = Field(None, description="登录所属地")


class RecentLoginItem(BaseModel):
    """最近登录记录"""
    username: str
    status: int
    login_time: datetime
    login_ip: str | None = None
    login_location: str | None = None


class LoginTrendItem(BaseModel):
    """登录趋势（按天聚合）"""
    day: str  # 日期 YYYY-MM-DD
    logins: int = 0  # 登录次数
    unique_users: int = 0  # 独立用户数
    new_users: int = 0  # 当日新增用户数


class DashboardStatsSchema(BaseModel):
    """仪表盘统计数据"""
    online_users: int = 0
    total_users: int = 0
    today_login_count: int = 0
    today_unique_users: int = 0
    week_user_created: int = 0
    login_trend: list[LoginTrendItem] = []
    recent_logins: list[RecentLoginItem] = []
