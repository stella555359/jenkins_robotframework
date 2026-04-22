from fastapi import APIRouter

from app.schemas.health import HealthResponse
from app.services.run_service import get_run_detail, get_run_list, run_create
from app.services.health_service import get_health_payload
from app.schemas.run import (
    RunCreateRequest,
    RunCreateResponse,
    RunDetailResponse,
    RunListResponse,
)

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["health"])
def get_health() -> HealthResponse:
    return HealthResponse(**get_health_payload())

@router.post("/runs", response_model=RunCreateResponse, tags=["run"])
def create_run(request: RunCreateRequest) -> RunCreateResponse:
    return run_create(request)


@router.get("/runs", response_model=RunListResponse, tags=["run"])
def list_runs() -> RunListResponse:
    return get_run_list()


@router.get("/runs/{run_id}", response_model=RunDetailResponse, tags=["run"])
def get_run(run_id: str) -> RunDetailResponse:
    return get_run_detail(run_id)

