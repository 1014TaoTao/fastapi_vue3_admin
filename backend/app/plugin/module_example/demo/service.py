from collections.abc import Sequence
from typing import Any

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_schema import AuthSchema, BatchSetAvailable, PageResultSchema
from app.core.exceptions import CustomException
from app.core.logger import logger
from app.utils.common_util import search_to_dict
from app.utils.excel_util import ExcelUtil

from .crud import DemoCRUD
from .model import DemoModel
from .schema import (
    DemoCreateSchema,
    DemoOutSchema,
    DemoQueryParam,
    DemoUpdateSchema,
)


class DemoService:
    """示例管理模块服务层"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        self.auth = auth
        self.db = db

    async def detail(self, id: int) -> DemoOutSchema:
        """获取示例详情

        参数:
        - id (int): 示例 ID

        返回:
        - DemoOutSchema: 示例响应模型
        """
        obj = await DemoCRUD(self.auth, self.db).get(id=id)
        if not obj:
            raise CustomException(msg="该数据不存在")
        return DemoOutSchema.model_validate(obj)

    async def get_list(
        self,
        search: DemoQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> list[DemoOutSchema]:
        """获取示例列表（不分页）

        参数:
        - search (DemoQueryParam | None): 查询参数
        - order_by (list[dict[str, str]] | None): 排序规则

        返回:
        - list[DemoOutSchema]: 示例列表
        """
        obj_list: Sequence[DemoModel] = await DemoCRUD(self.auth, self.db).get_list(search=search_to_dict(search), order_by=order_by)
        return [DemoOutSchema.model_validate(obj) for obj in obj_list]

    async def page(
        self,
        page_no: int,
        page_size: int,
        search: DemoQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> PageResultSchema[DemoOutSchema]:
        """分页查询示例

        参数:
        - page_no (int): 当前页码
        - page_size (int): 每页条数
        - search (DemoQueryParam | None): 查询参数
        - order_by (list[dict[str, str]] | None): 排序规则

        返回:
        - PageResultSchema[DemoOutSchema]: 分页结果
        """
        offset = (page_no - 1) * page_size
        return await DemoCRUD(self.auth, self.db).page(
            offset=offset,
            limit=page_size,
            order_by=order_by or [{"id": "asc"}],
            search=search_to_dict(search, {}),
            out_schema=DemoOutSchema,
        )

    async def create(self, data: DemoCreateSchema) -> DemoOutSchema:
        """创建示例

        参数:
        - data (DemoCreateSchema): 示例创建模型

        返回:
        - DemoOutSchema: 示例响应模型
        """
        obj: DemoModel | None = await DemoCRUD(self.auth, self.db).get(name=data.name)
        if obj:
            raise CustomException(msg="创建失败，名称已存在")
        obj = await DemoCRUD(self.auth, self.db).create(data=data)
        return DemoOutSchema.model_validate(obj)

    async def update(self, id: int, data: DemoUpdateSchema) -> DemoOutSchema:
        """更新示例

        参数:
        - id (int): 示例 ID
        - data (DemoUpdateSchema): 示例更新模型

        返回:
        - DemoOutSchema: 示例响应模型
        """
        obj: DemoModel | None = await DemoCRUD(self.auth, self.db).get(id=id)
        if not obj:
            raise CustomException(msg="更新失败，该数据不存在")

        exist_obj: DemoModel | None = await DemoCRUD(self.auth, self.db).get(name=data.name)
        if exist_obj and exist_obj.id != id:
            raise CustomException(msg="更新失败，名称重复")

        obj = await DemoCRUD(self.auth, self.db).update(id=id, data=data)
        return DemoOutSchema.model_validate(obj)

    async def delete(self, ids: list[int]) -> None:
        """批量删除示例

        参数:
        - ids (list[int]): 示例 ID 列表
        """
        if not ids:
            raise CustomException(msg="删除失败，删除对象不能为空")
        objs: Sequence[DemoModel] = await DemoCRUD(self.auth, self.db).get_list(search={"id": ("in", ids)})
        obj_map: dict[int, DemoModel] = {o.id: o for o in objs}
        for id_ in ids:
            if id_ not in obj_map:
                raise CustomException(msg="删除失败，该数据不存在")
        await DemoCRUD(self.auth, self.db).delete(ids=ids)

    async def set_available(self, data: BatchSetAvailable) -> None:
        """批量启用/停用示例

        参数:
        - data (BatchSetAvailable): 批量设置状态模型
        """
        await DemoCRUD(self.auth, self.db).set(ids=data.ids, status=data.status)

    @staticmethod
    async def batch_export(obj_list: list[dict[str, Any]]) -> bytes:
        """批量导出示例为 Excel 字节流

        参数:
        - obj_list (list[dict[str, Any]]): 示例数据字典列表

        返回:
        - bytes: Excel 文件字节流
        """
        mapping_dict: dict[str, str] = {
            "id": "编号",
            "name": "名称",
            "status": "状态",
            "description": "备注",
            "created_time": "创建时间",
            "updated_time": "更新时间",
            "created_id": "创建者",
        }

        data = obj_list.copy()
        for item in data:
            item["status"] = "正常" if item.get("status") == 0 else "停用"
            creator_info = item.get("created_id")
            if isinstance(creator_info, dict):
                item["created_id"] = creator_info.get("name", "未知")
            else:
                item["created_id"] = "未知"

        return await ExcelUtil.aexport_list2excel(list_data=data, mapping_dict=mapping_dict)

    async def batch_import(self, file: UploadFile, update_support: bool = False) -> str:
        """从 Excel 批量导入示例

        参数:
        - file (UploadFile): 上传的 Excel 文件
        - update_support (bool): 数据已存在时是否按名称更新

        返回:
        - str: 导入结果描述（含成功条数与逐行错误信息）
        """
        header_dict: dict[str, str] = {"名称": "name", "状态": "status", "描述": "description"}

        try:
            contents: bytes = await file.read()
            rows: list[dict[str, Any]] = await ExcelUtil.aread_excel_to_dicts(contents)
            await file.close()

            if not rows:
                raise CustomException(msg="导入文件为空")

            missing_headers = [h for h in header_dict if h not in rows[0]]
            if missing_headers:
                raise CustomException(msg=f"导入文件缺少必要的列: {', '.join(missing_headers)}")

            # 将中文字段名映射为英文字段
            mapped_rows: list[dict[str, Any]] = []
            for row in rows:
                mapped_rows.append({en: row.get(ch) for ch, en in header_dict.items()})

            required_fields: list[str] = ["name", "status"]
            errors: list[str] = []
            for field in required_fields:
                missing_indices: list[int] = [i + 1 for i, r in enumerate(mapped_rows) if r.get(field) is None]
                if missing_indices:
                    field_name: str = next(k for k, v in header_dict.items() if v == field)
                    rows_str: str = "、".join(str(i) for i in missing_indices)
                    errors.append(f"{field_name}不能为空，第{rows_str}行")
            if errors:
                raise CustomException(msg=f"导入失败，以下行缺少必要字段：\n{'; '.join(errors)}")

            error_msgs: list[str] = []
            success_count = 0

            for i, row in enumerate(mapped_rows, start=1):
                try:
                    status_str = str(row["status"]).strip()
                    if status_str == "正常":
                        status = 0
                    elif status_str == "停用":
                        status = 1
                    else:
                        error_msgs.append(f"第{i}行: 状态必须是'正常'或'停用'")
                        continue

                    create_data = DemoCreateSchema(
                        name=str(row["name"]),
                        status=status,
                        description=str(row["description"] or ""),
                    )

                    exists_obj: DemoModel | None = await DemoCRUD(self.auth, self.db).get(name=create_data.name)
                    if exists_obj:
                        if update_support:
                            update_data = DemoUpdateSchema(
                                name=create_data.name,
                                status=create_data.status,
                                description=create_data.description,
                            )
                            await DemoCRUD(self.auth, self.db).update(id=exists_obj.id, data=update_data)
                            success_count += 1
                        else:
                            error_msgs.append(f"第{i}行: 对象 {create_data.name} 已存在")
                    else:
                        await DemoCRUD(self.auth, self.db).create(data=create_data)
                        success_count += 1

                except Exception as e:
                    error_msgs.append(f"第{i}行: {e!s}")
                    continue

            result = f"成功导入 {success_count} 条数据"
            if error_msgs:
                result += "\n错误信息:\n" + "\n".join(error_msgs)
            return result

        except Exception as e:
            logger.error(f"批量导入示例失败: {e!s}")
            raise CustomException(msg=f"导入失败: {e!s}") from e

    @staticmethod
    def import_template_download() -> bytes:
        """生成示例导入模板 Excel 字节流

        返回:
        - bytes: Excel 模板文件字节流
        """
        header_list: list[str] = ["名称", "状态", "描述"]
        selector_header_list: list[str] = ["状态"]
        option_list: list[dict[str, list[str]]] = [{"状态": ["正常", "停用"]}]
        return ExcelUtil.get_excel_template(
            header_list=header_list,
            selector_header_list=selector_header_list,
            option_list=option_list,
        )
