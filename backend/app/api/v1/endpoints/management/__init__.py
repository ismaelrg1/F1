from fastapi import APIRouter

from . import official_results

router = APIRouter()
router.include_router(official_results.router)

__all__ = ["router"]