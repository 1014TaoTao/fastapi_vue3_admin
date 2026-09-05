from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Path, Query, Security, status
from fastapi.responses import JSONResponse
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseSchema, SuccessResponse
from app.core.base_schema import AuthSchema, BatchSetAvailable, PageResultSchema, PaginationQueryParam
from app.core.dependencies import AuthPermission, db_getter, redis_getter
from app.core.router_class import OperationLogRoute

from .schema import (
    DictDataCreateSchema,
    DictDataOutSchema,
    DictDataQueryParam,
    DictDataUpdateSchema,
    DictTypeCreateSchema,
    DictTypeOutSchema,
    DictTypeQueryParam,
    DictTypeUpdateSchema,
)
from .service import DictDataService, DictTypeService

DictRouter = APIRouter(route_class=OperationLogRoute, prefix="/dict", tags=["字典管理"])


@DictRouter.get("/type/detail/{id}", summary="获取字典类型详情", response_model=ResponseSchema[DictTypeOutSchema])
async def get_type_detail_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:dict_type:detail"]))],
    id: Annotated[int, Path(description="字典类型ID", ge=1)],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result_dict: DictTypeOutSchema = await DictTypeService(auth, db).detail(id=id)
    return SuccessResponse(data=result_dict, msg="获取字典类型详情成功")


@DictRouter.get("/type/list", summary="查询字典类型", response_model=ResponseSchema[PageResultSchema[DictTypeOutSchema]])
async def get_type_list_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:dict_type:query"]))],
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[DictTypeQueryParam, Query()],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result_dict: PageResultSchema[DictTypeOutSchema] = await DictTypeService(auth, db).page(
        page_no=page.page_no,
        page_size=page.page_size,
        search=search,
        order_by=page.order_by,
    )
    return SuccessResponse(data=result_dict, msg="查询字典类型列表成功")


@DictRouter.get("/type/optionselect", summary="获取全部字典类型", response_model=ResponseSchema[list[DictTypeOutSchema]])
async def get_type_optionselect_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:dict_type:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result_dict_list: list[DictTypeOutSchema] = await DictTypeService(auth, db).get_list()
    return SuccessResponse(data=result_dict_list, msg="获取字典类型列表成功")


@DictRouter.post("/type/create", status_code=status.HTTP_201_CREATED, summary="创建字典类型", response_model=ResponseSchema[DictTypeOutSchema])
async def create_type_controller(
    redis: Annotated[Redis, Depends(redis_getter)],
    db: Annotated[AsyncSession, Depends(db_getter)],
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:dict_type:create"]))],
    data: Annotated[DictTypeCreateSchema, Body(description="字典类型创建参数")],
) -> JSONResponse:
    result_dict: DictTypeOutSchema = await DictTypeService(auth, db).create(redis=redis, data=data)
    return SuccessResponse(data=result_dict, msg="创建字典类型成功")


@DictRouter.put("/type/update/{id}", summary="修改字典类型", response_model=ResponseSchema[DictTypeOutSchema])
async def update_type_controller(
    redis: Annotated[Redis, Depends(redis_getter)],
    db: Annotated[AsyncSession, Depends(db_getter)],
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:dict_type:update"]))],
    id: Annotated[int, Path(description="字典类型ID", ge=1)],
    data: Annotated[DictTypeUpdateSchema, Body(description="字典类型修改参数")],
) -> JSONResponse:
    result_dict: DictTypeOutSchema = await DictTypeService(auth, db).update(redis=redis, id=id, data=data)
    return SuccessResponse(data=result_dict, msg="修改字典类型成功")


@DictRouter.delete("/type/delete", summary="删除字典类型", response_model=ResponseSchema[None])
async def delete_type_controller(
    redis: Annotated[Redis, Depends(redis_getter)],
    db: Annotated[AsyncSession, Depends(db_getter)],
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:dict_type:delete"]))],
    ids: Annotated[list[int], Body(description="字典类型ID列表")],
) -> JSONResponse:
    await DictTypeService(auth, db).delete(redis=redis, ids=ids)
    return SuccessResponse(msg="删除字典类型成功")


