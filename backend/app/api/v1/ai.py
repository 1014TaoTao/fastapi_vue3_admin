"""ai 路由清单：仅聚合路由，不含业务逻辑。"""

from fastapi import APIRouter

from app.modules.ai.chat.controller import ChatRouter

ai_router = APIRouter(prefix="/ai")

ai_router.include_router(ChatRouter)
