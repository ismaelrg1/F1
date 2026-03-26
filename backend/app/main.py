from fastapi import FastAPI
from app.api.v1.api import api_router
from app.core.config import settings
from app.db.schema import Base
from app.db.session import engine
from app.core.logging import setup_logging


setup_logging()
Base.metadata.create_all(bind=engine)


app = FastAPI(title=settings.app_name, version="0.1.0")

app.include_router(api_router, prefix="/api/v1")


@app.get("/api/v1/health", tags=["health"])
def healthcheck() -> dict:
    return {"status": "ok", "env": settings.app_env}
