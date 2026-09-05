from fastapi import APIRouter

from app.modules.system.auth.controller import AuthRouter
from app.modules.system.dept.controller import DeptRouter
from app.modules.system.dict.controller import DictRouter
from app.modules.system.log.controller import LogRouter
from app.modules.system.menu.controller import MenuRouter
from app.modules.system.notice.controller import NoticeRouter
from app.modules.system.params.controller import ParamsRouter
from app.modules.system.position.controller import PositionRouter
from app.modules.system.role.controller import RoleRouter
from app.modules.system.ticket.controller import TicketRouter
from app.modules.system.user.controller import UserRouter
from app.modules.system.versions.controller import VersionRouter

system_router = APIRouter(prefix="/system")

system_router.include_router(AuthRouter)
system_router.include_router(DeptRouter)
system_router.include_router(DictRouter)
system_router.include_router(LogRouter)
system_router.include_router(MenuRouter)
system_router.include_router(NoticeRouter)
system_router.include_router(ParamsRouter)
system_router.include_router(PositionRouter)
system_router.include_router(RoleRouter)
system_router.include_router(TicketRouter)
system_router.include_router(UserRouter)
system_router.include_router(VersionRouter)
