from fastapi import APIRouter

from .chat.controller import ChatRouter

ai_router = APIRouter(prefix="/ai")

ai_router.include_router(ChatRouter)
