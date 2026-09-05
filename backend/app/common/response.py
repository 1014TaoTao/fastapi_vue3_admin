from collections.abc import Mapping
from datetime import date, datetime, time
from typing import Any

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, StreamingResponse
from pydantic import BaseModel, Field
from starlette.background import BackgroundTask

from app.common.constant import DATE_DISPLAY_FMT, DATETIME_DISPLAY_FMT, TIME_DISPLAY_FMT
from app.common.enums import RET

# 裸 datetime/date/time（未走 Pydantic 的 dict 等）JSON 输出与 constant 中展示格式一致
_JSON_DATETIME_CUSTOM_ENCODER: dict[type[Any], Any] = {
    datetime: lambda d: d.strftime(DATETIME_DISPLAY_FMT),
    date: lambda d: d.strftime(DATE_DISPLAY_FMT),
    time: lambda t: t.strftime(TIME_DISPLAY_FMT),
}


def jsonable_response_content(content: Any) -> Any:
    return jsonable_encoder(content, custom_encoder=_JSON_DATETIME_CUSTOM_ENCODER)


class ResponseSchema[T](BaseModel):
    """响应模型"""

    code: int = Field(default=RET.OK.code, description="业务状态码")
    msg: str = Field(default=RET.OK.msg, description="响应消息")
    data: T | None = Field(default=None, description="响应数据")
    status_code: int = Field(default=status.HTTP_200_OK, description="HTTP状态码")
    success: bool = Field(default=True, description="操作是否成功")


class SuccessResponse(JSONResponse):
    """成功响应类"""

    def __init__(
        self,
        data: Any | None = None,
        msg: str = RET.OK.msg,
        code: int = RET.OK.code,
        status_code: int = status.HTTP_200_OK,
        success: bool = True,
    ) -> None:
        """初始化成功响应类

        参数:
        - data (Any | None): 响应数据。
        - msg (str): 响应消息。
        - code (int): 业务状态码。
        - status_code (int): HTTP 状态码。
        - success (bool): 操作是否成功。

        返回:
        - None
        """
        content = ResponseSchema(
            code=code,
            msg=msg,
            data=data,
            status_code=status_code,
            success=success,
        ).model_dump()
        super().__init__(content=jsonable_response_content(content), status_code=status_code)
        self.headers["Content-Type"] = "application/json; charset=utf-8"


class ErrorResponse(JSONResponse):
    """错误响应类"""

    def __init__(
        self,
        data: Any = None,
        msg: str = RET.ERROR.msg,
        code: int = RET.ERROR.code,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        success: bool = False,
    ) -> None:
        """初始化错误响应类

        参数:
        - data (Any): 响应数据。
        - msg (str): 响应消息。
        - code (int): 业务状态码。
        - status_code (int): HTTP 状态码。
        - success (bool): 操作是否成功。

        返回:
        - None
        """
        content = ResponseSchema(
            code=code,
            msg=msg,
            data=data,
            status_code=status_code,
            success=success,
        ).model_dump()
        super().__init__(content=jsonable_response_content(content), status_code=status_code)
        self.headers["Content-Type"] = "application/json; charset=utf-8"


class StreamResponse(StreamingResponse):
    """流式响应类"""

    def __init__(
        self,
        data: Any = None,
        status_code: int = status.HTTP_200_OK,
        headers: Mapping[str, str] | None = None,
        media_type: str | None = None,
        background: BackgroundTask | None = None,
    ) -> None:
        """初始化流式响应类

        参数:
        - data (Any): 响应数据。
        - status_code (int): HTTP 状态码。
        - headers (Mapping[str, str] | None): 响应头。
        - media_type (str | None): 媒体类型。
        - background (BackgroundTask | None): 后台任务。

        返回:
        - None
        """
        super().__init__(
            content=data,
            status_code=status_code,
            media_type=media_type,  # 文件类型
            headers=headers,  # 文件名
            background=background,  # 文件大小
        )


class RedirectContentResponse(RedirectResponse):
    """重定向响应类"""

    def __init__(
        self,
        url: str,
        status_code: int = status.HTTP_302_FOUND,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        """初始化重定向响应类

        参数:
        - url (str): 重定向目标 URL。
        - status_code (int): HTTP 状态码（默认 302）。
        - headers (Mapping[str, str] | None): 响应头。

        返回:
        - None
        """
        super().__init__(url=url, status_code=status_code, headers=headers)


class UploadFileResponse(FileResponse):
    """文件响应
    """

    def __init__(
        self,
        file_path: str,
        filename: str,
        media_type: str = "application/octet-stream",
        headers: Mapping[str, str] | None = None,
        background: BackgroundTask | None = None,
        status_code: int = 200,
    ) -> None:
        """初始化文件响应类

        参数:
        - file_path (str): 文件路径。
        - filename (str): 文件名。
        - media_type (str): 文件类型。
        - headers (Mapping[str, str] | None): 响应头。
        - background (BackgroundTask | None): 后台任务。
        - status_code (int): HTTP 状态码。

        返回:
        - None
        """
        super().__init__(
            path=file_path,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
            background=background,
            filename=filename,
            stat_result=None,
            method=None,
            content_disposition_type="attachment",
        )
