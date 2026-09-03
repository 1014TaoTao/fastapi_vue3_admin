"""聊天 WebSocket 连接管理（进程内连接表，单实例部署）"""

from app.core.ws_manager import WSConnectionManager

chat_ws_manager = WSConnectionManager(channel="chat")
