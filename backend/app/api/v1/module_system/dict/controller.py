# -*- coding: utf-8 -*-

import json
from fastapi import APIRouter, Body, Depends, Path, Query
from fastapi.responses import JSONResponse, StreamingResponse
from redis.asyncio.client import Redis

from app.common.response import StreamResponse, SuccessResponse
from app.core.base_params import PaginationQueryParam
from app.core.base_schema import BatchSetAvailable
from app.core.dependencies import AuthPermission, redis_getter
from app.core.router_class import OperationLogRoute
from app.core.logger import logger
from app.common.request import PaginationService
from app.utils.common_util import bytes2file_response
from ..auth.schema import AuthSchema
from .param import DictTypeQueryParam, DictDataQueryParam
from .service import DictTypeService, DictDataService
from .schema import (
    DictTypeCreateSchema,
    DictTypeUpdateSchema,
    DictDataCreateSchema,
    DictDataUpdateSchema
)


DictRouter = APIRouter(route_class=OperationLogRoute, prefix="/dict", tags=["字典管理"])

@DictRouter.get("/type/detail/{id}", summary="获取字典类型详情", description="获取字典类型详情")
async def get_type_detail_controller(
    id: int = Path(..., description="字典类型ID"),
    auth: AuthSchema = Depends(AuthPermission(["system:dict_type:query"]))
) -> JSONResponse:
    """
    获取字典类型详情

    参数:
    - id (int): 字典类型ID
    - auth (AuthSchema): 认证信息模型
        
    返回:
    - JSONResponse: 包含字典类型详情的响应模型
        
    异常:
    - CustomException: 获取字典类型详情失败时抛出异常。
    """
    result_dict = await DictTypeService.get_obj_detail_service(id=id, auth=auth)
    logger.info(f"获取字典类型详情成功 {id}")
    return SuccessResponse(data=result_dict, msg="获取字典类型详情成功")

@DictRouter.get("/type/list", summary="查询字典类型", description="查询字典类型")
async def get_type_list_controller(
    page: PaginationQueryParam = Depends(),
    search: DictTypeQueryParam = Depends(),
    auth: AuthSchema = Depends(AuthPermission(["system:dict_type:query"]))
) -> JSONResponse:
    """
    查询字典类型列表

    参数:
    - page (PaginationQueryParam): 分页查询参数模型
    - search (DictTypeQueryParam): 查询参数模型
    - auth (AuthSchema): 认证信息模型
        
    返回:
    - JSONResponse: 包含字典类型列表的响应模型
        
    异常:
    - CustomException: 查询字典类型列表失败时抛出异常。
    """
    result_dict_list = await DictTypeService.get_obj_list_service(auth=auth, search=search, order_by=page.order_by)
    result_dict = await PaginationService.paginate(data_list= result_dict_list, page_no= page.page_no, page_size = page.page_size)
    logger.info(f"查询字典类型列表成功")
    return SuccessResponse(data=result_dict, msg="查询字典类型列表成功")

@DictRouter.get("/type/optionselect", summary="获取全部字典类型", description="获取全部字典类型")
async def get_type_loptionselect_controller(
    auth: AuthSchema = Depends(AuthPermission(["system:dict_type:query"]))
) -> JSONResponse:
    """
    获取全部字典类型

    参数:
    - auth (AuthSchema): 认证信息模型
        
    返回:
    - JSONResponse: 包含全部字典类型的响应模型
        
    异常:
    - CustomException: 获取字典类型列表失败时抛出异常。
    """
    result_dict_list = await DictTypeService.get_obj_list_service(auth=auth)
    logger.info(f"获取字典类型列表成功")
    return SuccessResponse(data=result_dict_list, msg="获取字典类型列表成功")

