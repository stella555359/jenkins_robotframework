from fastapi import APIRouter

from app.schemas.health import HealthResponse
from app.services.health_service import get_health_payload

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["health"])
def get_health() -> HealthResponse:
    return HealthResponse(**get_health_payload())
