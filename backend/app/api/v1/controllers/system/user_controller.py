# -*- coding: utf-8 -*-

from fastapi import APIRouter, Depends, Query, UploadFile, Request
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import urllib.parse

from app.common.response import StreamResponse, SuccessResponse
from app.api.v1.services.system.user_service import UserService
from app.core.router_class import OperationLogRoute
from app.core.dependencies import db_getter, get_current_user, AuthPermission
from app.core.base_params import PaginationQueryParams
from app.api.v1.params.system.user_param import UserQueryParams
from app.api.v1.schemas.system.auth_schema import AuthSchema
from app.api.v1.schemas.system.user_schema import (
    CurrentUserUpdateSchema,
    UserCreateSchema,
    UserForgetPasswordSchema,
    UserRegisterSchema,
    UserUpdateSchema,
    UserChangePasswordSchema
)
from app.core.base_schema import BatchSetAvailable
from app.core.logger import logger
from app.common.request import PaginationService
from app.utils.common_util import bytes2file_response

router = APIRouter(route_class=OperationLogRoute)


@router.get("/current/info", summary="查询当前用户信息", description="查询当前用户信息")
async def get_current_user_info_controller(
    auth: AuthSchema = Depends(get_current_user)
) -> JSONResponse:
    result_dict = await UserService.get_current_user_info_service(auth=auth)
    logger.info("获取当前用户信息成功")
    return SuccessResponse(data=result_dict, msg='获取当前用户信息成功')


@router.post("/current/avatar/upload", summary="上传当前用户头像", dependencies=[Depends(get_current_user)])
async def user_avatar_upload_controller(
    file: UploadFile, 
    request: Request
) -> JSONResponse:
    result_str = await UserService.upload_avatar_service(base_url=str(request.base_url), file=file)
    logger.info(f"上传头像成功: {result_str}")
    return SuccessResponse(data=result_str, msg='上传头像成功')


@router.put("/current/info/update", summary="更新当前用户基本信息", description="更新当前用户基本信息")
async def update_current_user_info_controller(
    data: CurrentUserUpdateSchema,
    auth: AuthSchema = Depends(get_current_user)
) -> JSONResponse:
    result_dict = await UserService.update_current_user_info_service(data=data, auth=auth)
    logger.info(f"更新当前用户基本信息成功: {result_dict}")
    return SuccessResponse(data=result_dict, msg='更新当前用户基本信息成功')


@router.put("/current/password/change", summary="修改当前用户密码", description="修改当前用户密码")
async def change_current_user_password_controller(
    data: UserChangePasswordSchema,
    auth: AuthSchema = Depends(get_current_user)
) -> JSONResponse:
    result_dict = await UserService.change_user_password_service(data=data, auth=auth)
    logger.info(f"修改密码成功: {result_dict}")
    return SuccessResponse(data=result_dict, msg='修改密码成功, 请重新登录')


@router.post('/register', summary="注册用户", description="注册用户")
async def register_user_controller(
    data: UserRegisterSchema, 
    db: AsyncSession = Depends(db_getter),
) -> JSONResponse:
    auth = AuthSchema(db=db)
    user_register_result = await UserService.register_user_service(data=data, auth=auth)
    logger.info(f"{data.username} 注册用户成功: {user_register_result}")
    return SuccessResponse(data=user_register_result, msg='注册用户成功')


@router.post('/forget/password', summary="忘记密码", description="忘记密码")
async def forget_password_controller(
    data: UserForgetPasswordSchema, 
    db: AsyncSession = Depends(db_getter),
) -> JSONResponse:
    auth = AuthSchema(db=db)
    user_forget_password_result = await UserService.forget_password_service(data=data, auth=auth)
    logger.info(f"{data.username} 重置密码成功: {user_forget_password_result}")
    return SuccessResponse(data=user_forget_password_result, msg='重置密码成功')


