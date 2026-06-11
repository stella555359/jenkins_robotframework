from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


AIAnalysisStatus = Literal["queued", "running", "completed", "failed"]
AIAnalysisMode = Literal["rules_first", "cursor_sdk"]
AIConfidence = Literal["high", "medium", "low"]


class AIAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    refresh: bool = False
    analysis_mode: AIAnalysisMode = "rules_first"
    include_console: bool = True
    include_artifacts: bool = True


class AIAnalysisCreateResponse(BaseModel):
    run_id: str
    analysis_id: str
    analysis_status: AIAnalysisStatus
    message: str


class EvidenceRef(BaseModel):
    kind: str = Field(min_length=1)
    label: str = Field(min_length=1)
    path: str | None = None
    url: str | None = None
    available: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class LogSummary(BaseModel):
    one_line_summary: str = ""
    failed_stage: str | None = None
    failed_command: str | None = None
    key_errors: list[str] = Field(default_factory=list)
    impact: str | None = None
    next_step: str | None = None


class RootCauseEvidence(BaseModel):
    source: str
    excerpt: str
    stage: str | None = None
    artifact_path: str | None = None


class RootCauseAnalysis(BaseModel):
    category: str = "unknown"
    confidence: AIConfidence = "low"
    symptom: str = ""
    evidence: list[RootCauseEvidence] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    needs_human_confirmation: bool = True


class AITestReportSection(BaseModel):
    title: str
    content_markdown: str


class AITestReport(BaseModel):
    title: str = "AI Run Analysis Report"
    status: str = "unknown"
    summary_markdown: str = ""
    sections: list[AITestReportSection] = Field(default_factory=list)


class AIAnalysisResult(BaseModel):
    run_id: str
    analysis_id: str
    analysis_status: AIAnalysisStatus
    analysis_version: str
    generated_at: str
    input_refs: list[EvidenceRef] = Field(default_factory=list)
    log_summary: LogSummary = Field(default_factory=LogSummary)
    root_cause: RootCauseAnalysis = Field(default_factory=RootCauseAnalysis)
    test_report: AITestReport = Field(default_factory=AITestReport)
    quality_signals: dict[str, Any] = Field(default_factory=dict)
    message: str | None = None


class AIReportResponse(BaseModel):
    run_id: str
    report_format: Literal["markdown"] = "markdown"
    content: str
    generated_at: str
