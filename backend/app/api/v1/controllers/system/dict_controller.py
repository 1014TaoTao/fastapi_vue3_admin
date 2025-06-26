# -*- coding: utf-8 -*-

import json
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse, StreamingResponse
from aioredis import Redis

from app.common.response import StreamResponse, SuccessResponse
from app.core.base_params import PaginationQueryParams
from app.core.dependencies import AuthPermission, redis_getter
from app.core.router_class import OperationLogRoute
from app.core.logger import logger
from app.common.request import PaginationService
from app.utils.common_util import bytes2file_response
from app.api.v1.schemas.system.auth_schema import AuthSchema
from app.api.v1.params.system.dict_param import DictTypeQueryParams, DictDataQueryParams
from app.api.v1.services.system.dict_service import DictTypeService, DictDataService
from app.api.v1.schemas.system.dict_schema import (
    DictTypeCreateSchema,
    DictTypeUpdateSchema,
    DictDataCreateSchema,
    DictDataUpdateSchema
)


router = APIRouter(route_class=OperationLogRoute)

@router.get("/type/detail", summary="获取字典类型详情", description="获取字典类型详情")
async def get_type_detail_controller(
    id: str = Query(..., description="字典类型ID"),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:dict_type:query"]))
) -> JSONResponse:
    result_dict = await DictTypeService.get_obj_detail_service(id=id, auth=auth)
    logger.info(f"获取字典类型详情成功 {id}")
    return SuccessResponse(data=result_dict, msg="获取字典类型详情成功")

@router.get("/type/list", summary="查询字典类型", description="查询字典类型")
async def get_type_list_controller(
    page: PaginationQueryParams = Depends(),
    search: DictTypeQueryParams = Depends(),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:dict_type:query"]))
) -> JSONResponse:
    result_dict_list = await DictTypeService.get_obj_list_service(auth=auth, search=search, order_by=page.order_by)
    result_dict = await PaginationService.get_page_obj(data_list= result_dict_list, page_no= page.page_no, page_size = page.page_size)
    logger.info("查询字典类型列表成功")
    return SuccessResponse(data=result_dict, msg="查询字典类型列表成功")

@router.get("/type/optionselect", summary="获取全部字典类型", description="获取全部字典类型")
async def get_type_list_controller(
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:dict_type:query"]))
) -> JSONResponse:
    result_dict_list = await DictTypeService.get_obj_list_service(auth=auth)
    logger.info("获取字典类型列表成功")
    return SuccessResponse(data=result_dict_list, msg="获取字典类型列表成功")

@router.post("/type/create", summary="创建字典类型", description="创建字典类型")
async def create_type_controller(
    data: DictTypeCreateSchema,
    redis: Redis = Depends(redis_getter),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:dict_type:create"]))
) -> JSONResponse:
    result_dict = await DictTypeService.create_obj_service(auth=auth, redis=redis, data=data)
    logger.info(f"创建字典类型成功: {result_dict}")
    return SuccessResponse(data=result_dict, msg="创建字典类型成功")

@router.put("/type/update", summary="修改字典类型", description="修改字典类型")
async def update_type_controller(
    data: DictTypeUpdateSchema,
    redis: Redis = Depends(redis_getter),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:dict_type:update"]))
) -> JSONResponse:
    result_dict = await DictTypeService.update_obj_service(auth=auth, redis=redis, data=data)
    logger.info(f"修改字典类型成功: {result_dict}")
    return SuccessResponse(data=result_dict, msg="修改字典类型成功")

@router.delete("/type/delete", summary="删除字典类型", description="删除字典类型")
async def delete_type_controller(
    redis: Redis = Depends(redis_getter),
    id: str = Query(..., description="字典类型ID"),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:dict_type:delete"]))
) -> JSONResponse:
    await DictTypeService.delete_obj_service(auth=auth, redis=redis, id=id)
    logger.info(f"删除字典类型成功: {id}")
    return SuccessResponse(msg="删除字典类型成功")

