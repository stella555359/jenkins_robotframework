from app.core.config import settings


def get_health_payload() -> dict:
    return {
        "status": "ok",
        "service": "kpi-portal",
        "environment": settings.app_env,
    }
