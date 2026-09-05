import asyncio
import json
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Path, Query, Security, WebSocket, WebSocketDisconnect, status
from fastapi.responses import JSONResponse
from redis.asyncio import Redis

from app.common.response import ResponseSchema, SuccessResponse
from app.core.base_schema import AuthSchema, PageResultSchema, PaginationQueryParam
from app.core.dependencies import AuthPermission, redis_getter, websocket_authenticate
from app.core.exceptions import CustomException
from app.core.logger import logger
from app.core.router_class import OperationLogRoute

from .schema import (
    AiChatRequestSchema,
    AiChatResponseSchema,
    AiModelConfigListResponse,
    AiModelConfigSchema,
    ChatQuerySchema,
    ChatSessionCreateSchema,
    ChatSessionOutSchema,
    ChatSessionQueryParam,
    ChatSessionUpdateSchema,
)
from .service import AiModelConfigService, ChatService, get_user_model_config

ChatRouter = APIRouter(route_class=OperationLogRoute, prefix="/chat", tags=["AI管理"])

# WebSocket 聊天所需权限（与 HTTP 对话端点保持一致）
_WS_CHAT_PERMISSION = "module_ai:chat:query"


def _has_chat_permission(auth: AuthSchema) -> bool:
    """校验当前用户是否具备 AI 聊天权限（超管/通配权限直接放行）"""
    user = auth.user
    if user.id is None or user.is_superuser:
        return True
    permissions = set(auth.permissions or [])
    return "*:*:*" in permissions or _WS_CHAT_PERMISSION in permissions


@ChatRouter.get("/detail/{session_id}", summary="获取会话详情", response_model=ResponseSchema[ChatSessionOutSchema])
async def get_session_detail_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_ai:chat:detail"]))],
    session_id: Annotated[str, Path(description="会话ID")],
) -> JSONResponse:
    service = ChatService(auth)
    result = await service.get_session(session_id=session_id)
    return SuccessResponse(data=result, msg="获取会话详情成功")


@ChatRouter.get("/list", summary="查询会话列表", response_model=ResponseSchema[PageResultSchema[ChatSessionOutSchema]])
async def get_session_list_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_ai:chat:query"]))],
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[ChatSessionQueryParam, Query()],
) -> JSONResponse:
    service = ChatService(auth)
    result_dict = await service.page(
        page_no=page.page_no,
        page_size=page.page_size,
        search=search,
        order_by=page.order_by,
    )
    return SuccessResponse(data=result_dict, msg="查询会话列表成功")


@ChatRouter.post("/create", status_code=status.HTTP_201_CREATED, summary="创建会话", response_model=ResponseSchema[ChatSessionOutSchema])
async def create_session_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_ai:chat:create"]))],
    data: Annotated[ChatSessionCreateSchema, Body(description="会话创建参数")],
) -> JSONResponse:
    service = ChatService(auth)
    result = await service.create(data=data)
    return SuccessResponse(data=result, msg="创建会话成功")


@ChatRouter.put("/update/{session_id}", summary="更新会话", response_model=ResponseSchema[None])
async def update_session_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_ai:chat:update"]))],
    session_id: Annotated[str, Path(description="会话ID")],
    data: Annotated[ChatSessionUpdateSchema, Body(description="会话更新参数")],
) -> JSONResponse:
    service = ChatService(auth)
    await service.update(session_id=session_id, data=data)
    return SuccessResponse(data=None, msg="更新会话成功")


@ChatRouter.delete("/delete", summary="删除会话", response_model=ResponseSchema[None])
async def delete_session_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_ai:chat:delete"]))],
    session_ids: Annotated[list[str], Body(description="会话ID列表")],
) -> JSONResponse:
    service = ChatService(auth)
    await service.delete(session_ids=session_ids)
    return SuccessResponse(data=None, msg="删除会话成功")


