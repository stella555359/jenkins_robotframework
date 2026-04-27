import sqlite3
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import HTTPException

from app.repositories.run_repository import (
    get_run_record_by_id,
    insert_run_record,
    list_run_records,
    update_run_record,
)
from app.schemas.run import (
    RunArtifactsResponse,
    RunCallbackRequest,
    RunCallbackResponse,
    RunCreateRequest,
    RunCreateResponse,
    RunDetailResponse,
    RunKpiResponse,
    RunListItem,
    RunListResponse,
)


def _build_run_id(timestamp: str, sequence: int) -> str:
    if sequence == 0:
        return f"run-{timestamp}"
    return f"run-{timestamp}-{sequence:02d}"


def _normalize_optional_text(value: Any) -> str | None:
    cleaned = str(value or "").strip()
    return cleaned or None


def _normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(record)
    for key in (
        "workflow_name",
        "robotcase_path",
        "build",
        "scenario",
        "jenkins_build_ref",
        "started_at",
        "finished_at",
    ):
        normalized[key] = _normalize_optional_text(normalized.get(key))
    if not normalized.get("workflow_spec_json"):
        normalized["workflow_spec"] = None
    else:
        normalized["workflow_spec"] = normalized["workflow_spec_json"]
    normalized["metadata"] = normalized.get("run_metadata_json") or {}
    normalized["artifact_manifest"] = normalized.get("artifact_manifest_json") or []
    normalized["kpi_config"] = normalized.get("kpi_config_json") or None
    normalized["kpi_summary"] = normalized.get("kpi_summary_json") or {}
    normalized["detector_summary"] = normalized.get("detector_summary_json") or {}
    return normalized


def _get_required_record(run_id: str) -> dict[str, Any]:
    record = get_run_record_by_id(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Run not found.")
    return _normalize_record(record)


def _validate_run_create_request(request: RunCreateRequest) -> None:
    if request.executor_type == "robot" and not _normalize_optional_text(request.robotcase_path):
        raise HTTPException(status_code=400, detail="robotcase_path is required when executor_type is robot.")
    if (
        request.executor_type == "robot"
        and (request.enable_kpi_generator or request.enable_kpi_anomaly_detector or request.kpi_config is not None)
    ):
        raise HTTPException(status_code=400, detail="KPI options are only supported when executor_type is python_orchestrator.")
    if request.executor_type == "python_orchestrator" and request.workflow_spec is None:
        raise HTTPException(status_code=400, detail="workflow_spec is required when executor_type is python_orchestrator.")


def run_create(request: RunCreateRequest) -> RunCreateResponse:
    _validate_run_create_request(request)

    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    timestamp = now.strftime("%Y%m%d%H%M%S%f")[:-3]
    workflow_name = (
        (request.workflow_spec.name if request.workflow_spec else None)
        or _normalize_optional_text(request.robotcase_path)
    )
    record = {
        "executor_type": request.executor_type,
        "workflow_name": workflow_name or "",
        "testline": request.testline,
        "robotcase_path": _normalize_optional_text(request.robotcase_path) or "",
        "build": _normalize_optional_text(request.build) or "",
        "scenario": "",
        "status": "created",
        "message": "Run request accepted.",
        "enable_kpi_generator": request.enable_kpi_generator,
        "enable_kpi_anomaly_detector": request.enable_kpi_anomaly_detector,
        "workflow_spec_json": request.workflow_spec.model_dump(mode="json") if request.workflow_spec else {},
        "run_metadata_json": request.metadata,
        "artifact_manifest_json": [],
        "kpi_config_json": request.kpi_config.model_dump(mode="json") if request.kpi_config else {},
        "kpi_summary_json": {},
        "detector_summary_json": {},
        "jenkins_build_ref": "",
        "started_at": "",
        "finished_at": "",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }

    for sequence in range(0, 1000):
        record["run_id"] = _build_run_id(timestamp, sequence)
        try:
            insert_run_record(record)
            break
        except sqlite3.IntegrityError:
            continue
    else:
        raise RuntimeError("Failed to generate a unique run_id.")

    return RunCreateResponse(
        run_id=record["run_id"],
        executor_type=record["executor_type"],
        status=record["status"],
        message=record["message"],
    )


def get_run_list() -> RunListResponse:
    records = [_normalize_record(record) for record in list_run_records()]
    return RunListResponse(items=[RunListItem(**record) for record in records])


def get_run_detail(run_id: str) -> RunDetailResponse:
    return RunDetailResponse(**_get_required_record(run_id))


def get_run_artifacts(run_id: str) -> RunArtifactsResponse:
    record = _get_required_record(run_id)
    return RunArtifactsResponse(run_id=run_id, items=record["artifact_manifest"])


def get_run_kpi(run_id: str) -> RunKpiResponse:
    record = _get_required_record(run_id)
    return RunKpiResponse(
        run_id=run_id,
        generator_enabled=record["enable_kpi_generator"],
        detector_enabled=record["enable_kpi_anomaly_detector"],
        kpi_config=record["kpi_config"],
        kpi_summary=record["kpi_summary"],
        detector_summary=record["detector_summary"],
        artifact_manifest=record["artifact_manifest"],
    )


def apply_run_callback(run_id: str, request: RunCallbackRequest) -> RunCallbackResponse:
    existing = _get_required_record(run_id)
    now = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()
    merged_artifacts = request.artifact_manifest or existing["artifact_manifest"]
    merged_metadata = dict(existing["metadata"])
    merged_metadata.update(request.metadata)

    updated = update_run_record(
        run_id,
        {
            "status": request.status,
            "message": _normalize_optional_text(request.message) or existing["message"],
            "jenkins_build_ref": _normalize_optional_text(request.jenkins_build_ref) or (existing["jenkins_build_ref"] or ""),
            "started_at": _normalize_optional_text(request.started_at) or (existing["started_at"] or ""),
            "finished_at": _normalize_optional_text(request.finished_at) or (existing["finished_at"] or ""),
            "run_metadata_json": merged_metadata,
            "artifact_manifest_json": [item.model_dump(mode="json") for item in merged_artifacts],
            "kpi_summary_json": request.kpi_summary or existing["kpi_summary"],
            "detector_summary_json": request.detector_summary or existing["detector_summary"],
            "updated_at": now,
        },
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Run not found.")

    normalized = _normalize_record(updated)
    return RunCallbackResponse(
        run_id=run_id,
        status=normalized["status"],
        updated_at=normalized["updated_at"],
    )
