from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


ExecutorType = Literal["robot", "python_orchestrator"]
ExecutionMode = Literal["serial", "parallel"]


class ArtifactDescriptor(BaseModel):
    kind: str = Field(min_length=1)
    label: str = Field(min_length=1)
    path: str | None = None
    url: str | None = None
    content_type: str | None = None
    source: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowItem(BaseModel):
    item_id: str = Field(min_length=1)
    model: str = Field(min_length=1)
    enabled: bool = True
    order: int = 0
    execution_mode: ExecutionMode = "serial"
    continue_on_failure: bool = False
    ue_scope: dict[str, Any] = Field(default_factory=lambda: {"mode": "all_selected_ues"})
    params: dict[str, Any] = Field(default_factory=dict)


class WorkflowStage(BaseModel):
    stage_id: int = Field(ge=1)
    stage_name: str = Field(min_length=1)
    execution_mode: ExecutionMode = "serial"
    items: list[WorkflowItem] = Field(default_factory=list)


class WorkflowSpec(BaseModel):
    name: str = Field(min_length=1)
    stages: list[WorkflowStage] = Field(default_factory=list)
    runtime_options: dict[str, Any] = Field(default_factory=dict)
    portal_followups: dict[str, Any] = Field(default_factory=dict)


class KpiConfig(BaseModel):
    source_type: str = "compass"
    template_set: str | None = None
    build: str | None = None
    environment: str | None = None
    scenario: str | None = None
    case_start_time: str | None = None
    case_end_time: str | None = None
    report_timestamps_list: list[list[str]] = Field(default_factory=list)


class RunCreateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    testline: str = Field(min_length=1)
    robotcase_path: str | None = None
    executor_type: ExecutorType = "robot"
    workflow_name: str | None = None
    workflow_spec: WorkflowSpec | None = None
    build: str | None = None
    scenario: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    enable_kpi_generator: bool = False
    enable_kpi_anomaly_detector: bool = False
    kpi_config: KpiConfig | None = None


class RunCreateResponse(BaseModel):
    run_id: str
    executor_type: ExecutorType
    status: str
    message: str


class RunListItem(BaseModel):
    run_id: str
    executor_type: ExecutorType
    workflow_name: str | None = None
    testline: str
    robotcase_path: str | None = None
    build: str | None = None
    scenario: str | None = None
    status: str
    message: str
    enable_kpi_generator: bool
    enable_kpi_anomaly_detector: bool
    jenkins_build_ref: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    created_at: str
    updated_at: str


class RunListResponse(BaseModel):
    items: list[RunListItem]


class RunDetailResponse(BaseModel):
    run_id: str
    executor_type: ExecutorType
    workflow_name: str | None = None
    workflow_spec: WorkflowSpec | None = None
    testline: str
    robotcase_path: str | None = None
    build: str | None = None
    scenario: str | None = None
    status: str
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    enable_kpi_generator: bool
    enable_kpi_anomaly_detector: bool
    kpi_config: KpiConfig | None = None
    artifact_manifest: list[ArtifactDescriptor] = Field(default_factory=list)
    kpi_summary: dict[str, Any] = Field(default_factory=dict)
    detector_summary: dict[str, Any] = Field(default_factory=dict)
    jenkins_build_ref: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    created_at: str
    updated_at: str


class RunArtifactsResponse(BaseModel):
    run_id: str
    items: list[ArtifactDescriptor] = Field(default_factory=list)


class RunKpiResponse(BaseModel):
    run_id: str
    generator_enabled: bool
    detector_enabled: bool
    kpi_config: KpiConfig | None = None
    kpi_summary: dict[str, Any] = Field(default_factory=dict)
    detector_summary: dict[str, Any] = Field(default_factory=dict)
    artifact_manifest: list[ArtifactDescriptor] = Field(default_factory=list)


class RunCallbackRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: str = Field(min_length=1)
    message: str | None = None
    jenkins_build_ref: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    artifact_manifest: list[ArtifactDescriptor] = Field(default_factory=list)
    kpi_summary: dict[str, Any] = Field(default_factory=dict)
    detector_summary: dict[str, Any] = Field(default_factory=dict)


class RunCallbackResponse(BaseModel):
    run_id: str
    status: str
    updated_at: str

