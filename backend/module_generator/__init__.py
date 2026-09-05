from fastapi import APIRouter

from .gencode.controller import GenRouter

generator_router = APIRouter(prefix="/generator")

generator_router.include_router(GenRouter)
