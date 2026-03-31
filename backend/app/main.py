from fastapi import FastAPI
from app.api.v1.api import api_router
from app.core.config import settings
from app.db.schema import Base
from app.db.session import engine
from app.core.logging import setup_logging


setup_logging()
Base.metadata.create_all(bind=engine)


is_production = settings.app_env.lower() == "production"

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
)

app.include_router(api_router, prefix="/api/v1")