@DictRouter.patch("/type/status/batch", summary="批量修改字典类型状态", response_model=ResponseSchema[None])
async def batch_set_available_dict_type_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:dict_type:patch"]))],
    data: Annotated[BatchSetAvailable, Body(description="状态设置")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    await DictTypeService(auth, db).set_available(data=data)
    return SuccessResponse(msg="批量修改字典类型状态成功")


@DictRouter.get("/data/detail/{id}", summary="获取字典数据详情", response_model=ResponseSchema[DictDataOutSchema])
async def get_data_detail_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:dict_data:detail"]))],
    id: Annotated[int, Path(description="字典数据ID", ge=1)],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result_dict: DictDataOutSchema = await DictDataService(auth, db).detail(id=id)
    return SuccessResponse(data=result_dict, msg="获取字典数据详情成功")


@DictRouter.get("/data/list", summary="查询字典数据", response_model=ResponseSchema[PageResultSchema[DictDataOutSchema]])
async def get_data_list_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:dict_data:query"]))],
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[DictDataQueryParam, Query()],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    order_by: list[dict[str, str]] = [{"order": "asc"}]
    if page.order_by:
        order_by = page.order_by
    result_dict: PageResultSchema[DictDataOutSchema] = await DictDataService(auth, db).page(
        page_no=page.page_no,
        page_size=page.page_size,
        search=search,
        order_by=order_by,
    )
    return SuccessResponse(data=result_dict, msg="查询字典数据列表成功")


@DictRouter.post("/data/create", status_code=status.HTTP_201_CREATED, summary="创建字典数据", response_model=ResponseSchema[DictDataOutSchema])
async def create_data_controller(
    redis: Annotated[Redis, Depends(redis_getter)],
    db: Annotated[AsyncSession, Depends(db_getter)],
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:dict_data:create"]))],
    data: Annotated[DictDataCreateSchema, Body(description="字典数据创建参数")],
) -> JSONResponse:
    result_dict: DictDataOutSchema = await DictDataService(auth, db).create(redis=redis, data=data)
    return SuccessResponse(data=result_dict, msg="创建字典数据成功")


@DictRouter.put("/data/update/{id}", summary="修改字典数据", response_model=ResponseSchema[DictDataOutSchema])
async def update_data_controller(
    redis: Annotated[Redis, Depends(redis_getter)],
    db: Annotated[AsyncSession, Depends(db_getter)],
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:dict_data:update"]))],
    id: Annotated[int, Path(description="字典数据ID", ge=1)],
    data: Annotated[DictDataUpdateSchema, Body(description="字典数据修改参数")],
) -> JSONResponse:
    result_dict: DictDataOutSchema = await DictDataService(auth, db).update(redis=redis, id=id, data=data)
    return SuccessResponse(data=result_dict, msg="修改字典数据成功")


@DictRouter.delete("/data/delete", summary="删除字典数据", response_model=ResponseSchema[None])
async def delete_data_controller(
    redis: Annotated[Redis, Depends(redis_getter)],
    db: Annotated[AsyncSession, Depends(db_getter)],
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:dict_data:delete"]))],
    ids: Annotated[list[int], Body(description="ID列表")],
) -> JSONResponse:
    await DictDataService(auth, db).delete(redis=redis, ids=ids)
    return SuccessResponse(msg="删除字典数据成功")


@DictRouter.patch("/data/status/batch", summary="批量修改字典数据状态", response_model=ResponseSchema[None])
async def batch_set_available_dict_data_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:dict_data:patch"]))],
    data: Annotated[BatchSetAvailable, Body(description="状态设置")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    await DictDataService(auth, db).set_available(data=data)
    return SuccessResponse(msg="批量修改字典数据状态成功")


@DictRouter.get("/data/info/{dict_type}", summary="根据字典类型获取数据", response_model=ResponseSchema[list[DictDataOutSchema]])
async def get_init_dict_data_controller(
    redis: Annotated[Redis, Depends(redis_getter)],
    dict_type: Annotated[str, Path(description="字典类型")],
) -> JSONResponse:
    dict_data_query_result: list[dict[str, Any]] = await DictDataService.get_init_cache(redis=redis, dict_type=dict_type)
    return SuccessResponse(data=dict_data_query_result, msg="获取初始化字典数据成功")