@router.post('/type/export', summary="导出字典类型", description="导出字典类型")
async def export_type_list_controller(
    search: DictTypeQueryParams = Depends(),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:dict_type:export"]))
) -> StreamingResponse:
    # 获取全量数据
    result_dict_list = await DictTypeService.get_obj_list_service(search=search, auth=auth)
    export_result = await DictTypeService.export_obj_service(data_list=result_dict_list)
    logger.info('导出字典类型成功')

    return StreamResponse(
        data=bytes2file_response(export_result),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers = {
            'Content-Disposition': 'attachment; filename=data.xlsx'
        }
    )

@router.get("/data/detail", summary="获取字典数据详情", description="获取字典数据详情")
async def get_data_detail_controller(
    id: str = Query(..., description="字典数据ID"),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:dict_data:query"]))
) -> JSONResponse:
    result_dict = await DictDataService.get_obj_detail_service(id=id, auth=auth)
    logger.info(f"获取字典数据详情成功 {id}")
    return SuccessResponse(data=result_dict, msg="获取字典数据详情成功")

@router.get("/data/list", summary="查询字典数据", description="查询字典数据")
async def get_data_list_controller(
    page: PaginationQueryParams = Depends(),
    search: DictDataQueryParams = Depends(),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:dict_data:query"]))
) -> JSONResponse:
    result_dict_list = await DictDataService.get_obj_list_service(auth=auth, search=search, order_by=page.order_by)
    result_dict = await PaginationService.get_page_obj(data_list= result_dict_list, page_no= page.page_no, page_size = page.page_size)
    logger.info("查询字典数据列表成功")
    return SuccessResponse(data=result_dict, msg="查询字典数据列表成功")

@router.post("/data/create", summary="创建字典数据", description="创建字典数据")
async def create_data_controller(
    data: DictDataCreateSchema,
    redis: Redis = Depends(redis_getter),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:dict_data:create"]))
) -> JSONResponse:
    result_dict = await DictDataService.create_obj_service(auth=auth, redis=redis, data=data)
    logger.info(f"创建字典数据成功: {result_dict}")
    return SuccessResponse(data=result_dict, msg="创建字典数据成功")

@router.put("/data/update", summary="修改字典数据", description="修改字典数据")
async def update_data_controller(
    data: DictDataUpdateSchema,
    redis: Redis = Depends(redis_getter),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:dict_data:update"]))
) -> JSONResponse:
    result_dict = await DictDataService.update_obj_service(auth=auth, redis=redis, data=data)
    logger.info(f"修改字典数据成功: {result_dict}")
    return SuccessResponse(data=result_dict, msg="修改字典数据成功")

@router.delete("/data/delete", summary="删除字典数据", description="删除字典数据")
async def delete_data_controller(
    redis: Redis = Depends(redis_getter),
    id: str = Query(..., description="字典数据ID"),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:dict_data:delete"]))
) -> JSONResponse:
    await DictDataService.delete_obj_service(auth=auth, redis=redis, id=id)
    logger.info(f"删除字典数据成功: {id}")
    return SuccessResponse(msg="删除字典数据成功")

@router.post('/data/export', summary="导出字典数据", description="导出字典数据")
async def export_data_list_controller(
    search: DictDataQueryParams = Depends(),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:dict_data:export"]))
) -> StreamingResponse:
    # 获取全量数据
    result_dict_list = await DictDataService.get_obj_list_service(search=search, auth=auth)
    export_result = await DictDataService.export_obj_service(data_list=result_dict_list)
    logger.info('导出字典数据成功')

    return StreamResponse(
        data=bytes2file_response(export_result),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers = {
            'Content-Disposition': 'attachment; filename=data.xlsx'
        }
    )

@router.get('/data/info/{dict_type}', summary="根据字典类型获取数据", description="根据字典类型获取数据")
async def get_init_dict_data_controller(
    dict_type: str,
    redis: Redis = Depends(redis_getter)
):
    # 获取全量数据
    dict_data_query_result = await DictDataService.get_init_dict_service(
        redis=redis, dict_type=dict_type
    )
    logger.info(f"获取初始化字典数据成功：{dict_data_query_result}")

    return SuccessResponse(data=json.loads(dict_data_query_result), msg="获取初始化字典数据成功")

