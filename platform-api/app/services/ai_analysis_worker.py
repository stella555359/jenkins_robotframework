import json
import os
import re
import ssl
import time
import urllib.error
import urllib.request
from base64 import b64encode
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.repositories.ai_analysis_repository import (
    claim_queued_ai_analysis_record,
    list_queued_ai_analysis_records,
    update_ai_analysis_record,
)
from app.repositories.run_repository import get_run_record_by_id
from app.schemas.ai_analysis import (
    AIAnalysisRequest,
    AIAnalysisResult,
    AITestReport,
    AITestReportSection,
    EvidenceRef,
    LogSummary,
    RootCauseAnalysis,
)
from app.services.ai_analysis_service import (
    AI_ANALYSIS_VERSION,
    build_evidence_manifest,
    build_markdown_report,
)
from app.services.run_service import _normalize_record


SECRET_PATTERNS = (
    re.compile(r"(?i)(password|passwd|token|secret|api[_-]?key)\s*[:=]\s*([^\s'\";,]+)"),
    re.compile(r"csr_[A-Za-z0-9_\-]+"),
)


def _now() -> str:
    from datetime import datetime
    from zoneinfo import ZoneInfo

    return datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()


def _redact(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(lambda match: f"{match.group(1)}=<redacted>" if match.groups() else "<redacted>", redacted)
    return redacted


def _limit_text(text: str, max_bytes: int) -> str:
    encoded = text.encode("utf-8", errors="ignore")
    if len(encoded) <= max_bytes:
        return text
    return encoded[:max_bytes].decode("utf-8", errors="ignore") + "\n...[truncated]..."


def _read_local_text(path: str, max_bytes: int) -> str | None:
    target = Path(path)
    if not target.exists() or not target.is_file():
        return None
    data = target.read_bytes()[:max_bytes]
    return data.decode("utf-8", errors="ignore")


def _request_headers() -> dict[str, str]:
    headers: dict[str, str] = {}
    if settings.jenkins_username and settings.jenkins_api_token:
        raw = f"{settings.jenkins_username}:{settings.jenkins_api_token}".encode("utf-8")
        headers["Authorization"] = "Basic " + b64encode(raw).decode("ascii")
    return headers


def _fetch_url_text(url: str, max_bytes: int) -> str | None:
    context = ssl._create_unverified_context() if settings.jenkins_insecure_tls else None
    request = urllib.request.Request(url, headers=_request_headers())
    try:
        with urllib.request.urlopen(request, timeout=settings.jenkins_timeout_seconds, context=context) as response:
            data = response.read(max_bytes)
    except (urllib.error.URLError, TimeoutError, ValueError):
        return None
    return data.decode("utf-8", errors="ignore")


def _jenkins_build_url_from_ref(jenkins_build_ref: str | None) -> str | None:
    ref = str(jenkins_build_ref or "").strip()
    if not ref:
        return None
    if ref.startswith("http://") or ref.startswith("https://"):
        return ref.rstrip("/")
    if "#" not in ref or not settings.jenkins_base_url:
        return None
    job_path, build_number = ref.rsplit("#", 1)
    normalized_job_path = job_path.strip("/")
    if not normalized_job_path.startswith("job/"):
        normalized_job_path = "/".join(f"job/{part}" for part in normalized_job_path.split("/") if part)
    return f"{settings.jenkins_base_url.rstrip('/')}/{normalized_job_path}/{build_number.strip('/')}"


def _collect_evidence_texts(run_record: dict[str, Any], request: AIAnalysisRequest) -> list[dict[str, str]]:
    max_bytes = settings.ai_analysis_max_evidence_bytes
    evidence: list[dict[str, str]] = []

    context_payload = {
        "run_id": run_record.get("run_id"),
        "executor_type": run_record.get("executor_type"),
        "testline": run_record.get("testline"),
        "build": run_record.get("build"),
        "status": run_record.get("status"),
        "message": run_record.get("message"),
        "jenkins_build_ref": run_record.get("jenkins_build_ref"),
        "metadata": run_record.get("metadata"),
        "kpi_summary": run_record.get("kpi_summary"),
        "detector_summary": run_record.get("detector_summary"),
    }
    evidence.append(
        {
            "kind": "run_context",
            "label": "Run Context",
            "content": json.dumps(context_payload, ensure_ascii=False, indent=2),
        }
    )

    if request.include_artifacts:
        for artifact in run_record.get("artifact_manifest") or []:
            if not isinstance(artifact, dict):
                continue
            text: str | None = None
            path = str(artifact.get("path") or "").strip()
            url = str(artifact.get("url") or "").strip()
            if path:
                text = _read_local_text(path, max_bytes)
            if text is None and url:
                text = _fetch_url_text(url, max_bytes)
            if text is None:
                continue
            evidence.append(
                {
                    "kind": str(artifact.get("kind") or "artifact"),
                    "label": str(artifact.get("label") or path or url),
                    "content": _limit_text(_redact(text), max_bytes),
                }
            )

    if request.include_console:
        build_url = _jenkins_build_url_from_ref(run_record.get("jenkins_build_ref"))
        if build_url:
            console_text = _fetch_url_text(f"{build_url.rstrip('/')}/consoleText", max_bytes)
            if console_text:
                evidence.append(
                    {
                        "kind": "jenkins_console",
                        "label": "Jenkins Console",
                        "content": _limit_text(_redact(console_text), max_bytes),
                    }
                )

    return evidence


def _build_prompt(run_record: dict[str, Any], input_refs: list[EvidenceRef], evidence_texts: list[dict[str, str]]) -> str:
    evidence_payload = {
        "run": {
            "run_id": run_record.get("run_id"),
            "executor_type": run_record.get("executor_type"),
            "testline": run_record.get("testline"),
            "build": run_record.get("build"),
            "status": run_record.get("status"),
            "message": run_record.get("message"),
        },
        "input_refs": [ref.model_dump(mode="json") for ref in input_refs],
        "evidence_texts": evidence_texts,
    }
    return (
        "Analyze this Jenkins/Robot run evidence and return STRICT JSON only. "
        "Do not include markdown fences. The JSON must contain keys: "
        "log_summary, root_cause, test_report, quality_signals. "
        "Use evidence excerpts and include recommended actions. "
        "If evidence is insufficient, say so and set confidence to low.\n\n"
        f"{json.dumps(evidence_payload, ensure_ascii=False, indent=2)}"
    )


def _extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(stripped[start : end + 1])


def _rules_first_payload(run_record: dict[str, Any], evidence_texts: list[dict[str, str]]) -> dict[str, Any]:
    combined = "\n".join(item["content"] for item in evidence_texts)
    lower = combined.lower()
    category = "unknown"
    confidence = "low"
    key_errors: list[str] = []
    next_step = "Review Jenkins console and archived artifacts."

    patterns = [
        ("scm_credentials", "permission denied", "Check Git/SSH credentials configured in Jenkins."),
        ("python_dependency", "modulenotfounderror", "Check Python environment preparation and dependency lock file."),
        ("jenkins_agent", "still waiting to schedule task", "Check Jenkins agent labels and executor availability."),
        ("pipeline_script", "no such file or directory", "Check generated script paths and workspace layout."),
    ]
    for candidate, needle, action in patterns:
        if needle in lower:
            category = candidate
            confidence = "medium"
            key_errors.append(needle)
            next_step = action
            break

    status = str(run_record.get("status") or "unknown")
    summary = f"Run {run_record.get('run_id')} finished with status {status}."
    if key_errors:
        summary = f"{summary} Key error pattern: {key_errors[0]}."

    return {
        "log_summary": {
            "one_line_summary": summary,
            "failed_stage": None,
            "failed_command": None,
            "key_errors": key_errors,
            "impact": "AI used bounded Jenkins/run evidence; verify before changing environment.",
            "next_step": next_step,
        },
        "root_cause": {
            "category": category,
            "confidence": confidence,
            "symptom": summary,
            "evidence": [
                {
                    "source": item["kind"],
                    "excerpt": _limit_text(item["content"].replace("\n", " "), 300),
                    "stage": None,
                    "artifact_path": None,
                }
                for item in evidence_texts[:3]
            ],
            "recommended_actions": [next_step],
            "needs_human_confirmation": True,
        },
        "test_report": {
            "title": "AI Run Analysis Report",
            "status": status,
            "summary_markdown": summary,
            "sections": [
                {
                    "title": "Evidence Coverage",
                    "content_markdown": "\n".join(f"- {item['kind']}: {item['label']}" for item in evidence_texts),
                }
            ],
        },
        "quality_signals": {
            "failure_signature": f"{run_record.get('executor_type')}|{category}|{run_record.get('testline')}",
            "stability_label": "needs_review" if category == "unknown" else "environment_or_pipeline_failure",
            "release_risk": "unknown",
        },
    }


def _invoke_cursor_sdk(prompt: str) -> dict[str, Any]:
    api_key = os.environ.get("CURSOR_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("CURSOR_API_KEY is not configured for AI analysis worker.")
    try:
        from cursor_sdk import Agent, AgentOptions, CursorAgentError, LocalAgentOptions
    except ImportError as exc:
        raise RuntimeError("cursor-sdk package is not installed in the platform-api environment.") from exc

    try:
        result = Agent.prompt(
            prompt,
            AgentOptions(
                api_key=api_key,
                model=settings.ai_analysis_model,
                local=LocalAgentOptions(cwd=settings.ai_analysis_workspace),
            ),
        )
    except CursorAgentError as exc:
        raise RuntimeError(f"Cursor SDK startup failed: {exc}") from exc

    if getattr(result, "status", "") == "error":
        raise RuntimeError(f"Cursor SDK run failed: {getattr(result, 'result', '')}")
    raw_result = getattr(result, "result", "")
    if not isinstance(raw_result, str):
        raw_result = str(raw_result)
    return _extract_json_object(raw_result)


def _result_from_payload(
    *,
    run_record: dict[str, Any],
    analysis_record: dict[str, Any],
    input_refs: list[EvidenceRef],
    payload: dict[str, Any],
) -> AIAnalysisResult:
    return AIAnalysisResult(
        run_id=analysis_record["run_id"],
        analysis_id=analysis_record["analysis_id"],
        analysis_status="completed",
        analysis_version=AI_ANALYSIS_VERSION,
        generated_at=_now(),
        input_refs=input_refs,
        log_summary=LogSummary(**(payload.get("log_summary") or {})),
        root_cause=RootCauseAnalysis(**(payload.get("root_cause") or {})),
        test_report=AITestReport(**(payload.get("test_report") or {
            "title": "AI Run Analysis Report",
            "status": run_record.get("status") or "unknown",
            "summary_markdown": "AI analysis completed.",
            "sections": [],
        })),
        quality_signals=payload.get("quality_signals") or {},
        message="AI analysis completed.",
    )


def process_ai_analysis_record(analysis_record: dict[str, Any]) -> AIAnalysisResult:
    run_record = get_run_record_by_id(analysis_record["run_id"])
    if run_record is None:
        raise RuntimeError(f"Run not found: {analysis_record['run_id']}")
    normalized_run = _normalize_record(run_record)
    request = AIAnalysisRequest(**(analysis_record.get("request_json") or {}))
    input_refs = build_evidence_manifest(normalized_run, request)
    evidence_texts = _collect_evidence_texts(normalized_run, request)

    if request.analysis_mode == "rules_first":
        payload = _rules_first_payload(normalized_run, evidence_texts)
    else:
        prompt = _build_prompt(normalized_run, input_refs, evidence_texts)
        payload = _invoke_cursor_sdk(prompt)

    return _result_from_payload(
        run_record=normalized_run,
        analysis_record=analysis_record,
        input_refs=input_refs,
        payload=payload,
    )


def process_next_ai_analysis() -> bool:
    queued = list_queued_ai_analysis_records(limit=1)
    if not queued:
        return False
    claimed = claim_queued_ai_analysis_record(queued[0]["analysis_id"], updated_at=_now())
    if claimed is None:
        return False
    try:
        result = process_ai_analysis_record(claimed)
        update_ai_analysis_record(
            claimed["analysis_id"],
            {
                "analysis_status": "completed",
                "result_json": result.model_dump(mode="json"),
                "report_markdown": build_markdown_report(result),
                "error_message": "",
                "updated_at": result.generated_at,
            },
        )
    except Exception as exc:
        failed_result = AIAnalysisResult(
            run_id=claimed["run_id"],
            analysis_id=claimed["analysis_id"],
            analysis_status="failed",
            analysis_version=AI_ANALYSIS_VERSION,
            generated_at=_now(),
            input_refs=[],
            log_summary=LogSummary(one_line_summary="AI analysis failed.", key_errors=[str(exc)]),
            root_cause=RootCauseAnalysis(
                category="ai_worker_error",
                confidence="low",
                symptom=str(exc),
                recommended_actions=["Check AI worker logs, CURSOR_API_KEY, Cursor SDK package, and Jenkins evidence access."],
                needs_human_confirmation=True,
            ),
            test_report=AITestReport(
                title="AI Run Analysis Report",
                status="failed",
                summary_markdown=f"AI analysis failed: {exc}",
                sections=[
                    AITestReportSection(
                        title="Failure",
                        content_markdown=str(exc),
                    )
                ],
            ),
            quality_signals={"failure_signature": "ai_worker_error"},
            message=str(exc),
        )
        update_ai_analysis_record(
            claimed["analysis_id"],
            {
                "analysis_status": "failed",
                "result_json": failed_result.model_dump(mode="json"),
                "report_markdown": build_markdown_report(failed_result),
                "error_message": str(exc),
                "updated_at": failed_result.generated_at,
            },
        )
    return True


def run_ai_analysis_worker_loop() -> None:
    while True:
        processed = process_next_ai_analysis()
        if not processed:
            time.sleep(settings.ai_analysis_worker_poll_seconds)


if __name__ == "__main__":
    run_ai_analysis_worker_loop()
