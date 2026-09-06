from fastapi import APIRouter, Security
from fastapi.responses import JSONResponse

from app.common.response import ResponseSchema, SuccessResponse
from app.core.dependencies import AuthPermission
from app.core.router_class import OperationLogRoute
from app.modules.monitor.server.schema import ServerMonitorSchema

from .service import ServerService

ServerRouter = APIRouter(route_class=OperationLogRoute, prefix="/server", tags=["服务器监控"])


@ServerRouter.get("/info", summary="查询服务器监控信息", response_model=ResponseSchema[ServerMonitorSchema], dependencies=[Security(AuthPermission(["module_monitor:server:query"]))])
async def get_monitor_server_info_controller() -> JSONResponse:
    result_dict: ServerMonitorSchema = await ServerService.get_server_monitor_info()
    return SuccessResponse(data=result_dict, msg="获取服务器监控信息成功")
