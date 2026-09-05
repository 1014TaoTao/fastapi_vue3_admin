"""传输任务 SSE 连接管理（按用户推送任务进度）"""

from app.core.sse_manager import SSEConnectionManager

transfer_stream_manager = SSEConnectionManager(channel="transfer")
