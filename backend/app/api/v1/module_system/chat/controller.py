from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.module_system.chat.schema import (
    ChatConversationSchema,
    ChatGroupCreateSchema,
    ChatGroupDetailSchema,
    ChatGroupMemberSchema,
    ChatGroupUpdateSchema,
    ChatMessageCreateSchema,
    ChatMessageOutSchema,
    ChatMessagePageSchema,
    ChatReadSchema,
    ChatUserItemSchema,
)
from app.api.v1.module_system.chat.service import ChatService
from app.api.v1.module_system.chat.ws_manager import chat_ws_manager
from app.common.response import ResponseSchema, SuccessResponse
from app.core.base_schema import AuthSchema
from app.core.dependencies import db_getter, get_current_user, websocket_authenticate
from app.core.logger import logger
from app.core.router_class import OperationLogRoute

ChatRouter = APIRouter(route_class=OperationLogRoute, prefix="/chat", tags=["系统聊天"])


@ChatRouter.get("/conversations", summary="会话列表", response_model=ResponseSchema[list[ChatConversationSchema]])
async def get_conversations_controller(
    auth: Annotated[AuthSchema, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await ChatService(auth, db).conversations()
    return SuccessResponse(data=result, msg="获取会话列表成功")


@ChatRouter.get("/messages", summary="历史消息", response_model=ResponseSchema[ChatMessagePageSchema])
async def get_messages_controller(
    auth: Annotated[AuthSchema, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(db_getter)],
    conversation_type: Annotated[int, Query(ge=1, le=2, description="会话类型(1:私聊 2:群聊)")] = 1,
    receiver_id: Annotated[int, Query(gt=0, description="接收人ID(私聊:对方用户,群聊:群ID)")] = 0,
    before_id: Annotated[int | None, Query(gt=0, description="分页游标(取该ID之前的历史消息)")] = None,
    page_size: Annotated[int, Query(ge=1, le=50, description="每页数量")] = 20,
) -> JSONResponse:
    result = await ChatService(auth, db).messages(
        conversation_type=conversation_type,
        receiver_id=receiver_id,
        before_id=before_id,
        page_size=page_size,
    )
    return SuccessResponse(data=result, msg="获取历史消息成功")


@ChatRouter.post("/messages", summary="发送消息", response_model=ResponseSchema[ChatMessageOutSchema])
async def send_message_controller(
    auth: Annotated[AuthSchema, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(db_getter)],
    data: Annotated[ChatMessageCreateSchema, Body(description="消息参数")],
) -> JSONResponse:
    result = await ChatService(auth, db).send_message(data=data)
    return SuccessResponse(data=result, msg="发送消息成功")


@ChatRouter.post("/read", summary="标记已读", response_model=ResponseSchema[None])
async def mark_read_controller(
    auth: Annotated[AuthSchema, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(db_getter)],
    data: Annotated[ChatReadSchema, Body(description="已读参数")],
) -> JSONResponse:
    await ChatService(auth, db).mark_read(data=data)
    return SuccessResponse(msg="标记已读成功")


@ChatRouter.get("/users", summary="用户选择器", response_model=ResponseSchema[list[ChatUserItemSchema]])
async def get_chat_users_controller(
    auth: Annotated[AuthSchema, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(db_getter)],
    keyword: Annotated[str | None, Query(description="关键字")] = None,
) -> JSONResponse:
    result = await ChatService(auth, db).users(keyword=keyword)
    return SuccessResponse(data=result, msg="获取用户列表成功")


@ChatRouter.post("/groups", summary="创建群组", response_model=ResponseSchema[ChatGroupDetailSchema])
async def create_group_controller(
    auth: Annotated[AuthSchema, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(db_getter)],
    data: Annotated[ChatGroupCreateSchema, Body(description="群组参数")],
) -> JSONResponse:
    result = await ChatService(auth, db).create_group(data=data)
    return SuccessResponse(data=result, msg="创建群组成功")


@ChatRouter.get("/groups/{group_id}", summary="群组详情", response_model=ResponseSchema[ChatGroupDetailSchema])
async def get_group_detail_controller(
    auth: Annotated[AuthSchema, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(db_getter)],
    group_id: Annotated[int, Path(gt=0, description="群ID")],
) -> JSONResponse:
    result = await ChatService(auth, db).group_detail(group_id=group_id)
    return SuccessResponse(data=result, msg="获取群组详情成功")


@ChatRouter.put("/groups/{group_id}", summary="修改群组", response_model=ResponseSchema[None])
async def update_group_controller(
    auth: Annotated[AuthSchema, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(db_getter)],
    group_id: Annotated[int, Path(gt=0, description="群ID")],
    data: Annotated[ChatGroupUpdateSchema, Body(description="群组参数")],
) -> JSONResponse:
    await ChatService(auth, db).update_group(group_id=group_id, data=data)
    return SuccessResponse(msg="修改群组成功")


@ChatRouter.delete("/groups/{group_id}", summary="解散群组", response_model=ResponseSchema[None])
async def delete_group_controller(
    auth: Annotated[AuthSchema, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(db_getter)],
    group_id: Annotated[int, Path(gt=0, description="群ID")],
) -> JSONResponse:
    await ChatService(auth, db).delete_group(group_id=group_id)
    return SuccessResponse(msg="解散群组成功")


@ChatRouter.post("/groups/{group_id}/members", summary="添加成员", response_model=ResponseSchema[None])
async def add_group_members_controller(
    auth: Annotated[AuthSchema, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(db_getter)],
    group_id: Annotated[int, Path(gt=0, description="群ID")],
    data: Annotated[ChatGroupMemberSchema, Body(description="成员参数")],
) -> JSONResponse:
    await ChatService(auth, db).add_members(group_id=group_id, member_ids=data.member_ids)
    return SuccessResponse(msg="添加成员成功")


@ChatRouter.delete("/groups/{group_id}/members", summary="移除成员", response_model=ResponseSchema[None])
async def remove_group_members_controller(
    auth: Annotated[AuthSchema, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(db_getter)],
    group_id: Annotated[int, Path(gt=0, description="群ID")],
    member_ids: Annotated[list[int], Body(description="成员ID列表")],
) -> JSONResponse:
    await ChatService(auth, db).remove_members(group_id=group_id, member_ids=member_ids)
    return SuccessResponse(msg="移除成员成功")


@ChatRouter.post("/groups/{group_id}/quit", summary="退出群组", response_model=ResponseSchema[None])
async def quit_group_controller(
    auth: Annotated[AuthSchema, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(db_getter)],
    group_id: Annotated[int, Path(gt=0, description="群ID")],
) -> JSONResponse:
    await ChatService(auth, db).quit_group(group_id=group_id)
    return SuccessResponse(msg="退出群组成功")


@ChatRouter.websocket("/ws")
async def chat_ws_endpoint(ws: WebSocket) -> None:
    """聊天实时通道：令牌通过 Sec-WebSocket-Protocol 携带（小程序可用 ?token=），发送走 REST、接收走推送。"""
    try:
        auth, subprotocol = await websocket_authenticate(ws)
    except Exception as e:
        logger.warning("聊天 WebSocket 认证失败: {}", e)
        await ws.close(code=4001, reason="无效令牌")
        return
    user_id = auth.user.id

    await chat_ws_manager.connect(user_id, ws, subprotocol=subprotocol)
    await _broadcast_presence(user_id, True)
    logger.info("聊天 WebSocket 已连接: user={}", user_id)
    try:
        while True:
            text = await ws.receive_text()
            if text == "ping":
                await ws.send_text("pong")
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.warning("聊天 WebSocket 异常断开: user={}, err={}", user_id, e)
    finally:
        chat_ws_manager.disconnect(user_id, ws)
        await _broadcast_presence(user_id, False)
        logger.info("聊天 WebSocket 已断开: user={}", user_id)


async def _broadcast_presence(user_id: int, online: bool) -> None:
    """向所有在线用户广播某用户的上线/离线状态"""
    await chat_ws_manager.broadcast({"type": "presence", "user_id": user_id, "online": online})