@DictRouter.post("/type/create", summary="创建字典类型", description="创建字典类型")
async def create_type_controller(
    data: DictTypeCreateSchema,
    redis: Redis = Depends(redis_getter),
    auth: AuthSchema = Depends(AuthPermission(["system:dict_type:create"]))
) -> JSONResponse:
    """
    创建字典类型

    参数:
    - data (DictTypeCreateSchema): 创建字典类型负载模型
    - redis (Redis): Redis数据库连接
    - auth (AuthSchema): 认证信息模型
        
    返回:
    - JSONResponse: 包含创建字典类型结果的响应模型
        
    异常:
    - CustomException: 创建字典类型失败时抛出异常。
    """
    result_dict = await DictTypeService.create_obj_service(auth=auth, redis=redis, data=data)
    logger.info(f"创建字典类型成功: {result_dict}")
    return SuccessResponse(data=result_dict, msg="创建字典类型成功")

@DictRouter.put("/type/update/{id}", summary="修改字典类型", description="修改字典类型")
async def update_type_controller(
    data: DictTypeUpdateSchema,
    redis: Redis = Depends(redis_getter),
    id: int = Path(..., description="字典类型ID"),
    auth: AuthSchema = Depends(AuthPermission(["system:dict_type:update"]))
) -> JSONResponse:
    """
    修改字典类型

    参数:
    - data (DictTypeUpdateSchema): 修改字典类型负载模型
    - redis (Redis): Redis数据库连接
    - id (int): 字典类型ID
    - auth (AuthSchema): 认证信息模型
        
    返回:
    - JSONResponse: 包含修改字典类型结果的响应模型
        
    异常:
    - CustomException: 修改字典类型失败时抛出异常。
    """
    result_dict = await DictTypeService.update_obj_service(auth=auth, redis=redis, id=id, data=data)
    logger.info(f"修改字典类型成功: {result_dict}")
    return SuccessResponse(data=result_dict, msg="修改字典类型成功")

@DictRouter.delete("/type/delete", summary="删除字典类型", description="删除字典类型")
async def delete_type_controller(
    redis: Redis = Depends(redis_getter),
    ids: list[int] = Body(..., description="ID列表"),
    auth: AuthSchema = Depends(AuthPermission(["system:dict_type:delete"]))
) -> JSONResponse:
    """
    删除字典类型

    参数:
    - redis (Redis): Redis数据库连接
    - ids (list[int]): 字典类型ID列表
    - auth (AuthSchema): 认证信息模型
        
    返回:
    - JSONResponse: 包含删除字典类型结果的响应模型
        
    异常:
    - CustomException: 删除字典类型失败时抛出异常。
    """
    await DictTypeService.delete_obj_service(auth=auth, redis=redis, ids=ids)
    logger.info(f"删除字典类型成功: {ids}")
    return SuccessResponse(msg="删除字典类型成功")

@DictRouter.patch("/type/available/setting", summary="批量修改字典类型状态", description="批量修改字典类型状态")
async def batch_set_available_dict_type_controller(
    data: BatchSetAvailable,
    auth: AuthSchema = Depends(AuthPermission(["system:dict_type:patch"]))
) -> JSONResponse:
    """
    批量修改字典类型状态

    参数:
    - data (BatchSetAvailable): 批量修改字典类型状态负载模型
    - auth (AuthSchema): 认证信息模型
        
    返回:
    - JSONResponse: 包含批量修改字典类型状态结果的响应模型
        
    异常:
    - CustomException: 批量修改字典类型状态失败时抛出异常。
    """
    await DictTypeService.set_obj_available_service(auth=auth, data=data)
    logger.info(f"批量修改字典类型状态成功: {data.ids}")
    return SuccessResponse(msg="批量修改字典类型状态成功")

@DictRouter.post('/type/export', summary="导出字典类型", description="导出字典类型")
async def export_type_list_controller(
    search: DictTypeQueryParam = Depends(),
    auth: AuthSchema = Depends(AuthPermission(["system:dict_type:export"]))
) -> StreamingResponse:
    """
    导出字典类型

    参数:
    - search (DictTypeQueryParam): 查询参数模型
    - auth (AuthSchema): 认证信息模型
        
    返回:
    - StreamingResponse: 包含导出字典类型结果的响应模型
        
    异常:
    - CustomException: 导出字典类型失败时抛出异常。
    """
    # 获取全量数据
    result_dict_list = await DictTypeService.get_obj_list_service(search=search, auth=auth)
    export_result = await DictTypeService.export_obj_service(data_list=result_dict_list)
    logger.info('导出字典类型成功')

    return StreamResponse(
        data=bytes2file_response(export_result),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers = {
            'Content-Disposition': 'attachment; filename=dict_type.xlsx'
        }
    )

