from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    countries,
    admin,
    health
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(countries.router, prefix="/countries", tags=["countries"])
api_router.include_router(health.router, tags=["health"])


api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
