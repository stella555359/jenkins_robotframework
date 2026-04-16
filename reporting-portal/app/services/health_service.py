from app.core.config import settings


def get_health_payload() -> dict:
    return {
        "status": "ok",
        "service": "reporting-portal",
        "environment": settings.app_env,
    }
