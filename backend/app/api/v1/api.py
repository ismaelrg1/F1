from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    admin,
    health,
    home,
    calendar,
    bets
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(health.router, tags=["health"])
api_router.include_router(home.router, tags=["home"])
api_router.include_router(calendar.router, tags=["calendar"])
api_router.include_router(bets.router, prefix="/bets", tags=["bets"])


api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