@DictRouter.get("/data/detail/{id}", summary="获取字典数据详情", description="获取字典数据详情")
async def get_data_detail_controller(
    id: int = Path(..., description="字典数据ID"),
    auth: AuthSchema = Depends(AuthPermission(["system:dict_data:query"]))
) -> JSONResponse:
    """
    获取字典数据详情

    参数:
    - id (int): 字典数据ID
    - auth (AuthSchema): 认证信息模型
        
    返回:
    - JSONResponse: 包含字典数据详情的响应模型
        
    异常:
    - CustomException: 获取字典数据详情失败时抛出异常。
    """
    result_dict = await DictDataService.get_obj_detail_service(id=id, auth=auth)
    logger.info(f"获取字典数据详情成功 {id}")
    return SuccessResponse(data=result_dict, msg="获取字典数据详情成功")

@DictRouter.get("/data/list", summary="查询字典数据", description="查询字典数据")
async def get_data_list_controller(
    page: PaginationQueryParam = Depends(),
    search: DictDataQueryParam = Depends(),
    auth: AuthSchema = Depends(AuthPermission(["system:dict_data:query"]))
) -> JSONResponse:
    """
    查询字典数据

    参数:
    - page (PaginationQueryParam): 分页查询参数模型
    - search (DictDataQueryParam): 查询参数模型
    - auth (AuthSchema): 认证信息模型
        
    返回:
    - JSONResponse: 包含字典数据列表的响应模型
        
    异常:
    - CustomException: 查询字典数据列表失败时抛出异常。
    """
    order_by = [{"order": "asc"}]
    if page.order_by:
        order_by = page.order_by
    result_dict_list = await DictDataService.get_obj_list_service(auth=auth, search=search, order_by=order_by)
    result_dict = await PaginationService.paginate(data_list= result_dict_list, page_no= page.page_no, page_size = page.page_size)
    logger.info(f"查询字典数据列表成功")
    return SuccessResponse(data=result_dict, msg="查询字典数据列表成功")

@DictRouter.post("/data/create", summary="创建字典数据", description="创建字典数据")
async def create_data_controller(
    data: DictDataCreateSchema,
    redis: Redis = Depends(redis_getter),
    auth: AuthSchema = Depends(AuthPermission(["system:dict_data:create"]))
) -> JSONResponse:
    """
    创建字典数据

    参数:
    - data (DictDataCreateSchema): 创建字典数据负载模型
    - redis (Redis): Redis数据库连接
    - auth (AuthSchema): 认证信息模型
        
    返回:
    - JSONResponse: 包含创建字典数据结果的响应模型
        
    异常:
    - CustomException: 创建字典数据失败时抛出异常。
    """
    result_dict = await DictDataService.create_obj_service(auth=auth, redis=redis, data=data)
    logger.info(f"创建字典数据成功: {result_dict}")
    return SuccessResponse(data=result_dict, msg="创建字典数据成功")

@DictRouter.put("/data/update/{id}", summary="修改字典数据", description="修改字典数据")
async def update_data_controller(
    data: DictDataUpdateSchema,
    redis: Redis = Depends(redis_getter),
    id: int = Path(..., description="字典数据ID"),
    auth: AuthSchema = Depends(AuthPermission(["system:dict_data:update"]))
) -> JSONResponse:
    """
    修改字典数据

    参数:
    - data (DictDataUpdateSchema): 修改字典数据负载模型
    - redis (Redis): Redis数据库连接
    - id (int): 字典数据ID
    - auth (AuthSchema): 认证信息模型
        
    返回:
    - JSONResponse: 包含修改字典数据结果的响应模型
        
    异常:
    - CustomException: 修改字典数据失败时抛出异常。
    """
    result_dict = await DictDataService.update_obj_service(auth=auth, redis=redis, id=id, data=data)
    logger.info(f"修改字典数据成功: {result_dict}")
    return SuccessResponse(data=result_dict, msg="修改字典数据成功")

