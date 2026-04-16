from app.services.health_service import get_health_payload


def test_health_payload_shape() -> None:
    payload = get_health_payload()

    assert payload["status"] == "ok"
    assert payload["service"] == "kpi-portal"
