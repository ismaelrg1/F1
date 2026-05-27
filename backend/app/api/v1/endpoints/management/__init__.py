from fastapi import APIRouter

from . import official_results, calendar

router = APIRouter()
router.include_router(official_results.router)
router.include_router(calendar.router)

__all__ = ["router"]