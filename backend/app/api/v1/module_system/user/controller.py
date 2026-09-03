import urllib.parse
from typing import Annotated

from fastapi import APIRouter, Body, Depends, File, Path, Query, Security, UploadFile, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseSchema, StreamResponse, SuccessResponse
from app.core.base_schema import AuthSchema, BatchSetAvailable, PageResultSchema, PaginationQueryParam
from app.core.dependencies import AuthPermission, db_getter, get_current_user
from app.core.logger import logger
from app.core.router_class import OperationLogRoute
from app.utils.common_util import bytes2file_response

from .schema import (
    CurrentUserOutSchema,
    CurrentUserUpdateSchema,
    ResetPasswordSchema,
    UserChangePasswordSchema,
    UserCreateSchema,
    UserForgetPasswordSchema,
    UserOutSchema,
    UserQueryParam,
    UserRegisterSchema,
    UserUpdateSchema,
)
from .service import UserService

UserRouter = APIRouter(route_class=OperationLogRoute, prefix="/user", tags=["用户管理"])


@UserRouter.get("/current/info", summary="查询当前用户信息", response_model=ResponseSchema[CurrentUserOutSchema])
async def get_current_user_info_controller(
    auth: Annotated[AuthSchema, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(db_getter)],
    check_data_scope: Annotated[bool, Query(description="是否加载完整数据（含部门/岗位/角色/OAuth），True-加载全部(默认)，False-仅菜单/权限")] = True,
) -> JSONResponse:
    user_dict = await UserService(auth, db).current_info(check_data_scope=check_data_scope)
    return SuccessResponse(data=user_dict, msg="获取当前用户信息成功")


@UserRouter.put("/current/info/update", summary="更新当前用户基本信息", response_model=ResponseSchema[UserOutSchema])
async def update_current_user_info_controller(
    auth: Annotated[AuthSchema, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(db_getter)],
    data: Annotated[CurrentUserUpdateSchema, Body(description="更新用户基本信息参数")],
) -> JSONResponse:
    result_dict = await UserService(auth, db).update_current_info(data=data)
    return SuccessResponse(data=result_dict, msg="更新当前用户基本信息成功")


@UserRouter.put("/password/change", summary="修改当前用户密码", response_model=ResponseSchema[UserOutSchema])
async def change_current_user_password_controller(
    auth: Annotated[AuthSchema, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(db_getter)],
    data: Annotated[UserChangePasswordSchema, Body(description="修改用户密码参数")],
) -> JSONResponse:
    result_dict = await UserService(auth, db).change_password(data=data)
    return SuccessResponse(data=result_dict, msg="修改密码成功, 请重新登录")


@UserRouter.put("/password/reset/{id}", summary="重置用户密码", response_model=ResponseSchema[UserOutSchema])
async def reset_password_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:user:update"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    id: Annotated[int, Path(description="用户ID", ge=1)],
    data: Annotated[ResetPasswordSchema, Body(description="重置用户密码参数")],
) -> JSONResponse:
    data.id = id
    result_dict = await UserService(auth, db).reset_password(data=data)
    return SuccessResponse(data=result_dict, msg="重置密码成功")


@UserRouter.post("/password/forget", summary="忘记密码", response_model=ResponseSchema[UserOutSchema])
async def forget_password_controller(
    db: Annotated[AsyncSession, Depends(db_getter)],
    data: Annotated[UserForgetPasswordSchema, Body(description="忘记密码参数")],
) -> JSONResponse:
    auth = AuthSchema()
    user_forget_password_result = await UserService(auth, db).forget_password(data=data)
    logger.info(f"{data.username} 重置密码成功")
    return SuccessResponse(data=user_forget_password_result, msg="重置密码成功")


