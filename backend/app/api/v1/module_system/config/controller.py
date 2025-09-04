# -*- coding: utf-8 -*-

from fastapi import APIRouter, Body, Depends, Path, Query, Request, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from redis.asyncio.client import Redis


from app.common.request import PaginationService
from app.common.response import StreamResponse, SuccessResponse
from app.utils.common_util import bytes2file_response
from app.core.base_params import PaginationQueryParams
from app.core.dependencies import AuthPermission, redis_getter
from app.core.router_class import OperationLogRoute
from app.core.logger import logger
from ..auth.schema import AuthSchema
from .param import ConfigQueryParams
from .schema import ConfigCreateSchema, ConfigUpdateSchema
from .service import ConfigService


ConfigRouter = APIRouter(route_class=OperationLogRoute, prefix="/config", tags=["系统配置"])

@ConfigRouter.get("/detail/{id}", summary="获取系统配置详情", description="获取系统配置详情")
async def get_type_detail_controller(
    id: int = Path(..., description="系统配置ID"),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:config:query"]))
) -> JSONResponse:
    result_dict = await ConfigService.get_obj_detail_service(id=id, auth=auth)
    logger.info(f"获取系统配置详情成功 {id}")
    return SuccessResponse(data=result_dict, msg="获取系统配置详情成功")


@ConfigRouter.get("/list", summary="获取配置", description="获取配置")
async def get_obj_list_controller(
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:config:query"])),
    page: PaginationQueryParams = Depends(),
    search: ConfigQueryParams = Depends(),
) -> JSONResponse:
    result_dict_list = await ConfigService.get_obj_list_service(auth=auth, search=search, order_by=page.order_by)
    result_dict = await PaginationService.get_page_obj(data_list= result_dict_list, page_no= page.page_no, page_size = page.page_size)
    logger.info(f"获取配置成功")
    return SuccessResponse(data=result_dict, msg="查询配置列表成功")


@ConfigRouter.post("/create", summary="创建系统配置", description="创建系统配置")
async def create_obj_controller(
    data: ConfigCreateSchema,
    redis: Redis = Depends(redis_getter),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:config:create"]))
) -> JSONResponse:
    result_dict = await ConfigService.create_obj_service(auth=auth, redis=redis, data=data)
    logger.info(f"创建系统配置成功: {result_dict}")
    return SuccessResponse(data=result_dict, msg="创建系统配置成功")


@ConfigRouter.put("/update/{id}", summary="修改配置", description="修改配置")
async def update_objs_controller(
    data: ConfigUpdateSchema,
    id: int = Path(..., description="系统配置ID"),
    redis: Redis = Depends(redis_getter), 
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:config:update"]))
) -> JSONResponse:
    result_dict = await ConfigService.update_obj_service(auth=auth, redis=redis, id=id, data=data)
    logger.info(f"更新配置成功 {result_dict}")
    return SuccessResponse(data=result_dict, msg="更新配置成功")


@ConfigRouter.delete("/delete", summary="删除系统配置", description="删除系统配置")
async def delete_type_controller(
    redis: Redis = Depends(redis_getter),
    ids: list[int] = Body(..., description="ID列表"),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:config:delete"]))
) -> JSONResponse:
    await ConfigService.delete_obj_service(auth=auth, redis=redis, ids=ids)
    logger.info(f"删除系统配置成功: {ids}")
    return SuccessResponse(msg="删除系统配置成功")


@ConfigRouter.post('/export', summary="导出系统配置", description="导出系统配置")
async def export_type_list_controller(
    search: ConfigQueryParams = Depends(),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:config:export"]))
) -> StreamingResponse:
    # 获取全量数据
    result_dict_list = await ConfigService.get_obj_list_service(search=search, auth=auth)
    export_result = await ConfigService.export_obj_service(data_list=result_dict_list)
    logger.info('导出系统配置成功')

    return StreamResponse(
        data=bytes2file_response(export_result),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers = {
            'Content-Disposition': 'attachment; filename=config.xlsx'
        }
    )


@ConfigRouter.post("/upload", summary="上传文件", dependencies=[Depends(AuthPermission(permissions=["system:config:upload"]))])
async def upload_file_controller(
    file: UploadFile,
    request: Request
) -> JSONResponse:
    result_str = await ConfigService.upload_service(base_url=str(request.base_url), file=file)
    logger.info(f"上传文件: {result_str}")
    return SuccessResponse(data=result_str, msg='上传文件成功')


@ConfigRouter.get("/info", summary="获取初始化缓存系统配置", description="获取初始化缓存系统配置")
async def get_init_config_controller(
    redis: Redis = Depends(redis_getter),
) -> JSONResponse:
    result_dict = await ConfigService.get_init_config_service(redis=redis)
    logger.info(f"获取初始化缓存系统配置成功 {result_dict}")
    return SuccessResponse(data=result_dict, msg="获取初始化缓存系统配置成功")
