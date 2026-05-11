from fastapi import APIRouter

from app.schemas.health import HealthResponse
from app.services.run_service import (
    apply_run_callback,
    get_run_artifacts,
    get_run_detail,
    get_run_kpi,
    get_run_list,
    get_tool_run_list,
    run_create,
    trigger_run,
    tool_run_create,
    update_run_stage,
)
from app.services.health_service import get_health_payload
from app.schemas.run import (
    RunArtifactsResponse,
    RunCallbackRequest,
    RunCallbackResponse,
    RunCreateRequest,
    RunCreateResponse,
    RunDetailResponse,
    RunKpiResponse,
    RunListResponse,
    RunStageUpdateRequest,
    RunStageUpdateResponse,
    RunTriggerResponse,
    ToolRunCreateRequest,
    ToolRunCreateResponse,
)

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["health"])
def get_health() -> HealthResponse:
    return HealthResponse(**get_health_payload())

@router.post("/runs", response_model=RunCreateResponse, tags=["run"])
def create_run(request: RunCreateRequest) -> RunCreateResponse:
    return run_create(request)


@router.post("/kpi/tool-runs", response_model=ToolRunCreateResponse, tags=["kpi"])
def create_tool_run(request: ToolRunCreateRequest) -> ToolRunCreateResponse:
    return tool_run_create(request)


@router.get("/kpi/tool-runs", response_model=RunListResponse, tags=["kpi"])
def list_tool_runs(status: str | None = None) -> RunListResponse:
    return get_tool_run_list(status=status)


@router.get("/runs", response_model=RunListResponse, tags=["run"])
def list_runs() -> RunListResponse:
    return get_run_list()


@router.get("/runs/{run_id}", response_model=RunDetailResponse, tags=["run"])
def get_run(run_id: str) -> RunDetailResponse:
    return get_run_detail(run_id)


@router.post("/runs/{run_id}/trigger", response_model=RunTriggerResponse, tags=["run"])
def trigger_existing_run(run_id: str) -> RunTriggerResponse:
    return trigger_run(run_id)


@router.get("/runs/{run_id}/artifacts", response_model=RunArtifactsResponse, tags=["run"])
def list_run_artifacts(run_id: str) -> RunArtifactsResponse:
    return get_run_artifacts(run_id)


@router.get("/runs/{run_id}/kpi", response_model=RunKpiResponse, tags=["run"])
def get_run_kpi_summary(run_id: str) -> RunKpiResponse:
    return get_run_kpi(run_id)


@router.post("/runs/{run_id}/callbacks/jenkins", response_model=RunCallbackResponse, tags=["run"])
def jenkins_callback(run_id: str, request: RunCallbackRequest) -> RunCallbackResponse:
    return apply_run_callback(run_id, request)


@router.post("/runs/{run_id}/callbacks/worker", response_model=RunCallbackResponse, tags=["run"])
def worker_callback(run_id: str, request: RunCallbackRequest) -> RunCallbackResponse:
    return apply_run_callback(run_id, request)


@router.post("/runs/{run_id}/stages", response_model=RunStageUpdateResponse, tags=["run"])
def update_stage(run_id: str, request: RunStageUpdateRequest) -> RunStageUpdateResponse:
    return update_run_stage(run_id, request)

