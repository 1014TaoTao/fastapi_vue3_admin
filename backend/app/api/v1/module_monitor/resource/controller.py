# -*- coding: utf-8 -*-

from fastapi import APIRouter, Body, Depends, Path, Query, Request, UploadFile, Form
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from typing import List, Optional

# from oss2 import auth # 预留阿里云OSS，后期使用

from app.common.response import StreamResponse, SuccessResponse, ErrorResponse
from app.common.request import PaginationService
from app.utils.common_util import bytes2file_response
from app.core.base_params import PaginationQueryParam
from app.core.dependencies import AuthPermission
from app.core.router_class import OperationLogRoute
from app.core.logger import logger
from .param import ResourceSearchQueryParam
from .schema import (
    ResourceMoveSchema,
    ResourceCopySchema,
    ResourceRenameSchema,
    ResourceCreateDirSchema
)
from .service import ResourceService

ResourceRouter = APIRouter(route_class=OperationLogRoute, prefix="/resource", tags=["资源管理"])

@ResourceRouter.get(
    "/list", 
    summary="获取目录列表", 
    description="获取指定目录下的文件和子目录列表",
    dependencies=[Depends(AuthPermission(["monitor:resource:query"]))]
)
async def get_directory_list_controller(
    request: Request,
    page: PaginationQueryParam = Depends(),
    search: ResourceSearchQueryParam = Depends(),
) -> JSONResponse:
    """获取目录列表"""
    # 获取资源列表（与案例模块保持一致的分页实现）
    result_dict_list = await ResourceService.get_resources_list_service(
        search=search, 
        base_url=str(request.base_url)
    )
    # 使用分页服务进行分页处理（与案例模块保持一致）
    result_dict = await PaginationService.paginate(
        data_list=result_dict_list, 
        page_no=page.page_no, 
        page_size=page.page_size
    )
    
    logger.info(f"获取目录列表成功: {getattr(search, 'name', None) or ''}")
    return SuccessResponse(data=result_dict, msg="获取目录列表成功")


@ResourceRouter.post(
    "/upload", 
    summary="上传文件", 
    description="上传文件到指定目录",
    dependencies=[Depends(AuthPermission(["monitor:resource:upload"]))])
async def upload_file_controller(
    file: UploadFile,
    request: Request,
    target_path: Optional[str] = Form(None, description="目标目录路径")
) -> JSONResponse:
    """上传文件"""
    result_dict = await ResourceService.upload_file_service(
        file=file,
        target_path=target_path,
        base_url=str(request.base_url)
    )
    logger.info(f"上传文件成功: {result_dict['filename']}")
    return SuccessResponse(data=result_dict, msg="上传文件成功")


@ResourceRouter.get(
    "/download", 
    summary="下载文件", 
    description="下载指定文件",
    dependencies=[Depends(AuthPermission(["monitor:resource:download"]))]
)
async def download_file_controller(
    request: Request,
    path: str = Query(..., description="文件路径")
) -> FileResponse:
    """下载文件"""
    file_path = await ResourceService.download_file_service(
        file_path=path,
        base_url=str(request.base_url)
    )
    
    # 获取文件名
    import os
    filename = os.path.basename(file_path)
    
    logger.info(f"下载文件成功: {filename}")
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )


@ResourceRouter.delete(
    "/delete", 
    summary="删除文件", 
    description="删除指定文件或目录",
    dependencies=[Depends(AuthPermission(["monitor:resource:delete"]))]
)
async def delete_files_controller(
    paths: List[str] = Body(..., description="文件路径列表")
) -> JSONResponse:
    """删除文件"""
    await ResourceService.delete_file_service(paths=paths)
    logger.info(f"删除文件成功: {paths}")
    return SuccessResponse(msg="删除文件成功")


@ResourceRouter.post(
    "/move", 
    summary="移动文件", 
    description="移动文件或目录",
    dependencies=[Depends(AuthPermission(["monitor:resource:move"]))]
)
async def move_file_controller(
    data: ResourceMoveSchema
) -> JSONResponse:
    """移动文件"""
    await ResourceService.move_file_service(data=data)
    logger.info(f"移动文件成功: {data.source_path} -> {data.target_path}")
    return SuccessResponse(msg="移动文件成功")


@ResourceRouter.post(
    "/copy", 
    summary="复制文件", 
    description="复制文件或目录",
    dependencies=[Depends(AuthPermission(["monitor:resource:copy"]))]
)
async def copy_file_controller(
    data: ResourceCopySchema
) -> JSONResponse:
    """复制文件"""
    await ResourceService.copy_file_service(data=data)
    logger.info(f"复制文件成功: {data.source_path} -> {data.target_path}")
    return SuccessResponse(msg="复制文件成功")


@ResourceRouter.post(
    "/rename", 
    summary="重命名文件", 
    description="重命名文件或目录",
    dependencies=[Depends(AuthPermission(["monitor:resource:rename"]))]
)
async def rename_file_controller(
    data: ResourceRenameSchema
) -> JSONResponse:
    """重命名文件"""
    await ResourceService.rename_file_service(data=data)
    logger.info(f"重命名文件成功: {data.old_path} -> {data.new_name}")
    return SuccessResponse(msg="重命名文件成功")


@ResourceRouter.post(
    "/create-dir", 
    summary="创建目录", 
    description="在指定路径创建新目录",
    dependencies=[Depends(AuthPermission(["monitor:resource:create_dir"]))]
)
async def create_directory_controller(
    data: ResourceCreateDirSchema
) -> JSONResponse:
    """创建目录"""
    await ResourceService.create_directory_service(data=data)
    logger.info(f"创建目录成功: {data.parent_path}/{data.dir_name}")
    return SuccessResponse(msg="创建目录成功")


@ResourceRouter.post(
    "/export", 
    summary="导出资源列表", 
    description="导出资源列表",
    dependencies=[Depends(AuthPermission(["monitor:resource:export"]))]
)
async def export_resource_list_controller(
    request: Request,
    search: ResourceSearchQueryParam = Depends()
) -> StreamingResponse:
    """导出资源列表"""
    # 获取搜索结果
    result_dict_list = await ResourceService.get_resources_list_service(
        search=search,
        base_url=str(request.base_url)
    )
    export_result = await ResourceService.export_resource_service(data_list=result_dict_list)
    
    logger.info("导出资源列表成功")
    return StreamResponse(
        data=bytes2file_response(export_result),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={
            'Content-Disposition': 'attachment; filename=resource_list.xlsx'
        }
    )