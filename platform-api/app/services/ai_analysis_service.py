import sqlite3
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import HTTPException

from app.repositories.ai_analysis_repository import (
    get_latest_ai_analysis_record,
    insert_ai_analysis_record,
)
from app.repositories.run_repository import get_run_record_by_id
from app.schemas.ai_analysis import (
    AIAnalysisCreateResponse,
    AIAnalysisRequest,
    AIAnalysisResult,
    AIReportResponse,
    AITestReport,
    AITestReportSection,
    EvidenceRef,
    LogSummary,
    RootCauseAnalysis,
)


AI_ANALYSIS_VERSION = "ai-mvp-v1"


def _now() -> str:
    return datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()


def _timestamp() -> str:
    return datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%d%H%M%S%f")[:-3]


def _build_analysis_id(run_id: str, timestamp: str, sequence: int) -> str:
    suffix = "" if sequence == 0 else f"-{sequence:02d}"
    return f"ai-{run_id}-{timestamp}{suffix}"


def _normalize_optional_text(value: Any) -> str | None:
    cleaned = str(value or "").strip()
    return cleaned or None


def _normalize_run_record(record: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(record)
    normalized["metadata"] = normalized.get("run_metadata_json") or {}
    normalized["artifact_manifest"] = normalized.get("artifact_manifest_json") or []
    normalized["kpi_summary"] = normalized.get("kpi_summary_json") or {}
    normalized["detector_summary"] = normalized.get("detector_summary_json") or {}
    normalized["workflow_spec"] = normalized.get("workflow_spec_json") or {}
    return normalized


def _get_required_run_record(run_id: str) -> dict[str, Any]:
    record = get_run_record_by_id(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Run not found.")
    return _normalize_run_record(record)


def build_evidence_manifest(run_record: dict[str, Any], request: AIAnalysisRequest) -> list[EvidenceRef]:
    refs: list[EvidenceRef] = []
    metadata = run_record.get("metadata") or {}

    refs.append(
        EvidenceRef(
            kind="run_metadata",
            label="Run Metadata",
            available=True,
            metadata={
                "source": "platform-api",
                "status": run_record.get("status"),
                "executor_type": run_record.get("executor_type"),
                "testline": run_record.get("testline"),
                "build": run_record.get("build"),
                "jenkins_build_ref": run_record.get("jenkins_build_ref"),
            },
        )
    )

    pipeline_stages = metadata.get("pipeline_stages") or []
    if pipeline_stages:
        refs.append(
            EvidenceRef(
                kind="pipeline_stages",
                label="Pipeline Stage Timeline",
                available=True,
                metadata={"source": "run_metadata", "count": len(pipeline_stages)},
            )
        )

    progress_events = metadata.get("progress_events") or []
    if progress_events:
        refs.append(
            EvidenceRef(
                kind="progress_events",
                label="Run Progress Events",
                available=True,
                metadata={"source": "run_metadata", "count": len(progress_events)},
            )
        )

    if request.include_artifacts:
        for item in run_record.get("artifact_manifest") or []:
            if not isinstance(item, dict):
                continue
            refs.append(
                EvidenceRef(
                    kind=str(item.get("kind") or "artifact"),
                    label=str(item.get("label") or item.get("path") or item.get("url") or "Artifact"),
                    path=_normalize_optional_text(item.get("path")),
                    url=_normalize_optional_text(item.get("url")),
                    available=bool(_normalize_optional_text(item.get("path")) or _normalize_optional_text(item.get("url"))),
                    metadata={
                        "source": "artifact_manifest",
                        **(item.get("metadata") or {}),
                    },
                )
            )

    if request.include_console:
        refs.append(
            EvidenceRef(
                kind="jenkins_console",
                label="Jenkins Console",
                available=bool(_normalize_optional_text(run_record.get("jenkins_build_ref"))),
                metadata={
                    "source": "jenkins_api",
                    "jenkins_build_ref": run_record.get("jenkins_build_ref"),
                },
            )
        )

    if run_record.get("kpi_summary"):
        refs.append(
            EvidenceRef(
                kind="kpi_summary",
                label="KPI Summary",
                available=True,
                metadata={"source": "platform-api"},
            )
        )

    if run_record.get("detector_summary"):
        refs.append(
            EvidenceRef(
                kind="detector_summary",
                label="KPI Detector Summary",
                available=True,
                metadata={"source": "platform-api"},
            )
        )

    return refs


def _build_initial_result(
    *,
    run_id: str,
    analysis_id: str,
    status: str,
    generated_at: str,
    input_refs: list[EvidenceRef],
    message: str | None = None,
) -> dict[str, Any]:
    result = AIAnalysisResult(
        run_id=run_id,
        analysis_id=analysis_id,
        analysis_status=status,  # type: ignore[arg-type]
        analysis_version=AI_ANALYSIS_VERSION,
        generated_at=generated_at,
        input_refs=input_refs,
        log_summary=LogSummary(
            one_line_summary="AI analysis is queued.",
            next_step="Wait for the AI analysis worker to process this run.",
        ),
        root_cause=RootCauseAnalysis(
            category="pending",
            confidence="low",
            symptom="AI analysis has not completed yet.",
            recommended_actions=["Check the analysis worker if this stays queued."],
            needs_human_confirmation=True,
        ),
        test_report=AITestReport(
            title="AI Run Analysis Report",
            status=status,
            summary_markdown="AI analysis is queued and will be generated by the worker.",
            sections=[],
        ),
        quality_signals={"analysis_mode": "pending"},
        message=message,
    )
    return result.model_dump(mode="json")


def _insert_analysis_with_generated_id(
    *,
    run_id: str,
    request: AIAnalysisRequest,
    input_refs: list[EvidenceRef],
    now: str,
    timestamp: str,
) -> dict[str, Any]:
    for sequence in range(0, 1000):
        analysis_id = _build_analysis_id(run_id, timestamp, sequence)
        result_json = _build_initial_result(
            run_id=run_id,
            analysis_id=analysis_id,
            status="queued",
            generated_at=now,
            input_refs=input_refs,
            message="AI analysis queued.",
        )
        record = {
            "analysis_id": analysis_id,
            "run_id": run_id,
            "analysis_status": "queued",
            "analysis_version": AI_ANALYSIS_VERSION,
            "analysis_mode": request.analysis_mode,
            "request_json": request.model_dump(mode="json"),
            "result_json": result_json,
            "report_markdown": "",
            "error_message": "",
            "created_at": now,
            "updated_at": now,
        }
        try:
            insert_ai_analysis_record(record)
            return record
        except sqlite3.IntegrityError:
            continue
    raise RuntimeError("Failed to generate a unique analysis_id.")


def create_ai_analysis(run_id: str, request: AIAnalysisRequest) -> AIAnalysisCreateResponse:
    run_record = _get_required_run_record(run_id)
    existing = get_latest_ai_analysis_record(run_id)
    if existing is not None and not request.refresh:
        return AIAnalysisCreateResponse(
            run_id=run_id,
            analysis_id=existing["analysis_id"],
            analysis_status=existing["analysis_status"],
            message="Existing AI analysis returned.",
        )

    now = _now()
    input_refs = build_evidence_manifest(run_record, request)
    record = _insert_analysis_with_generated_id(
        run_id=run_id,
        request=request,
        input_refs=input_refs,
        now=now,
        timestamp=_timestamp(),
    )
    return AIAnalysisCreateResponse(
        run_id=run_id,
        analysis_id=record["analysis_id"],
        analysis_status="queued",
        message="AI analysis queued.",
    )


def _analysis_record_to_result(record: dict[str, Any]) -> AIAnalysisResult:
    result_json = dict(record.get("result_json") or {})
    result_json.setdefault("run_id", record["run_id"])
    result_json.setdefault("analysis_id", record["analysis_id"])
    result_json["analysis_status"] = record["analysis_status"]
    result_json.setdefault("analysis_version", record["analysis_version"])
    result_json.setdefault("generated_at", record["updated_at"])
    if record.get("error_message") and not result_json.get("message"):
        result_json["message"] = record["error_message"]
    return AIAnalysisResult(**result_json)


def get_ai_analysis(run_id: str) -> AIAnalysisResult:
    _get_required_run_record(run_id)
    record = get_latest_ai_analysis_record(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="AI analysis not generated.")
    return _analysis_record_to_result(record)


def build_markdown_report(result: AIAnalysisResult) -> str:
    failure_layer = result.quality_signals.get("failure_layer") or "unknown"
    matched_rule = result.quality_signals.get("matched_rule") or "unknown"
    rerun_advice = result.quality_signals.get("rerun_advice") or "needs_human_check"
    lines = [
        f"# {result.test_report.title}",
        "",
        f"- Run ID: `{result.run_id}`",
        f"- Analysis ID: `{result.analysis_id}`",
        f"- Status: `{result.analysis_status}`",
        f"- Version: `{result.analysis_version}`",
        "",
        "## Summary",
        result.test_report.summary_markdown or result.log_summary.one_line_summary or "No summary generated.",
        "",
        "## Root Cause",
        f"- Category: `{result.root_cause.category}`",
        f"- Confidence: `{result.root_cause.confidence}`",
        f"- Failure Layer: `{failure_layer}`",
        f"- Matched Rule: `{matched_rule}`",
        f"- Rerun Advice: `{rerun_advice}`",
        f"- Symptom: {result.root_cause.symptom or 'Not available.'}",
        "",
        "## Primary Evidence",
    ]
    if result.root_cause.evidence:
        primary = result.root_cause.evidence[0]
        lines.extend(
            [
                f"- Source: `{primary.source}`",
                f"- Stage / Keyword: {primary.stage or 'Not available.'}",
                f"- Artifact: {primary.artifact_path or 'Not available.'}",
                f"- Excerpt: {primary.excerpt}",
            ]
        )
    else:
        lines.append("- No primary evidence was selected.")

    if len(result.root_cause.evidence) > 1:
        lines.extend(["", "## Secondary Evidence"])
        for evidence in result.root_cause.evidence[1:]:
            lines.append(f"- `{evidence.source}`: {evidence.excerpt}")

    lines.extend(
        [
            "",
            "## Recommended Actions",
        ]
    )
    actions = result.root_cause.recommended_actions or ["Review Jenkins artifacts and run metadata."]
    lines.extend(f"- {action}" for action in actions)
    lines.extend(["", "## Evidence"])
    if result.input_refs:
        lines.extend(
            f"- `{ref.kind}`: {ref.label} ({'available' if ref.available else 'missing'})"
            for ref in result.input_refs
        )
    else:
        lines.append("- No evidence references were recorded.")
    for section in result.test_report.sections:
        lines.extend(["", f"## {section.title}", section.content_markdown])
    return "\n".join(lines).strip() + "\n"


def get_ai_report(run_id: str) -> AIReportResponse:
    result = get_ai_analysis(run_id)
    record = get_latest_ai_analysis_record(run_id)
    content = (record or {}).get("report_markdown") or build_markdown_report(result)
    return AIReportResponse(
        run_id=run_id,
        content=content,
        generated_at=result.generated_at,
    )
