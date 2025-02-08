from fastapi import APIRouter
from .login import router as login_router
from .register import router as register_router
from .project import router as project_router
from .todo import router as todo_router
from .team import router as team_router
from .twofa import router as twofa_router
from .password_reset import router as password_reset_router

router = APIRouter()
router.include_router(login_router, tags=["auth"])
router.include_router(register_router, tags=["auth"])
router.include_router(project_router, tags=["dashboard"])
router.include_router(todo_router, tags=["dashboard"])
router.include_router(team_router, tags=["dashboard"])
router.include_router(twofa_router, tags=["2FA"])
router.include_router(password_reset_router, tags=["auth"])
