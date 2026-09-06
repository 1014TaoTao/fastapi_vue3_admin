from collections.abc import Sequence
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import CRUDBase
from app.core.base_schema import AuthSchema

from .model import JobModel
from .schema import JobCreateSchema, JobUpdateSchema


class JobCRUD(CRUDBase[JobModel, JobCreateSchema, JobUpdateSchema]):
    """任务执行日志数据层"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        """初始化任务执行日志CRUD

        参数:
        - auth (AuthSchema): 认证信息模型
        - db (AsyncSession): 数据库会话
        """
        super().__init__(model=JobModel, auth=auth, db=db)

    async def get_obj_by_id_crud(self, id: int, preload: list[str | Any] | None = None) -> JobModel | None:
        """获取执行日志详情

        参数:
        - id (int): 日志ID
        - preload (list[str | Any] | None): 预加载关系，未提供时使用模型默认项

        返回:
        - JobModel | None: 执行日志模型,如果不存在则为None
        """
        return await self.get(id=id, preload=preload)

    async def get_obj_list_crud(
        self,
        search: dict | None = None,
        order_by: list[dict[str, str]] | None = None,
        preload: list[str | Any] | None = None,
    ) -> Sequence[JobModel]:
        """获取执行日志列表

        参数:
        - search (dict | None): 查询参数字典
        - order_by (list[dict[str, str]] | None): 排序参数列表
        - preload (list[str | Any] | None): 预加载关系，未提供时使用模型默认项

        返回:
        - Sequence[JobModel]: 执行日志模型序列
        """
        return await self.get_list(search=search, order_by=order_by, preload=preload)

    async def create_obj_crud(self, data: JobCreateSchema) -> JobModel | None:
        """创建执行日志

        参数:
        - data (JobCreateSchema): 创建执行日志模型

        返回:
        - JobModel | None: 创建的执行日志模型,如果创建失败则为None
        """
        return await self.create(data=data)

    async def update_obj_crud(self, id: int, data: JobUpdateSchema) -> JobModel | None:
        """更新执行日志

        参数:
        - id (int): 日志ID
        - data (JobUpdateSchema): 更新执行日志模型

        返回:
        - JobModel | None: 更新后的执行日志模型,如果更新失败则为None
        """
        return await self.update(id=id, data=data)

    async def delete_obj_crud(self, ids: list[int]) -> None:
        """删除执行日志

        参数:
        - ids (list[int]): 日志ID列表

        返回:
        - None
        """
        return await self.delete(ids=ids)

    async def clear_obj_crud(self) -> None:
        """清空所有执行日志。

        返回:
        - None
        """
        return await self.clear()