@DictRouter.delete("/data/delete", summary="删除字典数据", description="删除字典数据")
async def delete_data_controller(
    redis: Redis = Depends(redis_getter),
    ids: list[int] = Body(..., description="ID列表"),
    auth: AuthSchema = Depends(AuthPermission(["system:dict_data:delete"]))
) -> JSONResponse:
    """
    删除字典数据

    参数:
    - redis (Redis): Redis数据库连接
    - ids (list[int]): 字典数据ID列表
    - auth (AuthSchema): 认证信息模型
        
    返回:
    - JSONResponse: 包含删除字典数据结果的响应模型
        
    异常:
    - CustomException: 删除字典数据失败时抛出异常。
    """
    await DictDataService.delete_obj_service(auth=auth, redis=redis, ids=ids)
    logger.info(f"删除字典数据成功: {ids}")
    return SuccessResponse(msg="删除字典数据成功")

@DictRouter.patch("/data/available/setting", summary="批量修改字典数据状态", description="批量修改字典数据状态")
async def batch_set_available_dict_data_controller(
    data: BatchSetAvailable,
    auth: AuthSchema = Depends(AuthPermission(["system:dict_data:patch"]))
) -> JSONResponse:
    """
    批量修改字典数据状态

    参数:
    - data (BatchSetAvailable): 批量修改字典数据状态负载模型
    - auth (AuthSchema): 认证信息模型
        
    返回:
    - JSONResponse: 包含批量修改字典数据状态结果的响应模型
        
    异常:
    - CustomException: 批量修改字典数据状态失败时抛出异常。
    """
    await DictDataService.set_obj_available_service(auth=auth, data=data)
    logger.info(f"批量修改字典数据状态成功: {data.ids}")
    return SuccessResponse(msg="批量修改字典数据状态成功")

@DictRouter.post('/data/export', summary="导出字典数据", description="导出字典数据")
async def export_data_list_controller(
    search: DictDataQueryParam = Depends(),
    page: PaginationQueryParam = Depends(),
    auth: AuthSchema = Depends(AuthPermission(["system:dict_data:export"]))
) -> StreamingResponse:
    """
    导出字典数据

    参数:
    - search (DictDataQueryParam): 查询参数模型
    - page (PaginationQueryParam): 分页参数模型
    - auth (AuthSchema): 认证信息模型
        
    返回:
    - StreamingResponse: 包含导出字典数据结果的响应模型
        
    异常:
    - CustomException: 导出字典数据失败时抛出异常。
    """
    result_dict_list = await DictDataService.get_obj_list_service(auth=auth, search=search, order_by=page.order_by)
    export_result = await DictDataService.export_obj_service(data_list=result_dict_list)
    logger.info('导出字典数据成功')

    return StreamResponse(
        data=bytes2file_response(export_result),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers = {
            'Content-Disposition': 'attachment; filename=dice_data.xlsx'
        }
    )

@DictRouter.get('/data/info/{dict_type}', summary="根据字典类型获取数据", description="根据字典类型获取数据")
async def get_init_dict_data_controller(
    dict_type: str,
    redis: Redis = Depends(redis_getter)
) -> JSONResponse:
    """
    根据字典类型获取数据

    参数:
    - dict_type (str): 字典类型
    - redis (Redis): Redis数据库连接
        
    返回:
    - JSONResponse: 包含根据字典类型获取数据结果的响应模型
        
    异常:
    - CustomException: 根据字典类型获取数据失败时抛出异常。
    """
    dict_data_query_result = await DictDataService.get_init_dict_service(
        redis=redis, dict_type=dict_type
    )
    logger.info(f"获取初始化字典数据成功：{dict_data_query_result}")

    # 确保数据是字符串类型再进行 JSON 解析
    if isinstance(dict_data_query_result, bytes):
        dict_data_query_result = dict_data_query_result.decode('utf-8')
    elif not isinstance(dict_data_query_result, str):
        dict_data_query_result = str(dict_data_query_result)
        
    return SuccessResponse(data=json.loads(dict_data_query_result), msg="获取初始化字典数据成功")
