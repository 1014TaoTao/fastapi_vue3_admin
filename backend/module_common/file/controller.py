from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, BackgroundTasks, Body, Depends, File, Form, Query, Request, Security, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from app.common.response import ResponseSchema, SuccessResponse, UploadFileResponse
from app.core.base_schema import AuthSchema, UploadResponseSchema
from app.core.dependencies import AuthPermission, get_current_user
from app.core.router_class import OperationLogRoute
from app.utils.upload_util import UploadUtil

from .service import FileService

FileRouter = APIRouter(route_class=OperationLogRoute, prefix="/file", tags=["文件管理"])


@FileRouter.post("/upload", summary="上传文件", response_model=ResponseSchema[UploadResponseSchema], dependencies=[Security(AuthPermission(["module_common:file:upload"]))])
async def upload_controller(
    request: Request,
    auth: Annotated[AuthSchema, Depends(get_current_user)],
    file: Annotated[UploadFile, File(description="上传文件")],
    upload_type: Annotated[
        Literal["file", "avatar", "param", "resource"] | None,
        Query(description="上传类型: file=通用文件, avatar=头像, param=参数配置, resource=监控资源"),
    ] = "file",
    target_path: Annotated[str | None, Form(description="目标目录路径（仅 resource 类型支持）")] = None,
) -> JSONResponse:
    result = await FileService.upload_service(
        base_url=str(request.base_url),
        file=file,
        upload_type=upload_type or "file",
        target_path=target_path,
    )
    return SuccessResponse(data=result, msg="上传文件成功")


@FileRouter.post("/download", summary="下载文件", dependencies=[Security(AuthPermission(["module_common:file:download"]))])
async def download_controller(
    auth: Annotated[AuthSchema, Depends(get_current_user)],
    background_tasks: BackgroundTasks,
    file_path: Annotated[str, Body(description="文件路径")],
    delete: Annotated[bool, Body(description="是否删除文件")] = False,
) -> FileResponse:
    result = await FileService.download_service(file_path=file_path)
    if delete:
        background_tasks.add_task(UploadUtil.delete_file, Path(result.file_path))
    return UploadFileResponse(file_path=result.file_path, filename=result.file_name)
