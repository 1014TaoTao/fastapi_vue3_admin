import os

from fastapi import UploadFile

from app.config.setting import settings
from app.core.base_schema import DownloadFileSchema, UploadResponseSchema
from app.core.exceptions import CustomException
from app.core.logger import logger
from app.utils.upload_util import UploadUtil


class FileService:
    """文件管理服务层
    """

    @classmethod
    async def upload_service(
        cls,
        base_url: str,
        file: UploadFile,
        upload_type: str = "file",
        target_path: str | None = None,
    ) -> UploadResponseSchema:
        """上传文件"""

        filename, filepath, file_url = await UploadUtil.upload_file(
            file=file,
            base_url=base_url,
            upload_type=upload_type,
            target_path=target_path,
        )

        return UploadResponseSchema(
            file_path=f"{filepath}",
            file_name=filename,
            origin_name=file.filename,
            file_url=f"{file_url}",
        )

    @classmethod
    async def download_service(cls, file_path: str) -> DownloadFileSchema:
        """下载文件"""
        if not file_path:
            raise CustomException(msg="请选择要下载的文件")

        dangerous_patterns = ["../", "..\\", "\0"]
        for pattern in dangerous_patterns:
            if pattern in file_path:
                logger.error(f"检测到路径穿越攻击: {file_path}")
                raise CustomException(msg="非法的文件路径")

        upload_root = settings.UPLOAD_FILE_PATH.resolve()
        abs_path = os.path.normpath(os.path.abspath(file_path))

        if not abs_path.startswith(str(upload_root)):
            logger.error(f"路径不在上传目录内: {file_path}")
            raise CustomException(msg="非法的文件路径")

        if not UploadUtil.check_file_exists(abs_path):
            raise CustomException(msg="文件不存在")

        file_name = UploadUtil.download_file(abs_path)

        return DownloadFileSchema(
            file_path=abs_path,
            file_name=str(file_name),
        )
