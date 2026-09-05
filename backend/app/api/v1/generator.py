"""generator 路由清单：仅聚合路由，不含业务逻辑。"""

from fastapi import APIRouter

from app.modules.generator.gencode.controller import GenRouter

generator_router = APIRouter(prefix="/generator")

generator_router.include_router(GenRouter)
