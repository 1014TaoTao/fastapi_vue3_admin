from pydantic import BaseModel, Field


class StorageUploadResultSchema(BaseModel):
    """上传结果"""

    file_path: str = Field(..., description="远端路径")
    file_name: str = Field(..., description="远端文件名")
    origin_name: str = Field(..., description="原始文件名")
    file_url: str | None = Field(default=None, description="访问链接")


class StoragePathResultSchema(BaseModel):
    """路径操作结果（复制/移动/重命名）"""

    source_path: str = Field(..., description="源路径")
    target_path: str = Field(..., description="目标路径")


class StoragePathCreateSchema(BaseModel):
    """新建目录结果"""

    path: str = Field(..., description="目录路径")
