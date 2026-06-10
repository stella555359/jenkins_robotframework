from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import router as api_router
from app.core.config import settings
from app.repositories.ai_analysis_repository import initialize_ai_analysis_repository
from app.repositories.run_repository import initialize_run_repository


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_run_repository()
    initialize_ai_analysis_repository()
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.include_router(api_router, prefix="/api")