@ChatRouter.post("/ai-chat", summary="AI 对话（非流式）", response_model=ResponseSchema[AiChatResponseSchema])
async def ai_chat_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_ai:chat:query"]))],
    redis: Annotated[Redis, Depends(redis_getter)],
    data: Annotated[AiChatRequestSchema, Body(description="对话请求")],
) -> JSONResponse:
    service = ChatService(auth)
    # 与 WebSocket 流式一致：优先使用用户激活的模型配置
    model_config = await get_user_model_config(redis, auth.user.id)
    result = await service.chat_non_stream(
        message=data.message,
        session_id=data.session_id,
        model_config=model_config,
    )
    return SuccessResponse(
        data=AiChatResponseSchema(
            response=result["response"],
            session_id=result["session_id"],
            function_calls=result.get("function_calls"),
            action=result.get("action"),
        ),
        msg="对话成功",
    )


@ChatRouter.get("/model", summary="获取 AI 模型配置列表", response_model=ResponseSchema[AiModelConfigListResponse])
async def list_model_config_controller(
    redis: Annotated[Redis, Depends(redis_getter)],
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_ai:chat:query"]))],
) -> JSONResponse:
    service = AiModelConfigService(auth, redis)
    result = await service.list_configs()
    return SuccessResponse(data=result, msg="获取模型配置列表成功")


@ChatRouter.post("/model", status_code=status.HTTP_201_CREATED, summary="新增一个 AI 模型配置", response_model=ResponseSchema[dict[str, Any]])
async def create_model_config_controller(
    redis: Annotated[Redis, Depends(redis_getter)],
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_ai:chat:update"]))],
    data: Annotated[AiModelConfigSchema, Body(description="模型配置参数")],
) -> JSONResponse:
    service = AiModelConfigService(auth, redis)
    result = await service.create(data)
    return SuccessResponse(data=result, msg="模型配置已新增")


@ChatRouter.put("/model/{config_id}", summary="更新指定 ID 的 AI 模型配置", response_model=ResponseSchema[dict[str, Any]])
async def update_model_config_controller(
    redis: Annotated[Redis, Depends(redis_getter)],
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_ai:chat:update"]))],
    config_id: Annotated[str, Path(description="配置项 ID")],
    data: Annotated[AiModelConfigSchema, Body(description="模型配置参数")],
) -> JSONResponse:
    service = AiModelConfigService(auth, redis)
    result = await service.update(config_id, data)
    return SuccessResponse(data=result, msg="模型配置已更新")


@ChatRouter.delete("/model/{config_id}", summary="删除指定 ID 的 AI 模型配置", response_model=ResponseSchema[None])
async def delete_model_config_controller(
    redis: Annotated[Redis, Depends(redis_getter)],
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_ai:chat:update"]))],
    config_id: Annotated[str, Path(description="配置项 ID")],
) -> JSONResponse:
    service = AiModelConfigService(auth, redis)
    await service.delete(config_id)
    return SuccessResponse(data=None, msg="模型配置已删除")


@ChatRouter.post("/model/{config_id}/activate", summary="切换激活的 AI 模型配置", response_model=ResponseSchema[None])
async def activate_model_config_controller(
    redis: Annotated[Redis, Depends(redis_getter)],
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_ai:chat:update"]))],
    config_id: Annotated[str, Path(description="配置项 ID；传 __default__ 使用系统默认")],
) -> JSONResponse:
    service = AiModelConfigService(auth, redis)
    await service.set_active(config_id)
    return SuccessResponse(data=None, msg="已切换模型")


async def _send_error_and_close(websocket: WebSocket, message: str) -> None:
    """发送错误消息并关闭连接"""
    try:
        await websocket.send_text(f"错误: {message}")
    except RuntimeError:
        pass
    finally:
        try:
            await websocket.close()
        except RuntimeError:
            pass


