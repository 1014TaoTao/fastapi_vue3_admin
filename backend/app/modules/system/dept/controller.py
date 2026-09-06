from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Path, Query, Security, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseSchema, SuccessResponse
from app.core.base_schema import AuthSchema, BatchSetAvailable
from app.core.dependencies import AuthPermission, db_getter
from app.core.router_class import OperationLogRoute

from .schema import DeptCreateSchema, DeptOutSchema, DeptQueryParam, DeptUpdateSchema
from .service import DeptService

DeptRouter = APIRouter(route_class=OperationLogRoute, prefix="/dept", tags=["部门管理"])


@DeptRouter.get("/tree", summary="查询部门树", response_model=ResponseSchema[list[DeptOutSchema]])
async def get_dept_tree_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:dept:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    search: Annotated[DeptQueryParam, Query()],
) -> JSONResponse:
    order_by: list[dict[str, str]] = [{"order": "asc"}]
    result_dict_tree: list[dict[str, Any]] = await DeptService(auth, db).tree(search=search, order_by=order_by)
    return SuccessResponse(data=result_dict_tree, msg="查询部门树成功")


@DeptRouter.get("/detail/{id}", summary="查询部门详情", response_model=ResponseSchema[DeptOutSchema])
async def get_obj_detail_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:dept:detail"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    id: Annotated[int, Path(description="部门ID", ge=1)],
) -> JSONResponse:
    result_dict: DeptOutSchema = await DeptService(auth, db).detail(id=id)
    return SuccessResponse(data=result_dict, msg="查询部门详情成功")


@DeptRouter.post("/create", status_code=status.HTTP_201_CREATED, summary="创建部门", response_model=ResponseSchema[DeptOutSchema])
async def create_obj_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:dept:create"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    data: Annotated[DeptCreateSchema, Body(description="部门创建参数")],
) -> JSONResponse:
    result_dict: DeptOutSchema = await DeptService(auth, db).create(data=data)
    return SuccessResponse(data=result_dict, msg="创建部门成功")


@DeptRouter.put("/update/{id}", summary="修改部门", response_model=ResponseSchema[DeptOutSchema])
async def update_obj_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:dept:update"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    id: Annotated[int, Path(description="部门ID", ge=1)],
    data: Annotated[DeptUpdateSchema, Body(description="部门修改参数")],
) -> JSONResponse:
    result_dict: DeptOutSchema = await DeptService(auth, db).update(id=id, data=data)
    return SuccessResponse(data=result_dict, msg="修改部门成功")


@DeptRouter.delete("/delete", summary="删除部门", response_model=ResponseSchema[None])
async def delete_obj_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:dept:delete"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    ids: Annotated[list[int], Body(description="ID列表")],
) -> JSONResponse:
    await DeptService(auth, db).delete(ids=ids)
    return SuccessResponse(msg="删除部门成功")


@DeptRouter.patch("/status/batch", summary="批量修改部门状态", response_model=ResponseSchema[None])
async def batch_set_available_obj_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:dept:patch"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    data: Annotated[BatchSetAvailable, Body(description="状态设置")],
) -> JSONResponse:
    await DeptService(auth, db).set_available(data=data)
    return SuccessResponse(msg="批量修改部门状态成功")
