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
from app.services.jenkins_service import (
    JenkinsDispatchError,
    build_robot_jenkins_parameters,
    trigger_jenkins_job,
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
    RunStageUpdateRequest,
    RunStageUpdateResponse,
    RunTriggerResponse,
    ToolExecutionHandoff,
    ToolRunCreateRequest,
    ToolRunCreateResponse,
)


def _build_run_id(timestamp: str, sequence: int) -> str:
    if sequence == 0:
        return f"run-{timestamp}"
    return f"run-{timestamp}-{sequence:02d}"


def _normalize_optional_text(value: Any) -> str | None:
    cleaned = str(value or "").strip()
    return cleaned or None


def _insert_record_with_generated_run_id(record: dict[str, Any], timestamp: str) -> dict[str, Any]:
    for sequence in range(0, 1000):
        candidate = dict(record)
        candidate["run_id"] = _build_run_id(timestamp, sequence)
        try:
            insert_run_record(candidate)
            return candidate
        except sqlite3.IntegrityError:
            continue
    raise RuntimeError("Failed to generate a unique run_id.")


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
    if request.executor_type == "internal_tool":
        raise HTTPException(status_code=400, detail="Use /api/kpi/tool-runs to create internal tool runs.")
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

    record = _insert_record_with_generated_run_id(record, timestamp)

    return RunCreateResponse(
        run_id=record["run_id"],
        executor_type=record["executor_type"],
        status=record["status"],
        message=record["message"],
    )


def tool_run_create(request: ToolRunCreateRequest) -> ToolRunCreateResponse:
    if not request.payload:
        raise HTTPException(status_code=400, detail="payload is required for internal tool runs.")

    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    timestamp = now.strftime("%Y%m%d%H%M%S%f")[:-3]
    tool_payload = dict(request.payload)
    metadata = dict(request.metadata)
    metadata.update(
        {
            "tool_kind": request.tool_kind,
            "tool_payload": tool_payload,
        }
    )

    testline = _normalize_optional_text(request.testline) or _normalize_optional_text(tool_payload.get("test_line")) or "standalone"
    build = _normalize_optional_text(request.build) or _normalize_optional_text(tool_payload.get("build")) or ""
    generator_enabled = request.tool_kind == "kpi_generator"
    detector_enabled = request.tool_kind == "kpi_detector"
    record = {
        "executor_type": "internal_tool",
        "workflow_name": request.tool_kind,
        "testline": testline,
        "robotcase_path": "",
        "build": build,
        "scenario": _normalize_optional_text(tool_payload.get("scenario")) or "",
        "status": "created",
        "message": "Internal tool run request accepted.",
        "enable_kpi_generator": generator_enabled,
        "enable_kpi_anomaly_detector": detector_enabled,
        "workflow_spec_json": {},
        "run_metadata_json": metadata,
        "artifact_manifest_json": [],
        "kpi_config_json": tool_payload if generator_enabled else {},
        "kpi_summary_json": {},
        "detector_summary_json": {},
        "jenkins_build_ref": "",
        "started_at": "",
        "finished_at": "",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    record = _insert_record_with_generated_run_id(record, timestamp)
    run_id = record["run_id"]
    handoff = ToolExecutionHandoff(
        run_id=run_id,
        tool_kind=request.tool_kind,
        detail_url=f"/api/runs/{run_id}",
        callback_url=f"/api/runs/{run_id}/callbacks/worker",
    )
    return ToolRunCreateResponse(
        run_id=run_id,
        executor_type="internal_tool",
        tool_kind=request.tool_kind,
        status=record["status"],
        message=record["message"],
        handoff=handoff,
    )


def get_run_list() -> RunListResponse:
    records = [_normalize_record(record) for record in list_run_records()]
    return RunListResponse(items=[RunListItem(**record) for record in records])


def get_tool_run_list(status: str | None = None) -> RunListResponse:
    normalized_status = _normalize_optional_text(status)
    records = [
        _normalize_record(record)
        for record in list_run_records()
        if record.get("executor_type") == "internal_tool"
        and (normalized_status is None or record.get("status") == normalized_status)
    ]
    return RunListResponse(items=[RunListItem(**record) for record in records])


def get_run_detail(run_id: str) -> RunDetailResponse:
    return RunDetailResponse(**_get_required_record(run_id))


def trigger_run(run_id: str) -> RunTriggerResponse:
    record = _get_required_record(run_id)
    if record["executor_type"] == "internal_tool":
        raise HTTPException(status_code=400, detail="Internal tool runs are executed by the worker.")
    if record["executor_type"] != "robot":
        raise HTTPException(status_code=400, detail="Only robot runs can be triggered directly.")
    if record["status"] not in {"created", "trigger_failed"}:
        raise HTTPException(status_code=409, detail=f"Run cannot be triggered from status {record['status']}.")

    parameters = build_robot_jenkins_parameters(record)
    now = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()
    try:
        dispatch = trigger_jenkins_job(parameters=parameters)
    except JenkinsDispatchError as exc:
        update_run_record(
            run_id,
            {
                "status": "trigger_failed",
                "message": str(exc),
                "updated_at": now,
            },
        )
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    queue_url = _normalize_optional_text(dispatch.get("queue_url"))
    updated = update_run_record(
        run_id,
        {
            "status": "triggered",
            "message": "Run triggered via Jenkins.",
            "jenkins_build_ref": queue_url or "",
            "updated_at": now,
        },
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Run not found.")
    normalized = _normalize_record(updated)
    return RunTriggerResponse(
        run_id=run_id,
        executor_type=normalized["executor_type"],
        status=normalized["status"],
        message=normalized["message"],
        scheduler="jenkins",
        dispatch=dispatch,
    )


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


def update_run_stage(run_id: str, request: RunStageUpdateRequest) -> RunStageUpdateResponse:
    existing = _get_required_record(run_id)
    now = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()

    metadata = dict(existing["metadata"])
    stages: list[dict[str, Any]] = list(metadata.get("pipeline_stages") or [])

    # Find existing stage entry or create a new one
    stage_entry = None
    for entry in stages:
        if entry.get("name") == request.stage_name:
            stage_entry = entry
            break

    if stage_entry is None:
        stage_entry = {"name": request.stage_name}
        stages.append(stage_entry)

    stage_entry["status"] = request.stage_status
    if request.stage_status == "started":
        stage_entry["started_at"] = now
    elif request.stage_status in ("completed", "failed", "skipped"):
        stage_entry["finished_at"] = now
    if request.message:
        stage_entry["message"] = request.message

    metadata["pipeline_stages"] = stages

    updated = update_run_record(
        run_id,
        {
            "run_metadata_json": metadata,
            "updated_at": now,
        },
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Run not found.")

    return RunStageUpdateResponse(
        run_id=run_id,
        stage_name=request.stage_name,
        stage_status=request.stage_status,
        updated_at=now,
    )