@UserRouter.post("/register", summary="用户注册", response_model=ResponseSchema[UserOutSchema])
async def register_controller(
    db: Annotated[AsyncSession, Depends(db_getter)],
    data: Annotated[UserRegisterSchema, Body(description="用户注册参数")],
) -> JSONResponse:
    auth = AuthSchema()
    register_result = await UserService(auth, db).register(data=data)
    logger.info(f"新用户注册成功: {data.username}")
    return SuccessResponse(data=register_result, msg="注册成功")


@UserRouter.get("/list", summary="查询用户", response_model=ResponseSchema[PageResultSchema[UserOutSchema]])
async def get_user_list_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:user:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[UserQueryParam, Query()],
) -> JSONResponse:
    result_dict = await UserService(auth, db).page(
        page_no=page.page_no,
        page_size=page.page_size,
        search=search,
        order_by=page.order_by,
    )
    return SuccessResponse(data=result_dict, msg="查询用户成功")


@UserRouter.get("/detail/{id}", summary="查询用户详情", response_model=ResponseSchema[UserOutSchema])
async def get_user_detail_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:user:detail"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    id: Annotated[int, Path(description="用户ID", ge=1)],
) -> JSONResponse:
    result_dict = await UserService(auth, db).detail(id=id)
    return SuccessResponse(data=result_dict, msg="获取用户详情成功")


@UserRouter.post("/create", status_code=status.HTTP_201_CREATED, summary="创建用户", response_model=ResponseSchema[UserOutSchema])
async def create_user_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:user:create"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    data: Annotated[UserCreateSchema, Body(description="创建用户参数")],
) -> JSONResponse:
    result_dict = await UserService(auth, db).create(data=data)
    return SuccessResponse(data=result_dict, msg="创建用户成功")


@UserRouter.put("/update/{id}", summary="修改用户", response_model=ResponseSchema[UserOutSchema])
async def update_user_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:user:update"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    id: Annotated[int, Path(description="用户ID")],
    data: Annotated[UserUpdateSchema, Body(description="修改用户参数")],
) -> JSONResponse:
    result_dict = await UserService(auth, db).update(id=id, data=data)
    return SuccessResponse(data=result_dict, msg="修改用户成功")


@UserRouter.delete("/delete", summary="删除用户", response_model=ResponseSchema[None])
async def delete_user_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:user:delete"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    ids: Annotated[list[int], Body(description="ID列表")],
) -> JSONResponse:
    await UserService(auth, db).delete(ids=ids)
    return SuccessResponse(msg="删除用户成功")


@UserRouter.patch("/status/batch", summary="批量修改用户状态", response_model=ResponseSchema[None])
async def batch_set_available_user_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:user:patch"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    data: Annotated[BatchSetAvailable, Body(description="状态设置")],
) -> JSONResponse:
    await UserService(auth, db).set_available(data=data)
    return SuccessResponse(msg="批量修改用户状态成功")


@UserRouter.get("/import/template", summary="获取用户导入模板", dependencies=[Security(AuthPermission(["module_system:user:download"]))])
async def export_user_import_template_controller() -> StreamingResponse:
    user_import_template_result = UserService.get_import_template()

    return StreamResponse(
        data=bytes2file_response(user_import_template_result),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename={urllib.parse.quote('用户导入模板.xlsx')}",
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


@UserRouter.post("/export", summary="导出用户")
async def export_user_list_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:user:export"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[UserQueryParam, Body()],
) -> StreamingResponse:
    user_list = await UserService(auth, db).get_list(search=search, order_by=page.order_by)
    user_export_result = await UserService.export_list(user_list=[item.model_dump() for item in user_list])

    return StreamResponse(
        data=bytes2file_response(user_export_result),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=user.xlsx"},
    )


@UserRouter.post("/import/data", summary="导入用户", response_model=ResponseSchema[None])
async def import_user_list_controller(
    file: Annotated[UploadFile, File(description="用户导入文件")],
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:user:import"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    batch_import_result = await UserService(auth, db).batch_import(file=file, update_support=True)
    return SuccessResponse(data=batch_import_result, msg="导入用户成功")
