from fastapi import APIRouter

from app.modules.common.file.controller import FileRouter

file_router = APIRouter()

file_router.include_router(FileRouter)
