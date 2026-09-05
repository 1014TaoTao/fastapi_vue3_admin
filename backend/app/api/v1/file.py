"""file 路由清单：仅聚合路由，不含业务逻辑。"""

from fastapi import APIRouter

from app.modules.file.file.controller import FileRouter

file_router = APIRouter(prefix="/file")

file_router.include_router(FileRouter)