@router.get("/list", summary="查询用户", description="查询用户")
async def get_obj_list_controller(
    page: PaginationQueryParams = Depends(),
    search: UserQueryParams = Depends(),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:user:query"])),
) -> JSONResponse:
    result_dict_list = await UserService.get_user_list_service(search=search, auth=auth, order_by=page.order_by)
    result_dict = await PaginationService.get_page_obj(data_list= result_dict_list, page_no= page.page_no, page_size = page.page_size)
    logger.info("查询用户成功")
    return SuccessResponse(data=result_dict, msg="查询用户成功")


@router.get("/detail", summary="查询用户详情", description="查询用户详情")
async def get_obj_detail_controller(
    id: str = Query(..., description="用户ID"),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:user:query"])),
) -> JSONResponse:
    result_dict = await UserService.get_detail_by_id_service(id=id, auth=auth)
    logger.info(f"获取用户详情成功 {id}")
    return SuccessResponse(data=result_dict, msg='获取用户详情成功')


@router.post("/create", summary="创建用户", description="创建用户")
async def create_obj_controller(
    data: UserCreateSchema,
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:user:create"])),
) -> JSONResponse:
    result_dict = await UserService.create_user_service(data=data, auth=auth)
    logger.info(f"创建用户成功: {result_dict}")
    return SuccessResponse(data=result_dict, msg="创建用户成功")


@router.put("/update", summary="修改用户", description="修改用户")
async def update_obj_controller(
    data: UserUpdateSchema,
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:user:update"])),
) -> JSONResponse:
    result_dict = await UserService.update_user_service(data=data, auth=auth)
    logger.info(f"修改用户成功: {result_dict}")
    return SuccessResponse(data=result_dict, msg="修改用户成功")


@router.delete("/delete", summary="删除用户", description="删除用户")
async def delete_obj_controller(
    id: str = Query(..., description="用户ID"),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:user:delete"])),
) -> JSONResponse:
    await UserService.delete_user_service(id=id, auth=auth)
    logger.info(f"删除用户成功: {id}")
    return SuccessResponse(msg="删除用户成功")


@router.patch("/available/setting", summary="批量修改用户状态", description="批量修改用户状态")
async def batch_set_available_obj_controller(
    data: BatchSetAvailable,
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:user:patch"])),
) -> JSONResponse:
    await UserService.set_user_available_service(data=data, auth=auth)
    logger.info(f"批量修改用户状态成功: {data.ids}")
    return SuccessResponse(msg="批量修改用户状态成功")


@router.post('/import/template', summary="获取用户导入模板", description="获取用户导入模板", dependencies=[Depends(AuthPermission(permissions=["system:user:import"]))])
async def export_obj_template_controller()-> StreamingResponse:
    user_import_template_result = await UserService.get_import_template_user_service()
    logger.info('获取用户导入模板成功')

    return StreamResponse(
        data=bytes2file_response(user_import_template_result),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers = {
            'Content-Disposition': f'attachment; filename={urllib.parse.quote("用户导入模板.xlsx")}',
            'Access-Control-Expose-Headers': 'Content-Disposition'
        }
    )


@router.post('/export', summary="导出用户", description="导出用户")
async def export_obj_list_controller(
    page: PaginationQueryParams = Depends(),
    search: UserQueryParams = Depends(),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:user:export"])),
) -> StreamingResponse:
    # 获取全量数据
    user_list = await UserService.get_user_list_service(auth=auth, search=search, order_by=page.order_by)
    user_export_result = await UserService.export_user_list_service(user_list)
    logger.info('导出用户成功')

    return StreamResponse(
        data=bytes2file_response(user_export_result),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers = {
            'Content-Disposition': 'attachment; filename=data.xlsx'
        }
    )


@router.post('/import/data', summary="导入用户", description="导入用户")
async def import_obj_list_controller(
    file: UploadFile,
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:user:import"]))
) -> JSONResponse:
    batch_import_result = await UserService.batch_import_user_service(file=file, auth=auth, update_support=True)
    logger.info(f"导入用户成功: {batch_import_result}")
    return SuccessResponse(data=batch_import_result, msg="导入用户成功")
