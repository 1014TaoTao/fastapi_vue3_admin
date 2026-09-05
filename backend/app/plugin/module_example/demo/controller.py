import urllib.parse
from typing import Annotated

from fastapi import APIRouter, Body, Depends, File, Path, Query, Security, UploadFile, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseSchema, StreamResponse, SuccessResponse
from app.core.base_schema import AuthSchema, BatchSetAvailable, PageResultSchema, PaginationQueryParam
from app.core.dependencies import AuthPermission, db_getter
from app.core.router_class import OperationLogRoute
from app.utils.common_util import bytes2file_response

from .schema import DemoCreateSchema, DemoOutSchema, DemoQueryParam, DemoUpdateSchema
from .service import DemoService

DemoRouter = APIRouter(route_class=OperationLogRoute, prefix="/demo", tags=["示例管理"])


@DemoRouter.get("/detail/{id}", summary="获取示例详情", response_model=ResponseSchema[DemoOutSchema])
async def get_obj_detail_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_example:demo:detail"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    id: Annotated[int, Path(description="示例ID", ge=1)],
) -> JSONResponse:
    result_dict: DemoOutSchema = await DemoService(auth, db).detail(id=id)
    return SuccessResponse(data=result_dict, msg="获取示例详情成功")


@DemoRouter.get("/list", summary="分页查询示例", response_model=ResponseSchema[PageResultSchema[DemoOutSchema]])
async def get_obj_list_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_example:demo:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[DemoQueryParam, Query()],
) -> JSONResponse:
    result_dict: PageResultSchema[DemoOutSchema] = await DemoService(auth, db).page(
        page_no=page.page_no,
        page_size=page.page_size,
        search=search,
        order_by=page.order_by,
    )
    return SuccessResponse(data=result_dict, msg="查询示例列表成功")


@DemoRouter.post("/create", status_code=status.HTTP_201_CREATED, summary="创建示例", response_model=ResponseSchema[DemoOutSchema])
async def create_obj_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_example:demo:create"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    data: Annotated[DemoCreateSchema, Body(description="创建参数")],
) -> JSONResponse:
    result_dict: DemoOutSchema = await DemoService(auth, db).create(data=data)
    return SuccessResponse(data=result_dict, msg="创建示例成功")


@DemoRouter.put("/update/{id}", summary="修改示例", response_model=ResponseSchema[DemoOutSchema])
async def update_obj_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_example:demo:update"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    id: Annotated[int, Path(description="示例ID", ge=1)],
    data: Annotated[DemoUpdateSchema, Body(description="修改参数")],
) -> JSONResponse:
    result_dict: DemoOutSchema = await DemoService(auth, db).update(id=id, data=data)
    return SuccessResponse(data=result_dict, msg="修改示例成功")


@DemoRouter.delete("/delete", summary="删除示例", response_model=ResponseSchema[None])
async def delete_obj_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_example:demo:delete"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    ids: Annotated[list[int], Body(description="ID列表")],
) -> JSONResponse:
    await DemoService(auth, db).delete(ids=ids)
    return SuccessResponse(msg="删除示例成功")


@DemoRouter.patch("/status/batch", summary="批量修改示例状态", response_model=ResponseSchema[None])
async def batch_set_available_obj_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_example:demo:patch"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    data: Annotated[BatchSetAvailable, Body(description="状态设置")],
) -> JSONResponse:
    await DemoService(auth, db).set_available(data=data)
    return SuccessResponse(msg="批量修改示例状态成功")


@DemoRouter.post("/export", summary="导出示例")
async def export_obj_list_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_example:demo:export"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    search: Annotated[DemoQueryParam, Body()],
) -> StreamingResponse:
    result_dict_list: list[DemoOutSchema] = await DemoService(auth, db).get_list(search=search)
    export_result: bytes = await DemoService.batch_export(obj_list=[item.model_dump() for item in result_dict_list])

    return StreamResponse(
        data=bytes2file_response(export_result),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=demo.xlsx"},
    )


@DemoRouter.post("/import", summary="导入示例", response_model=ResponseSchema[str])
async def import_obj_list_controller(
    file: Annotated[UploadFile, File(description="导入文件")],
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_example:demo:import"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    batch_import_result = await DemoService(auth, db).batch_import(file=file, update_support=True)
    return SuccessResponse(data=batch_import_result, msg="导入示例成功")


@DemoRouter.post("/download/template", summary="获取示例导入模板", dependencies=[Security(AuthPermission(["module_example:demo:download"]))])
async def export_obj_template_controller() -> StreamingResponse:
    import_template_result: bytes = DemoService.import_template_download()

    return StreamResponse(
        data=bytes2file_response(import_template_result),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename={urllib.parse.quote('示例导入模板.xlsx')}",
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )
