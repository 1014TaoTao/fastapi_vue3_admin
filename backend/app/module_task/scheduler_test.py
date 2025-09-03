# -*- coding: utf-8 -*-

import time
from datetime import datetime

from app.core.logger import logger

def job(*args, **kwargs):
    """
    定时任务执行同步函数示例
    """
    try:
        print(f"开始执行任务: {args}-{kwargs}")
        time.sleep(3)
        print(f'{datetime.now()}同步函数执行完成')
    except Exception as e:
        logger.error(f"同步任务执行失败: {e}")
        raise

async def async_job(*args, **kwargs):
    """
    定时任务执行异步函数示例
    """
    try:
        print(f"开始执行任务: {args}-{kwargs}")
        time.sleep(3)
        print(f'{datetime.now()}异步函数执行完成')
    except Exception as e:
        logger.error(f"异步任务执行失败: {e}")
        raise

