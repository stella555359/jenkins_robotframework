from __future__ import annotations

import base64
import json
from typing import Any
from urllib import error as urllib_error
from urllib import parse, request

from app.core.config import settings


class JenkinsDispatchError(RuntimeError):
    pass


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _join_url(base_url: str, *parts: str) -> str:
    base = base_url.rstrip("/")
    suffix = "/".join(part.strip("/") for part in parts if part.strip("/"))
    return f"{base}/{suffix}" if suffix else base


def _auth_header() -> dict[str, str]:
    username = _clean_text(settings.jenkins_username)
    token = _clean_text(settings.jenkins_api_token)
    if not username or not token:
        return {}
    encoded = base64.b64encode(f"{username}:{token}".encode("utf-8")).decode("ascii")
    return {"Authorization": f"Basic {encoded}"}


def trigger_jenkins_job(*, parameters: dict[str, Any]) -> dict[str, Any]:
    base_url = _clean_text(settings.jenkins_base_url)
    if not base_url:
        raise JenkinsDispatchError("jenkins_base_url is not configured.")

    job_path = _clean_text(settings.jenkins_robot_job_path)
    if not job_path:
        raise JenkinsDispatchError("jenkins_robot_job_path is not configured.")

    request_params = {key: str(value) for key, value in parameters.items() if value is not None}
    trigger_token = _clean_text(settings.jenkins_trigger_token)
    if trigger_token:
        request_params.setdefault("token", trigger_token)

    url = _join_url(base_url, job_path, "buildWithParameters")
    body = parse.urlencode(request_params).encode("utf-8")
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        **_auth_header(),
    }
    http_request = request.Request(url, data=body, headers=headers, method="POST")

    try:
        with request.urlopen(http_request, timeout=settings.jenkins_timeout_seconds) as response:
            safe_params = dict(request_params)
            safe_params.pop("token", None)
            return {
                "url": url,
                "http_status": response.status,
                "queue_url": response.headers.get("Location"),
                "parameters": safe_params,
            }
    except urllib_error.HTTPError as exc:
        body_preview = exc.read().decode("utf-8", errors="replace")[:1000]
        raise JenkinsDispatchError(f"Jenkins trigger failed with HTTP {exc.code}: {body_preview}") from exc
    except urllib_error.URLError as exc:
        raise JenkinsDispatchError(f"Jenkins trigger failed: {exc}") from exc


def build_robot_jenkins_parameters(record: dict[str, Any]) -> dict[str, Any]:
    metadata = dict(record.get("metadata") or {})
    selected_tests = metadata.get("selected_tests") or []
    if isinstance(selected_tests, str):
        selected_tests_text = selected_tests
    else:
        selected_tests_text = "\n".join(str(item).strip() for item in selected_tests if str(item).strip())

    robot_variables = metadata.get("robot_variables") or metadata.get("variables") or {}
    if not isinstance(robot_variables, dict):
        robot_variables = {}
    if record.get("build"):
        robot_variables.setdefault("BUILD", record["build"])

    params = {
        "RUN_ID": record["run_id"],
        "TESTLINE": record["testline"],
        "ROBOTCASE_PATH": record["robotcase_path"],
        "CASE_NAME": metadata.get("case_name") or "",
        "ROBOT_SELECTED_TESTS": selected_tests_text,
        "ROBOT_VARIABLES_JSON": json.dumps(robot_variables, ensure_ascii=False),
        "PLATFORM_API_BASE_URL": metadata.get("platform_api_base_url") or settings.public_base_url,
        "TAF_MODE": metadata.get("taf_mode") or "reuse",
        "PYTHON_ENV_ROOT": metadata.get("python_env_root") or "",
        "ROBOTWS_ROOT": metadata.get("robotws_root") or "",
        "TESTLINE_VARIABLES_PATH": metadata.get("testline_variables_path") or "",
        "ROBOTWS_REPO_URL_OVERRIDE": metadata.get("robotws_repo_url") or "",
        "ROBOTWS_GIT_REF": metadata.get("robotws_ref") or metadata.get("robotws_branch") or "master",
        "ROBOTWS_CREDENTIALS_ID_OVERRIDE": metadata.get("robotws_credentials_id") or "",
        "TESTLINE_CONFIGURATION_REPO_URL_OVERRIDE": metadata.get("testline_configuration_repo_url") or "",
        "TESTLINE_CONFIGURATION_GIT_REF": metadata.get("testline_configuration_ref") or metadata.get("testline_configuration_branch") or "master",
        "TESTLINE_CONFIGURATION_CREDENTIALS_ID_OVERRIDE": metadata.get("testline_configuration_credentials_id") or "",
        "ARTIFACT_LABEL": metadata.get("artifact_label") or "quicktest",
        "RETRY_INDEX": metadata.get("retry_index") or "0",
        "ROBOT_LOG_LEVEL": metadata.get("log_level") or "TRACE",
    }
    return params