@ChatRouter.websocket("/ws", name="WebSocket聊天")
async def websocket_chat_controller(websocket: WebSocket) -> None:
    """WebSocket 聊天接口。

    支持的消息格式（JSON）：
    - 对话：{"message": "...", "session_id": "...", "files": [...]}
    - 停止：{"action": "stop", "session_id": "..."}

    ws://127.0.0.1:8001/api/v1/ai/chat/ws

    令牌优先通过 Sec-WebSocket-Protocol 携带（不会进入网关/服务的 access log）：
      new WebSocket(url, ["access_token", "access_token." + jwt])
    小程序等无法自定义子协议的客户端，可用 ?token= 兜底。
    """
    # 握手阶段完成认证；未 accept 前无法发送业务报文，失败直接关闭
    try:
        auth, subprotocol = await websocket_authenticate(websocket)
    except Exception as e:
        logger.warning("WebSocket认证失败: {}", e)
        await websocket.close(code=4001, reason="无效令牌")
        return

    # 权限校验：与 HTTP 对话端点一致，未授权用户拒绝握手
    if not _has_chat_permission(auth):
        logger.warning("WebSocket权限不足: 用户={}", auth.user.username)
        await websocket.close(code=4003, reason="无权限")
        return

    await websocket.accept(subprotocol=subprotocol)

    # 跨消息循环共享的停止信号：客户端发送 stop 时 set，生成器检测到后退出
    stop_event = asyncio.Event()
    # 标记当前是否在生成中，便于 stop 校验
    is_generating = asyncio.Event()

    try:
        redis = websocket.app.state.redis
        logger.info("WebSocket连接已建立: {} - 用户: {}", websocket.client, auth.user.username or "未认证")

        chat_service = ChatService(auth)

        # 消息循环
        while True:
            try:
                data = await websocket.receive_text()
                try:
                    message_data = json.loads(data)
                    query = ChatQuerySchema(**message_data)
                except json.JSONDecodeError:
                    logger.warning("收到非JSON消息: {}", data)
                    await websocket.send_text("消息格式错误，请发送JSON格式的消息")
                    continue
                except Exception as e:
                    logger.warning("消息校验失败: {}", e)
                    await websocket.send_text(f"消息格式错误: {e}")
                    continue

                # 处理停止指令
                if query.action == "stop":
                    if is_generating.is_set():
                        stop_event.set()
                        logger.info("收到停止指令: session={}", query.session_id)
                        await websocket.send_text("[STOPPED]")
                    else:
                        await websocket.send_text("当前没有正在进行的生成任务")
                    continue

                # 对话指令
                logger.info("收到聊天查询: session_id={}", query.session_id)

                is_generating.set()
                stop_event.clear()
                # 读取用户的 AI 模型配置（每次可动态切换）
                model_config = await get_user_model_config(redis, auth.user.id)

                stream = chat_service.chat_query(
                    query=query,
                    stop_event=stop_event,
                    model_config=model_config,
                )
                try:
                    async for chunk in stream:
                        if not chunk:
                            continue
                        try:
                            await websocket.send_text(chunk)
                        except RuntimeError:
                            # 客户端已断开：通知生成器停止并关闭底层 LLM 流，避免继续消耗配额
                            logger.warning("WebSocket连接已关闭，停止发送消息")
                            return
                finally:
                    is_generating.clear()
                    stop_event.set()
                    await stream.aclose()

                # 告知前端生成结束
                try:
                    await websocket.send_text("[DONE]")
                except RuntimeError:
                    return

            except WebSocketDisconnect:
                logger.info("WebSocket连接已断开: {}", websocket.client)
                return

    except CustomException as e:
        # 业务异常（认证已前置，多为会话/模型配置异常）
        logger.warning("WebSocket业务异常: {}", e.msg)
        await _send_error_and_close(websocket, e.msg)
    except Exception as e:
        # 未知异常
        logger.exception("WebSocket未知异常: {}", e)
        await _send_error_and_close(websocket, "服务器内部错误")
