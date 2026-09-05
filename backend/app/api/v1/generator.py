from fastapi import APIRouter

from app.modules.generator.gencode.controller import GenRouter

generator_router = APIRouter(prefix="/generator")

generator_router.include_router(GenRouter)
