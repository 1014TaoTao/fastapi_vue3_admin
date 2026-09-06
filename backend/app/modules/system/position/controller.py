from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Path, Query, Security, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseSchema, StreamResponse, SuccessResponse
from app.core.base_schema import AuthSchema, BatchSetAvailable, PageResultSchema, PaginationQueryParam
from app.core.dependencies import AuthPermission, db_getter
from app.core.router_class import OperationLogRoute
from app.utils.common_util import bytes2file_response

from .schema import PositionCreateSchema, PositionOutSchema, PositionQueryParam, PositionUpdateSchema
from .service import PositionService

PositionRouter = APIRouter(route_class=OperationLogRoute, prefix="/position", tags=["岗位管理"])


@PositionRouter.get("/list", summary="查询岗位", response_model=ResponseSchema[PageResultSchema[PositionOutSchema]])
async def get_obj_list_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:position:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[PositionQueryParam, Query()],
) -> JSONResponse:
    result_dict: PageResultSchema[PositionOutSchema] = await PositionService(auth, db).page(
        page_no=page.page_no,
        page_size=page.page_size,
        search=search,
        order_by=page.order_by,
    )
    return SuccessResponse(data=result_dict, msg="查询岗位列表成功")


@PositionRouter.get("/detail/{id}", summary="查询岗位详情", response_model=ResponseSchema[PositionOutSchema])
async def get_obj_detail_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:position:detail"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    id: Annotated[int, Path(description="岗位ID", ge=1)],
) -> JSONResponse:
    result_dict: PositionOutSchema = await PositionService(auth, db).detail(id=id)
    return SuccessResponse(data=result_dict, msg="获取岗位详情成功")


@PositionRouter.post("/create", status_code=status.HTTP_201_CREATED, summary="创建岗位", response_model=ResponseSchema[PositionOutSchema])
async def create_obj_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:position:create"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    data: Annotated[PositionCreateSchema, Body(description="岗位创建参数")],
) -> JSONResponse:
    result_dict: PositionOutSchema = await PositionService(auth, db).create(data=data)
    return SuccessResponse(data=result_dict, msg="创建岗位成功")


@PositionRouter.put("/update/{id}", summary="修改岗位", response_model=ResponseSchema[PositionOutSchema])
async def update_obj_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:position:update"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    id: Annotated[int, Path(description="岗位ID", ge=1)],
    data: Annotated[PositionUpdateSchema, Body(description="岗位修改参数")],
) -> JSONResponse:
    result_dict: PositionOutSchema = await PositionService(auth, db).update(id=id, data=data)
    return SuccessResponse(data=result_dict, msg="修改岗位成功")


@PositionRouter.delete("/delete", summary="删除岗位", response_model=ResponseSchema[None])
async def delete_obj_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:position:delete"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    ids: Annotated[list[int], Body(description="ID列表")],
) -> JSONResponse:
    await PositionService(auth, db).delete(ids=ids)
    return SuccessResponse(msg="删除岗位成功")


@PositionRouter.patch("/status/batch", summary="批量修改岗位状态", response_model=ResponseSchema[None])
async def batch_set_available_obj_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:position:patch"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    data: Annotated[BatchSetAvailable, Body(description="状态设置")],
) -> JSONResponse:
    await PositionService(auth, db).set_available(data=data)
    return SuccessResponse(msg="批量修改岗位状态成功")


@PositionRouter.get("/options", summary="获取岗位下拉选项", response_model=ResponseSchema[list[dict[str, int | str]]])
async def get_position_options_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:position:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    options: list[dict[str, Any]] = await PositionService(auth, db).get_options()
    return SuccessResponse(data=options, msg="获取岗位选项成功")


@PositionRouter.post("/export", summary="导出岗位")
async def export_obj_list_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:position:export"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    search: Annotated[PositionQueryParam, Body()],
) -> StreamingResponse:
    position_query_result: list[PositionOutSchema] = await PositionService(auth, db).get_list(search=search)
    position_export_result: bytes = await PositionService.export_list(position_list=[item.model_dump() for item in position_query_result])

    return StreamResponse(
        data=bytes2file_response(position_export_result),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=position.xlsx"},
    )
