import os
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Body, Depends, File, Form, Query, Security, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseSchema, SuccessResponse, UploadFileResponse
from app.core.base_schema import AuthSchema
from app.core.dependencies import AuthPermission, db_getter
from app.core.router_class import OperationLogRoute
from app.modules.task.storage.core.base import StorageObject, StoragePage

from .schema import StoragePathCreateSchema, StoragePathResultSchema, StorageUploadResultSchema
from .service import StorageFileService

StorageBrowseRouter = APIRouter(route_class=OperationLogRoute, prefix="/storage/browse", tags=["存储管理"])


def _delete_temp_file(path: str) -> None:
    """响应发送后清理临时下载文件。"""
    try:
        os.unlink(path)
    except OSError:
        pass


@StorageBrowseRouter.post("/upload", summary="上传文件到存储源", response_model=ResponseSchema[StorageUploadResultSchema])
async def upload_storage_file_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:storage:browse:upload"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    file: Annotated[UploadFile, File(description="上传文件")],
    source_id: Annotated[int | None, Form(description="存储源ID（不传使用默认存储源）")] = None,
    remote_path: Annotated[str | None, Form(description="远端目录路径（不传自动生成文件名）")] = None,
    bucket: Annotated[str | None, Form(description="存储桶（对象存储多桶浏览用，可选）")] = None,
) -> JSONResponse:
    result: StorageUploadResultSchema = await StorageFileService(auth, db).upload(
        source_id=source_id, file=file, remote_path=remote_path, bucket=bucket
    )
    return SuccessResponse(data=result, msg="上传文件成功")


@StorageBrowseRouter.post("/download", summary="下载存储源文件", response_model=None)
async def download_storage_file_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:storage:browse:download"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    background_tasks: BackgroundTasks,
    remote_path: Annotated[str, Body(description="远端文件路径")],
    source_id: Annotated[int | None, Body(description="存储源ID（不传使用默认存储源）")] = None,
    bucket: Annotated[str | None, Body(description="存储桶（对象存储多桶浏览用，可选）")] = None,
) -> UploadFileResponse:
    local_path, file_name = await StorageFileService(auth, db).download(
        source_id=source_id, remote_path=remote_path, bucket=bucket
    )
    background_tasks.add_task(_delete_temp_file, local_path)
    return UploadFileResponse(file_path=local_path, filename=file_name)


@StorageBrowseRouter.post("/download_dir", summary="下载存储源目录（递归打包ZIP）", response_model=None)
async def download_dir_storage_file_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:storage:browse:download"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    background_tasks: BackgroundTasks,
    remote_path: Annotated[str, Body(description="远端目录路径")],
    source_id: Annotated[int | None, Body(description="存储源ID（不传使用默认存储源）")] = None,
    bucket: Annotated[str | None, Body(description="存储桶（对象存储多桶浏览用，可选）")] = None,
) -> UploadFileResponse:
    local_path, file_name = await StorageFileService(auth, db).download_dir(
        source_id=source_id, remote_path=remote_path, bucket=bucket
    )
    background_tasks.add_task(_delete_temp_file, local_path)
    return UploadFileResponse(file_path=local_path, filename=file_name)


@StorageBrowseRouter.delete("/delete", summary="删除存储源文件", response_model=ResponseSchema[None])
async def delete_storage_file_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:storage:browse:delete"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    remote_path: Annotated[str, Body(description="远端文件路径")],
    source_id: Annotated[int | None, Body(description="存储源ID（不传使用默认存储源）")] = None,
    bucket: Annotated[str | None, Body(description="存储桶（对象存储多桶浏览用，可选）")] = None,
) -> JSONResponse:
    await StorageFileService(auth, db).delete(source_id=source_id, remote_path=remote_path, bucket=bucket)
    return SuccessResponse(msg="删除文件成功")


@StorageBrowseRouter.get("/list", summary="查询存储源文件列表", response_model=None)
async def list_storage_file_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:storage:browse:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    source_id: Annotated[int | None, Query(description="存储源ID（不传使用默认存储源）")] = None,
    prefix: Annotated[str | None, Query(description="目录前缀（可选）")] = None,
    bucket: Annotated[str | None, Query(description="存储桶（对象存储多桶浏览用，可选）")] = None,
    page_size: Annotated[int | None, Query(ge=1, le=500, description="每页数量（传了才走游标分页，不传返回全量）")] = None,
    cursor: Annotated[str | None, Query(description="下一页游标（上一页返回的 next_cursor，可选）")] = None,
) -> JSONResponse:
    result: StoragePage | list[StorageObject] = await StorageFileService(auth, db).list_files(
        source_id=source_id, prefix=prefix or "", bucket=bucket, page_size=page_size, cursor=cursor
    )
    return SuccessResponse(data=result, msg="查询文件列表成功")


