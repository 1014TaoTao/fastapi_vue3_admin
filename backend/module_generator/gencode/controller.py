from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query, Security, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseSchema, StreamResponse, SuccessResponse
from app.core.base_schema import AuthSchema, PageResultSchema, PaginationQueryParam
from app.core.dependencies import AuthPermission, db_getter
from app.core.logger import logger
from app.core.router_class import OperationLogRoute
from app.utils.common_util import bytes2file_response

from .schema import GenCreateTableSqlBody, GenDBTableSchema, GenSyncPreviewSchema, GenTableOutSchema, GenTableQueryParam, GenTableSchema
from .service import GenTableService

GenRouter = APIRouter(route_class=OperationLogRoute, prefix="/gencode", tags=["代码生成"])


@GenRouter.get("/list", summary="查询代码生成业务表列表", response_model=ResponseSchema[list[GenTableOutSchema]])
async def gen_table_list_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_generator:gencode:query"]))],
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[GenTableQueryParam, Query()],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    order_by = [{"created_time": "desc"}]
    if page.order_by:
        order_by = page.order_by
    result_dict = await GenTableService(auth, db).get_gen_table_page(
        page_no=page.page_no,
        page_size=page.page_size,
        search=search,
        order_by=order_by,
    )
    return SuccessResponse(data=result_dict, msg="获取代码生成业务表列表成功")


@GenRouter.get("/db/list", summary="查询数据库表列表", response_model=ResponseSchema[PageResultSchema[GenDBTableSchema]])
async def get_gen_db_table_list_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_generator:dblist:query"]))],
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[GenTableQueryParam, Query()],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result_dict = await GenTableService(auth, db).get_gen_db_table_page(
        page_no=page.page_no,
        page_size=page.page_size,
        search=search,
    )
    return SuccessResponse(data=result_dict, msg="获取数据库表列表成功")


@GenRouter.post("/import", summary="导入表结构", response_model=ResponseSchema[bool])
async def import_gen_table_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_generator:gencode:import"]))],
    table_names: Annotated[list[str], Body(description="表名列表")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    svc = GenTableService(auth, db)
    add_gen_table_list = await svc.get_gen_db_table_list_by_name(table_names)
    result = await svc.import_gen_table(add_gen_table_list)
    return SuccessResponse(msg="导入表结构成功", data=result)


@GenRouter.get("/detail/{table_id}", summary="获取业务表详细信息", response_model=ResponseSchema[GenTableOutSchema])
async def gen_table_detail_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_generator:gencode:query"]))],
    table_id: Annotated[int, Path(description="业务表ID")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await GenTableService(auth, db).get_gen_table_detail(table_id)
    return SuccessResponse(data=result, msg="获取业务表详细信息成功")


@GenRouter.post("/create", status_code=status.HTTP_201_CREATED, summary="创建表结构", response_model=ResponseSchema[bool])
async def create_table_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_generator:gencode:create"]))],
    body: Annotated[GenCreateTableSqlBody, Body(description="创建表结构参数")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await GenTableService(auth, db).create_table(body.sql)
    return SuccessResponse(msg="创建表结构成功", data=result)


@GenRouter.put("/update/{table_id}", summary="编辑业务表信息", response_model=ResponseSchema[GenTableOutSchema])
async def update_gen_table_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_generator:gencode:update"]))],
    table_id: Annotated[int, Path(description="业务表ID")],
    data: Annotated[GenTableSchema, Body(description="业务表信息")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result_dict = await GenTableService(auth, db).update_gen_table(data, table_id)
    return SuccessResponse(data=result_dict, msg="编辑业务表信息成功")


@GenRouter.delete("/delete", summary="删除业务表信息", response_model=ResponseSchema[None])
async def delete_gen_table_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_generator:gencode:delete"]))],
    ids: Annotated[list[int], Body(description="业务表ID列表")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await GenTableService(auth, db).delete_gen_table(ids)
    return SuccessResponse(msg="删除业务表信息成功", data=result)


@GenRouter.patch("/batch/output", summary="批量生成代码")
async def batch_gen_code_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_generator:gencode:operate"]))],
    table_names: Annotated[list[str], Body(description="表名列表")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> StreamResponse:
    batch_gen_code_result, failed_tables = await GenTableService(auth, db).batch_gen_code(table_names)
    headers = {"Content-Disposition": "attachment; filename=code.zip"}
    if failed_tables:
        logger.warning(f"批量生成代码部分失败，跳过表: {failed_tables}")
        headers["X-Skipped-Tables"] = ",".join(failed_tables)
    return StreamResponse(
        data=bytes2file_response(batch_gen_code_result),
        media_type="application/zip",
        headers=headers,
    )


@GenRouter.post("/output/{table_name}", summary="生成代码到指定路径", response_model=ResponseSchema[bool])
async def gen_code_local_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_generator:gencode:code"]))],
    table_name: Annotated[str, Path(description="表名")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await GenTableService(auth, db).generate_code(table_name)
    return SuccessResponse(msg="生成代码到指定路径成功", data=result)


@GenRouter.get("/preview/{table_id}", summary="预览代码", response_model=ResponseSchema[GenTableOutSchema])
async def preview_code_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_generator:gencode:query"]))],
    table_id: Annotated[int, Path(description="业务表ID")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await GenTableService(auth, db).preview_code(table_id)
    return SuccessResponse(data=result, msg="预览代码成功")


@GenRouter.post("/sync_db/{table_name}", summary="同步数据库", response_model=ResponseSchema[None])
async def sync_db_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_generator:db:sync"]))],
    table_name: Annotated[str, Path(description="表名")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await GenTableService(auth, db).sync_db(table_name)
    return SuccessResponse(msg="同步数据库成功", data=result)


@GenRouter.get("/sync_db/preview/{table_name}", summary="同步数据库差异预览", response_model=ResponseSchema[GenSyncPreviewSchema])
async def sync_db_preview_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_generator:db:sync"]))],
    table_name: Annotated[str, Path(description="表名")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await GenTableService(auth, db).sync_db_preview(table_name)
    return SuccessResponse(msg="获取同步差异预览成功", data=result)
