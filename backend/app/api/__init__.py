from fastapi import APIRouter
from .api import router as api_router
from .orchestrator import router as orchestrator_router

router = APIRouter()
router.include_router(api_router, prefix="/api")
router.include_router(orchestrator_router, prefix="/orchestrator")

__all__ = ["router"]
