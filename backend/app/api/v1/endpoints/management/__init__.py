from fastapi import APIRouter

from . import official_results, calendar, result_publications

router = APIRouter()
router.include_router(official_results.router)
router.include_router(calendar.router)
router.include_router(result_publications.router)

__all__ = ["router"]