@StorageBrowseRouter.get("/buckets", summary="查询存储源桶列表", response_model=ResponseSchema[list[str]])
async def list_storage_buckets_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:storage:browse:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    source_id: Annotated[int | None, Query(description="存储源ID（不传使用默认存储源）")] = None,
) -> JSONResponse:
    result: list[str] = await StorageFileService(auth, db).list_buckets(source_id=source_id)
    return SuccessResponse(data=result, msg="查询桶列表成功")


@StorageBrowseRouter.post("/copy", summary="复制/移动文件", response_model=ResponseSchema[StoragePathResultSchema])
async def copy_or_move_storage_file_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:storage:browse:update"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    source_id: Annotated[int | None, Body(description="源存储源ID（不传使用默认存储源）")] = None,
    source_path: Annotated[str, Body(description="源文件路径")] = "",
    target_id: Annotated[int, Body(description="目标存储源ID")] = 0,
    target_path: Annotated[str, Body(description="目标路径")] = "",
    move: Annotated[bool, Body(description="是否为移动（true 移动/重命名，false 复制）")] = False,
    bucket: Annotated[str | None, Body(description="存储桶（对象存储多桶浏览用，可选）")] = None,
) -> JSONResponse:
    result: StoragePathResultSchema = await StorageFileService(auth, db).copy_or_move(
        source_id=source_id,
        source_path=source_path,
        target_id=target_id,
        target_path=target_path,
        move=move,
        bucket=bucket,
    )
    return SuccessResponse(data=result, msg="操作文件成功")


@StorageBrowseRouter.put("/rename", summary="重命名/移动文件", response_model=ResponseSchema[StoragePathResultSchema])
async def rename_storage_file_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:storage:browse:update"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    source_id: Annotated[int | None, Body(description="存储源ID（不传使用默认存储源）")] = None,
    source_path: Annotated[str, Body(description="原路径")] = "",
    target_path: Annotated[str, Body(description="新路径")] = "",
    bucket: Annotated[str | None, Body(description="存储桶（对象存储多桶浏览用，可选）")] = None,
) -> JSONResponse:
    result: StoragePathResultSchema = await StorageFileService(auth, db).rename(
        source_id=source_id, src_path=source_path, dst_path=target_path, bucket=bucket
    )
    return SuccessResponse(data=result, msg="重命名成功")


@StorageBrowseRouter.post("/mkdir", summary="新建目录", response_model=ResponseSchema[StoragePathCreateSchema])
async def mkdir_storage_file_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:storage:browse:update"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    source_id: Annotated[int | None, Body(description="存储源ID（不传使用默认存储源）")] = None,
    remote_dir: Annotated[str, Body(description="目录路径")] = "",
    bucket: Annotated[str | None, Body(description="存储桶（对象存储多桶浏览用，可选）")] = None,
) -> JSONResponse:
    result: StoragePathCreateSchema = await StorageFileService(auth, db).mkdir(source_id=source_id, remote_dir=remote_dir, bucket=bucket)
    return SuccessResponse(data=result, msg="新建目录成功")


@StorageBrowseRouter.post("/share", summary="生成分享链接", response_model=ResponseSchema[str | None])
async def share_storage_file_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:storage:browse:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    remote_path: Annotated[str, Body(description="远端文件路径")] = "",
    source_id: Annotated[int | None, Body(description="存储源ID（不传使用默认存储源）")] = None,
    expire: Annotated[int, Body(description="有效期（秒）", ge=60, le=604800)] = 3600,
    bucket: Annotated[str | None, Body(description="存储桶（对象存储多桶浏览用，可选）")] = None,
) -> JSONResponse:
    result: str | None = await StorageFileService(auth, db).share(
        source_id=source_id, remote_path=remote_path, expire=expire, bucket=bucket
    )
    return SuccessResponse(data=result, msg="生成分享链接成功")
