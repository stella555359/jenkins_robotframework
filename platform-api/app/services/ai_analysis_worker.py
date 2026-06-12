import json
import re
import ssl
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
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

KEY_ARTIFACT_LABELS = (
    "output.xml",
    "debug.log",
    "robot-command.json",
    "callback-payload.json",
    "ute_ue.log",
    "ute_ue.debug.log",
)

DIAGNOSTIC_LINE_PATTERN = re.compile(
    r"(?i)(error|fail|failed|failure|timeout|timed out|traceback|assertion|reservation|devicepool|"
    r"permission denied|no such file|modulenotfounderror|importing library failed|no keyword with name|variable not found)"
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


def _collect_evidence_texts(run_record: dict[str, Any], request: AIAnalysisRequest) -> list[dict[str, Any]]:
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
                    "path": path or None,
                    "url": url or None,
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
                        "path": None,
                        "url": f"{build_url.rstrip('/')}/consoleText",
                        "content": _limit_text(_redact(console_text), max_bytes),
                    }
                )

    return evidence


def _artifact_name(evidence: dict[str, Any]) -> str:
    return str(evidence.get("label") or evidence.get("path") or evidence.get("url") or "").replace("\\", "/").lower()


def _find_evidence(evidence_texts: list[dict[str, Any]], *names: str) -> dict[str, Any] | None:
    lowered_names = tuple(name.lower() for name in names)
    for item in evidence_texts:
        name = _artifact_name(item)
        if any(name.endswith(candidate) or candidate in name for candidate in lowered_names):
            return item
    return None


def _evidence_ref(
    item: dict[str, Any] | None,
    excerpt: str,
    *,
    stage: str | None = None,
    source_override: str | None = None,
) -> dict[str, Any]:
    return {
        "source": source_override or str((item or {}).get("label") or (item or {}).get("kind") or "analysis"),
        "excerpt": _limit_text(excerpt.replace("\n", " "), 500),
        "stage": stage,
        "artifact_path": (item or {}).get("path"),
    }


def _extract_diagnostic_lines(text: str, *, limit: int = 5) -> list[str]:
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or not DIAGNOSTIC_LINE_PATTERN.search(line):
            continue
        lines.append(_limit_text(line, 500))
        if len(lines) >= limit:
            break
    return lines


