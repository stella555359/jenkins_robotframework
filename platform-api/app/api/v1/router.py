from fastapi import APIRouter

from app.schemas.health import HealthResponse
from app.services.run_service import run_create
from app.services.health_service import get_health_payload
from app.schemas.run import RunCreateRequest, RunCreateResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["health"])
def get_health() -> HealthResponse:
    return HealthResponse(**get_health_payload())

@router.post("/runs", response_model=RunCreateResponse, tags=["run"])
def create_run(request: RunCreateRequest) -> RunCreateResponse:
    return run_create(request)

