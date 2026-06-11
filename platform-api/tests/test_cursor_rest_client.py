import json
from unittest.mock import MagicMock, patch

import pytest

from app.services.cursor_rest_client import (
    CursorApiError,
    create_cloud_agent,
    get_me,
    prompt_cloud_no_repo,
    wait_for_run,
)


def _mock_response(payload: dict, *, status: int = 200) -> MagicMock:
    body = json.dumps(payload).encode("utf-8")
    response = MagicMock()
    response.read.return_value = body
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


@patch("app.services.cursor_rest_client._build_opener")
def test_get_me_returns_payload(mock_build_opener: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CURSOR_API_KEY", "crsr_test_key")
    opener = MagicMock()
    opener.open.return_value = _mock_response({"apiKeyName": "smoke", "userEmail": "dev@example.com"})
    mock_build_opener.return_value = opener

    payload = get_me()

    assert payload["apiKeyName"] == "smoke"
    request = opener.open.call_args.args[0]
    assert request.full_url.endswith("/v1/me")
    assert request.get_method() == "GET"


@patch("app.services.cursor_rest_client.wait_for_run")
@patch("app.services.cursor_rest_client.create_cloud_agent")
def test_prompt_cloud_no_repo_returns_result_text(
    mock_create: MagicMock,
    mock_wait: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CURSOR_API_KEY", "crsr_test_key")
    mock_create.return_value = {
        "agent": {"id": "bc-agent-1", "latestRunId": "run-1"},
        "run": {"id": "run-1", "status": "CREATING"},
    }
    mock_wait.return_value = {
        "id": "run-1",
        "status": "FINISHED",
        "result": '{"log_summary": {"one_line_summary": "ok"}}',
    }

    result = prompt_cloud_no_repo("analyze this")

    assert "log_summary" in result
    mock_create.assert_called_once()
    mock_wait.assert_called_once_with("bc-agent-1", "run-1")


@patch("app.services.cursor_rest_client._build_opener")
def test_create_cloud_agent_maps_403(mock_build_opener: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CURSOR_API_KEY", "crsr_test_key")
    import urllib.error

    opener = MagicMock()
    error = urllib.error.HTTPError(
        url="https://api.cursor.com/v1/agents",
        code=403,
        msg="Forbidden",
        hdrs=None,
        fp=MagicMock(read=MagicMock(return_value=b'{"code":"feature_unavailable","message":"unauthenticated"}')),
    )
    opener.open.side_effect = error
    mock_build_opener.return_value = opener

    with pytest.raises(CursorApiError) as exc_info:
        create_cloud_agent("hello")

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "feature_unavailable"


@patch("app.services.cursor_rest_client.get_run")
@patch("app.services.cursor_rest_client.time.sleep", return_value=None)
@patch("app.services.cursor_rest_client.time.monotonic")
def test_wait_for_run_polls_until_finished(
    mock_monotonic: MagicMock,
    _mock_sleep: MagicMock,
    mock_get_run: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CURSOR_API_KEY", "crsr_test_key")
    mock_monotonic.side_effect = [0.0, 1.0, 2.0]
    mock_get_run.side_effect = [
        {"status": "RUNNING"},
        {"status": "FINISHED", "result": "done"},
    ]

    run = wait_for_run("bc-agent-1", "run-1")

    assert run["status"] == "FINISHED"
    assert mock_get_run.call_count == 2