def _parse_json_summary(item: dict[str, Any] | None) -> dict[str, Any]:
    if not item:
        return {}
    try:
        payload = json.loads(str(item.get("content") or "{}"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    return {
        "status": payload.get("status"),
        "message": payload.get("message"),
        "command": payload.get("command") or payload.get("robot_command"),
        "test": payload.get("test") or payload.get("robotcase_path"),
        "artifact_count": len(payload.get("artifact_manifest") or []) if isinstance(payload.get("artifact_manifest"), list) else None,
    }


def _status_message(status: ET.Element | None) -> str:
    if status is None:
        return ""
    return " ".join("".join(status.itertext()).split())


def _parse_output_xml(item: dict[str, Any] | None) -> dict[str, Any] | None:
    if not item:
        return None
    try:
        root = ET.fromstring(str(item.get("content") or ""))
    except ET.ParseError:
        return None

    failed_test: ET.Element | None = None
    for test in root.iter("test"):
        status = test.find("status")
        if status is not None and str(status.attrib.get("status") or "").upper() == "FAIL":
            failed_test = test
            break
    if failed_test is None:
        return None

    test_status = failed_test.find("status")
    failed_keyword: ET.Element | None = None
    for keyword in failed_test.iter("kw"):
        keyword_status = keyword.find("status")
        if keyword_status is not None and str(keyword_status.attrib.get("status") or "").upper() == "FAIL":
            failed_keyword = keyword
            break

    keyword_name = str(failed_keyword.attrib.get("name") or "") if failed_keyword is not None else ""
    keyword_type = str(failed_keyword.attrib.get("type") or "") if failed_keyword is not None else ""
    message = _status_message(test_status)
    if failed_keyword is not None:
        keyword_message = _status_message(failed_keyword.find("status"))
        if keyword_message:
            message = keyword_message

    return {
        "test_name": str(failed_test.attrib.get("name") or ""),
        "keyword_name": keyword_name,
        "keyword_type": keyword_type.lower() or None,
        "message": message,
        "source": str(item.get("label") or "output.xml"),
        "artifact_path": item.get("path"),
    }


def _build_prompt(run_record: dict[str, Any], input_refs: list[EvidenceRef], evidence_texts: list[dict[str, Any]]) -> str:
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


def _classify_robot_failure(output_result: dict[str, Any], output_item: dict[str, Any]) -> dict[str, Any]:
    message = str(output_result.get("message") or "")
    lower_message = message.lower()
    test_name = str(output_result.get("test_name") or "unknown test")
    keyword_name = str(output_result.get("keyword_name") or "unknown keyword")

    category = "robot_case_failed"
    failure_layer = "robot"
    matched_rule = "robot_output_failed_test"
    rerun_advice = "needs_human_check"
    actions = [
        "Open Robot log.html/output.xml and inspect the failed test and keyword.",
        "Confirm whether the failed keyword is product behavior, test data, or environment related before rerun.",
    ]

    if any(token in lower_message for token in ("importing library failed", "no keyword with name", "variable not found")):
        category = "taf_import_or_library_error"
        failure_layer = "taf"
        matched_rule = "robot_taf_import_or_keyword_error"
        rerun_advice = "fix_required"
        actions = [
            "Check Robot library imports, resource paths, variables, and TAF dependency versions.",
            "Verify robotws and testline_configuration checkout refs match the selected build/testline.",
        ]
    elif "timeout" in lower_message or "timed out" in lower_message:
        category = "timeout"
        matched_rule = "robot_keyword_timeout"
        rerun_advice = "needs_human_check"
        actions = [
            "Check whether the timeout came from product state, UE/device response, or test environment slowness.",
            "Review debug.log and UE logs around the failed keyword timestamp before rerun.",
        ]
    elif "assertion" in lower_message or "should be" in lower_message:
        category = "assertion_failed"
        matched_rule = "robot_assertion_failed"
        rerun_advice = "needs_human_check"
        actions = [
            "Compare the expected and actual values in the failed assertion.",
            "Confirm whether the assertion reflects a product regression or stale test expectation.",
        ]

    symptom = f"Robot test '{test_name}' failed"
    if keyword_name and keyword_name != "unknown keyword":
        symptom = f"{symptom} at keyword '{keyword_name}'"
    if message:
        symptom = f"{symptom}: {message}"

    return {
        "category": category,
        "failure_layer": failure_layer,
        "confidence": "medium",
        "symptom": symptom,
        "primary_evidence": _evidence_ref(output_item, symptom, stage=keyword_name or None),
        "secondary_evidence": [],
        "recommended_actions": actions,
        "rerun_advice": rerun_advice,
        "matched_rule": matched_rule,
        "details": output_result,
    }


def _classify_text_failure(evidence_texts: list[dict[str, Any]], combined: str) -> dict[str, Any]:
    lower = combined.lower()
    rules = [
        {
            "category": "scm_credentials",
            "failure_layer": "jenkins_pipeline",
            "needle": "permission denied",
            "matched_rule": "scm_permission_denied",
            "rerun_advice": "fix_required",
            "action": "Check Git/SSH credentials configured in Jenkins.",
        },
        {
            "category": "python_dependency",
            "failure_layer": "taf",
            "needle": "modulenotfounderror",
            "matched_rule": "python_module_not_found",
            "rerun_advice": "fix_required",
            "action": "Check Python environment preparation and dependency lock file.",
        },
        {
            "category": "jenkins_agent",
            "failure_layer": "jenkins_pipeline",
            "needle": "still waiting to schedule task",
            "matched_rule": "jenkins_agent_unavailable",
            "rerun_advice": "needs_human_check",
            "action": "Check Jenkins agent labels and executor availability.",
        },
        {
            "category": "ue_reservation_or_device_pool",
            "failure_layer": "testline_ue",
            "needle": "devicepool",
            "matched_rule": "ue_devicepool_error",
            "rerun_advice": "needs_human_check",
            "action": "Check UE reservation, device pool availability, and keep_reservation logs.",
        },
        {
            "category": "ue_reservation_or_device_pool",
            "failure_layer": "testline_ue",
            "needle": "reservation",
            "matched_rule": "ue_reservation_error",
            "rerun_advice": "needs_human_check",
            "action": "Check testline reservation state and UE availability before rerun.",
        },
        {
            "category": "timeout",
            "failure_layer": "robot",
            "needle": "timeout",
            "matched_rule": "text_timeout",
            "rerun_advice": "needs_human_check",
            "action": "Review the timeout source in Robot/debug logs before rerun.",
        },
        {
            "category": "assertion_failed",
            "failure_layer": "robot",
            "needle": "assertionerror",
            "matched_rule": "text_assertion_error",
            "rerun_advice": "needs_human_check",
            "action": "Compare expected and actual values from Robot logs.",
        },
        {
            "category": "taf_import_or_library_error",
            "failure_layer": "taf",
            "needle": "importing library failed",
            "matched_rule": "text_taf_library_import_failed",
            "rerun_advice": "fix_required",
            "action": "Check Robot library imports, PYTHONPATH, and TAF dependency versions.",
        },
        {
            "category": "checkout_or_workspace_failed",
            "failure_layer": "jenkins_pipeline",
            "needle": "no such file or directory",
            "matched_rule": "workspace_missing_path",
            "rerun_advice": "fix_required",
            "action": "Check generated script paths and workspace layout.",
        },
    ]

    for rule in rules:
        if str(rule["needle"]) not in lower:
            continue
        source_item = next((item for item in evidence_texts if str(rule["needle"]) in str(item.get("content") or "").lower()), evidence_texts[0])
        excerpt_lines = _extract_diagnostic_lines(str(source_item.get("content") or ""), limit=1)
        excerpt = excerpt_lines[0] if excerpt_lines else str(rule["needle"])
        symptom = f"Matched diagnostic pattern '{rule['needle']}' in {source_item.get('label') or source_item.get('kind')}."
        return {
            "category": rule["category"],
            "failure_layer": rule["failure_layer"],
            "confidence": "medium",
            "symptom": symptom,
            "primary_evidence": _evidence_ref(source_item, excerpt),
            "secondary_evidence": [],
            "recommended_actions": [rule["action"]],
            "rerun_advice": rule["rerun_advice"],
            "matched_rule": rule["matched_rule"],
            "details": {"matched_text": rule["needle"]},
        }

    return {
        "category": "unknown",
        "failure_layer": "unknown",
        "confidence": "low",
        "symptom": "No high-confidence failure rule matched the collected evidence.",
        "primary_evidence": _evidence_ref(evidence_texts[0] if evidence_texts else None, "No primary diagnostic evidence was selected."),
        "secondary_evidence": [],
        "recommended_actions": [
            "Review Jenkins console and archived artifacts.",
            "Add a rules_first pattern if the failure is recurring and diagnosable.",
        ],
        "rerun_advice": "needs_human_check",
        "matched_rule": "no_rule_matched",
        "details": {},
    }


def _rules_first_payload(run_record: dict[str, Any], evidence_texts: list[dict[str, Any]]) -> dict[str, Any]:
    combined = "\n".join(str(item.get("content") or "") for item in evidence_texts)
    output_item = _find_evidence(evidence_texts, "output.xml")
    output_result = _parse_output_xml(output_item)
    diagnosis = _classify_robot_failure(output_result, output_item) if output_result and output_item else _classify_text_failure(evidence_texts, combined)

    debug_item = _find_evidence(evidence_texts, "debug.log")
    ue_item = _find_evidence(evidence_texts, "ute_ue.log", "ute_ue.debug.log")
    command_item = _find_evidence(evidence_texts, "robot-command.json")
    callback_item = _find_evidence(evidence_texts, "callback-payload.json")

    secondary_evidence = list(diagnosis.get("secondary_evidence") or [])
    for item in (debug_item, ue_item):
        for line in _extract_diagnostic_lines(str((item or {}).get("content") or ""), limit=2):
            secondary_evidence.append(_evidence_ref(item, line))
    for item in (command_item, callback_item):
        summary = _parse_json_summary(item)
        if summary:
            secondary_evidence.append(_evidence_ref(item, json.dumps({k: v for k, v in summary.items() if v is not None}, ensure_ascii=False)))
    diagnosis["secondary_evidence"] = secondary_evidence[:5]

    category = str(diagnosis["category"])
    confidence = str(diagnosis["confidence"])
    next_step = str((diagnosis.get("recommended_actions") or ["Review Jenkins console and archived artifacts."])[0])

    status = str(run_record.get("status") or "unknown")
    summary = f"Run {run_record.get('run_id')} finished with status {status}."
    if diagnosis.get("symptom"):
        summary = f"{summary} {diagnosis['symptom']}"

    root_evidence = [diagnosis["primary_evidence"], *diagnosis["secondary_evidence"]]
    analyzed_artifacts = [
        str(item.get("label") or item.get("kind"))
        for item in evidence_texts
        if _artifact_name(item).endswith(KEY_ARTIFACT_LABELS) or item.get("kind") in {"run_context", "jenkins_console"}
    ]

    return {
        "log_summary": {
            "one_line_summary": summary,
            "failed_stage": (diagnosis.get("details") or {}).get("keyword_type"),
            "failed_command": (_parse_json_summary(command_item) or {}).get("command"),
            "key_errors": [str((diagnosis.get("details") or {}).get("matched_text") or diagnosis.get("matched_rule"))],
            "impact": "AI used bounded Jenkins/run evidence; verify before changing environment.",
            "next_step": next_step,
        },
        "root_cause": {
            "category": category,
            "confidence": confidence,
            "symptom": str(diagnosis.get("symptom") or summary),
            "evidence": root_evidence,
            "recommended_actions": list(diagnosis.get("recommended_actions") or [next_step]),
            "needs_human_confirmation": True,
        },
        "test_report": {
            "title": "AI Run Analysis Report",
            "status": status,
            "summary_markdown": summary,
            "sections": [
                {
                    "title": "Diagnosis",
                    "content_markdown": "\n".join(
                        [
                            f"- Failure layer: {diagnosis.get('failure_layer')}",
                            f"- Matched rule: {diagnosis.get('matched_rule')}",
                            f"- Rerun advice: {diagnosis.get('rerun_advice')}",
                            f"- Primary evidence: {diagnosis['primary_evidence']['source']}",
                        ]
                    ),
                },
                {
                    "title": "Evidence Coverage",
                    "content_markdown": "\n".join(f"- {item.get('kind')}: {item.get('label')}" for item in evidence_texts),
                },
            ],
        },
        "quality_signals": {
            "failure_signature": f"{run_record.get('executor_type')}|{category}|{run_record.get('testline')}",
            "failure_layer": diagnosis.get("failure_layer"),
            "matched_rule": diagnosis.get("matched_rule"),
            "rerun_advice": diagnosis.get("rerun_advice"),
            "primary_evidence_source": diagnosis["primary_evidence"]["source"],
            "analyzed_artifacts": analyzed_artifacts,
            "stability_label": "needs_review" if category == "unknown" else "environment_or_pipeline_failure",
            "release_risk": "unknown",
        },
    }


def _invoke_cursor_rest(prompt: str) -> dict[str, Any]:
    from app.services.cursor_rest_client import CursorApiError, prompt_cloud_no_repo

    try:
        raw_result = prompt_cloud_no_repo(prompt, model_id=settings.ai_analysis_model)
    except CursorApiError as exc:
        if exc.status_code == 403:
            raise RuntimeError(
                "Cursor Cloud Agent API returned 403 feature_unavailable. "
                "Confirm Cloud Agents is enabled for this account/key in Cursor Dashboard, "
                "or run platform-api/scripts/cursor_api_smoke.py for details."
            ) from exc
        raise RuntimeError(f"Cursor REST API failed: {exc}") from exc
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
        payload = _invoke_cursor_rest(prompt)

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
                recommended_actions=["Check AI worker logs, CURSOR_API_KEY, Cursor REST API access, and Jenkins evidence access."],
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
