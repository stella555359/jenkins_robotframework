import json
import os
import ssl
import time
import urllib.error
import urllib.request
from base64 import b64encode
from typing import Any

from app.core.config import settings

TERMINAL_RUN_STATUSES = frozenset({"FINISHED", "ERROR", "CANCELLED", "EXPIRED"})


class CursorApiError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        code: str | None = None,
        is_retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.is_retryable = is_retryable


def _api_key() -> str:
    key = os.environ.get("CURSOR_API_KEY", "").strip()
    if not key:
        raise CursorApiError("CURSOR_API_KEY is not configured for AI analysis worker.")
    return key


def _proxy_url() -> str | None:
    if not settings.cursor_api_use_proxy:
        return None
    return (
        os.environ.get("HTTPS_PROXY")
        or os.environ.get("https_proxy")
        or os.environ.get("HTTP_PROXY")
        or os.environ.get("http_proxy")
        or ""
    ).strip() or None


def _build_opener() -> urllib.request.OpenerDirector:
    handlers: list[Any] = []
    proxy = _proxy_url()
    if proxy:
        handlers.append(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
    if settings.cursor_api_insecure_tls:
        handlers.append(urllib.request.HTTPSHandler(context=ssl._create_unverified_context()))
    return urllib.request.build_opener(*handlers)


def _request(
    method: str,
    path: str,
    *,
    body: dict[str, Any] | None = None,
    timeout: int | None = None,
) -> dict[str, Any]:
    api_key = _api_key()
    url = f"{settings.cursor_api_base_url.rstrip('/')}{path}"
    headers = {
        "Authorization": "Basic " + b64encode(f"{api_key}:".encode("ascii")).decode("ascii"),
        "Accept": "application/json",
    }
    data: bytes | None = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    opener = _build_opener()
    try:
        with opener.open(request, timeout=timeout or settings.cursor_api_timeout_seconds) as response:
            payload = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="ignore")
        parsed: dict[str, Any] = {}
        if error_body:
            try:
                parsed = json.loads(error_body)
            except json.JSONDecodeError:
                parsed = {"message": error_body}
        message = str(parsed.get("message") or parsed.get("error") or exc.reason or error_body or exc)
        code = str(parsed.get("code") or "")
        is_retryable = bool(parsed.get("isRetryable") or parsed.get("is_retryable") or False)
        raise CursorApiError(
            message,
            status_code=exc.code,
            code=code or None,
            is_retryable=is_retryable,
        ) from exc
    except urllib.error.URLError as exc:
        raise CursorApiError(f"Cursor API network error: {exc.reason}") from exc

    if not payload.strip():
        return {}
    return json.loads(payload)


def get_me() -> dict[str, Any]:
    return _request("GET", "/v1/me")


def list_models() -> dict[str, Any]:
    return _request("GET", "/v1/models")


def create_cloud_agent(prompt_text: str, *, model_id: str | None = None) -> dict[str, Any]:
    body: dict[str, Any] = {
        "prompt": {"text": prompt_text},
    }
    model = (model_id or settings.ai_analysis_model or "auto").strip()
    if model and model != "auto":
        body["model"] = {"id": model}
    return _request("POST", "/v1/agents", body=body, timeout=settings.cursor_api_timeout_seconds)


def get_run(agent_id: str, run_id: str) -> dict[str, Any]:
    return _request("GET", f"/v1/agents/{agent_id}/runs/{run_id}")


def wait_for_run(agent_id: str, run_id: str) -> dict[str, Any]:
    deadline = time.monotonic() + settings.cursor_api_run_timeout_seconds
    while time.monotonic() < deadline:
        run = get_run(agent_id, run_id)
        status = str(run.get("status") or "").upper()
        if status in TERMINAL_RUN_STATUSES:
            return run
        time.sleep(settings.cursor_api_poll_seconds)
    raise CursorApiError(
        f"Cursor run timed out after {settings.cursor_api_run_timeout_seconds}s: agent={agent_id} run={run_id}",
        is_retryable=True,
    )


def prompt_cloud_no_repo(prompt_text: str, *, model_id: str | None = None) -> str:
    created = create_cloud_agent(prompt_text, model_id=model_id)
    agent = created.get("agent") or {}
    run = created.get("run") or {}
    agent_id = str(agent.get("id") or "").strip()
    run_id = str(run.get("id") or agent.get("latestRunId") or "").strip()
    if not agent_id or not run_id:
        raise CursorApiError(f"Cursor create agent response missing ids: {created}")

    final_run = wait_for_run(agent_id, run_id)
    status = str(final_run.get("status") or "").upper()
    result_text = str(final_run.get("result") or "").strip()
    if status == "FINISHED" and result_text:
        return result_text
    if status == "FINISHED" and not result_text:
        raise CursorApiError(f"Cursor run finished without result text: run={run_id}")
    raise CursorApiError(
        f"Cursor run ended with status={status}: {result_text or final_run}",
        code=status.lower(),
    )
