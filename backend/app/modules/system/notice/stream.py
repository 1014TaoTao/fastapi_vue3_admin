"""公告通知 SSE 连接管理（向全部在线用户广播公告变更事件）"""

from app.core.sse_manager import SSEConnectionManager

notice_stream_manager = SSEConnectionManager(channel="notice")
