import allure

from fastapi.testclient import TestClient


@allure.feature("Health API")
@allure.story("Health check")
@allure.title("GET /api/health returns the expected health payload")
def test_health_payload_contains_expected_fields(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["service"] == "Platform API"
    assert "environment" in payload
