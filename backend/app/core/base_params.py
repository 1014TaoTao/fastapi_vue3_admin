# -*- coding: utf-8 -*-

from typing import Optional, List, Dict
from fastapi import Query


class PaginationQueryParam:
    """分页查询参数基类"""

    def __init__(
        self,
        page_no: Optional[int] = Query(default=None, description="当前页码", ge=1),
        page_size: Optional[int] = Query(default=None, description="每页数量", ge=1, le=100), 
        order_by: Optional[str] = Query(default=None, description="排序字段,格式:field1,asc;field2,desc"),
    ) -> None:
        """
        初始化分页查询参数
        
        :param page_no: 当前页码,默认None
        :param page_size: 每页数量,默认None,最大100
        :param order_by: 排序字段
        """
        self.page_no = page_no
        self.page_size = page_size
        # 将字符串格式的order_by转换为服务层需要的List[Dict[str, str]]格式
        if order_by:
            try:
                self.order_by = []
                for item in order_by.split(';'):
                    if item.strip():
                        field, direction = item.split(',', 1)
                        self.order_by.append({field.strip(): direction.strip().lower()})
            except ValueError:
                # 如果解析失败，使用默认排序
                self.order_by = [{'id': 'asc'}]
        else:
            self.order_by = [{'id': 'asc'}]

