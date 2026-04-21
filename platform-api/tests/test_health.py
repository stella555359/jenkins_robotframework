from app.services.health_service import get_health_payload


def test_health_payload_contains_expected_fields() -> None:
    payload = get_health_payload()

    assert payload["status"] == "ok"
    assert payload["service"] == "Platform API"
    assert "environment" in payload
