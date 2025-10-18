# -*- coding: utf-8 -*-

from typing import Any, Dict, List, Optional
from pydantic import ConfigDict, Field, BaseModel
from pydantic.alias_generators import to_camel

from app.common.constant import RET
from app.core.exceptions import CustomException


class PageResultSchema(BaseModel):
    """分页查询结果模型"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    page_no: Optional[int] = Field(default=None, ge=1, description="页码，默认为1")
    page_size: Optional[int] = Field(default=None, ge=1, description="页面大小，默认为10") 
    total: int = Field(default=0, ge=0, description="总记录数")
    has_next: Optional[bool] = Field(default=False, description="是否有下一页")
    items: Optional[List[Any]] = Field(default_factory=list, description="分页后的数据列表")


class PaginationService:
    """分页服务类"""

    @staticmethod
    async def paginate(data_list: List[Any], page_no: Optional[int] = None, page_size: Optional[int] = None) -> Dict[str, Any]:
        """
        分页数据处理。
        输入数据列表和分页信息，返回分页或非分页数据列表结果。
        未传入 page_no 和 page_size 时，返回全部数据。

        参数:
        - data_list (List[Any]): 原始数据列表。
        - page_no (int | None): 当前页码，默认 None。
        - page_size (int | None): 每页数据量，默认 None。

        返回:
        - Dict[str, Any]: 分页或非分页数据对象。

        异常:
        - CustomException: 当分页参数不合法时抛出。
        """
        total = len(data_list)

        # 如果page_no和page_size都为None,返回全部数据
        if page_no is None or page_size is None:
            return {
                "items": data_list,
                "total": total,
                "page_no": None,
                "page_size": None,
                "has_next": False
            }

        # 验证分页参数
        if page_no < 1 or page_size < 1:
            raise CustomException(code=RET.ERROR.code, msg="分页参数不合法")
        
        # 计算起始索引和结束索引
        start = (page_no - 1) * page_size
        end = min(start + page_size, total)

        # 根据计算得到的起始索引和结束索引对数据列表进行切片
        paginated_data = data_list[start:end]

        # 判断是否有下一页
        has_next = end < total

        return {
            "items": paginated_data,
            "total": total,
            "page_no": page_no,
            "page_size": page_size,
            "has_next": has_next
        }