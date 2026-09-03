"""传输任务 WebSocket 连接管理（进程内连接表，按用户推送任务进度）"""

from app.core.ws_manager import WSConnectionManager

transfer_ws_manager = WSConnectionManager(channel="transfer")
