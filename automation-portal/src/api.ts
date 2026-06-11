export type ExecutorType = "robot" | "python_orchestrator" | "internal_tool";
export type ToolKind = "kpi_generator" | "kpi_detector";
export type DispatchBackend = "jenkins";

export type ArtifactDescriptor = {
  kind: string;
  label: string;
  path?: string | null;
  url?: string | null;
  content_type?: string | null;
  source?: string | null;
  metadata?: Record<string, unknown>;
};

export type RunListItem = {
  run_id: string;
  executor_type: ExecutorType;
  testline: string;
  robotcase_path?: string | null;
  build?: string | null;
  status: string;
  message: string;
  enable_kpi_generator: boolean;
  enable_kpi_anomaly_detector: boolean;
  jenkins_build_ref?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  created_at: string;
  updated_at: string;
};

export type RunDetail = RunListItem & {
  workflow_spec?: Record<string, unknown> | null;
  metadata: Record<string, unknown>;
  kpi_config?: Record<string, unknown> | null;
  artifact_manifest: ArtifactDescriptor[];
  kpi_summary: Record<string, unknown>;
  detector_summary: Record<string, unknown>;
};

export type RunKpi = {
  run_id: string;
  generator_enabled: boolean;
  detector_enabled: boolean;
  kpi_config?: Record<string, unknown> | null;
  kpi_summary: Record<string, unknown>;
  detector_summary: Record<string, unknown>;
  artifact_manifest: ArtifactDescriptor[];
};

export type AIConfidence = "high" | "medium" | "low";

export type AIAnalysisStatus = "queued" | "running" | "completed" | "failed";
export type AIAnalysisMode = "rules_first" | "cursor_sdk";

export type AIEvidenceRef = {
  kind: string;
  label: string;
  path?: string | null;
  url?: string | null;
  available: boolean;
  metadata?: Record<string, unknown>;
};

export type AILogSummary = {
  one_line_summary: string;
  failed_stage?: string | null;
  failed_command?: string | null;
  key_errors: string[];
  impact?: string | null;
  next_step?: string | null;
};

export type AIRootCause = {
  category: string;
  confidence: AIConfidence;
  symptom: string;
  evidence: Array<{
    source: string;
    excerpt: string;
    stage?: string | null;
    artifact_path?: string | null;
  }>;
  recommended_actions: string[];
  needs_human_confirmation: boolean;
};

export type AITestReport = {
  title: string;
  status: string;
  summary_markdown: string;
  sections: Array<{
    title: string;
    content_markdown: string;
  }>;
};

export type AIAnalysisResult = {
  run_id: string;
  analysis_id: string;
  analysis_status: AIAnalysisStatus;
  analysis_version: string;
  generated_at: string;
  input_refs: AIEvidenceRef[];
  log_summary: AILogSummary;
  root_cause: AIRootCause;
  test_report: AITestReport;
  quality_signals: Record<string, unknown>;
  message?: string | null;
};

export type AIAnalysisCreateResponse = {
  run_id: string;
  analysis_id: string;
  analysis_status: AIAnalysisStatus;
  message: string;
};

export type AIReportResponse = {
  run_id: string;
  report_format: "markdown";
  content: string;
  generated_at: string;
};

export type RunCreatePayload = {
  testline: string;
  robotcase_path?: string;
  executor_type: "robot" | "python_orchestrator";
  dispatch_backend?: DispatchBackend;
  workflow_spec?: Record<string, unknown>;
  build?: string;
  metadata: Record<string, unknown>;
  enable_kpi_generator?: boolean;
  enable_kpi_anomaly_detector?: boolean;
  kpi_config?: Record<string, unknown>;
};

export type RunCreateResponse = {
  run_id: string;
  executor_type: ExecutorType;
  status: string;
  message: string;
};

export type RunTriggerResponse = {
  run_id: string;
  executor_type: ExecutorType;
  status: string;
  message: string;
  scheduler: string;
  dispatch: Record<string, unknown>;
};

export type OperationDescriptor = {
  model: string;
  label: string;
  category: string;
  requires_ue: boolean;
  default_stage: string;
  default_execution_mode: "serial" | "parallel";
  resource_domain: string;
  default_ue_scope: Record<string, unknown>;
  default_params: Record<string, unknown>;
  description: string;
};

export type ToolRunCreatePayload = {
  tool_kind: ToolKind;
  payload: Record<string, unknown>;
  testline?: string;
  build?: string;
  metadata?: Record<string, unknown>;
};

export type ToolRunCreateResponse = {
  run_id: string;
  executor_type: ExecutorType;
  tool_kind: ToolKind;
  status: string;
  message: string;
  handoff: {
    run_id: string;
    tool_kind: ToolKind;
    detail_url: string;
    callback_url: string;
  };
};

export type ProgressEvent = {
  stage: string;
  message: string;
  timestamp: string;
  extra?: Record<string, unknown>;
};

export type RunProgressResponse = {
  run_id: string;
  status: string;
  events: ProgressEvent[];
};

export type RunDeleteResponse = {
  run_id: string;
  deleted: boolean;
  message: string;
};

export type RunRebuildResponse = {
  original_run_id: string;
  new_run_id: string;
  tool_kind: ToolKind;
  status: string;
  message: string;
};

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || "/api").replace(/\/$/, "");
const jenkinsBaseUrl = (import.meta.env.VITE_JENKINS_BASE_URL || "").replace(/\/$/, "");

/** Parse "robot/robot-execution#42" → Jenkins build page URL. */
export function jenkinsJobUrl(buildRef: string | null | undefined): string | null {
  if (!buildRef || !jenkinsBaseUrl) return null;
  const match = buildRef.match(/^(.+)#(\d+)$/);
  if (!match) return null;
  const [, jobName, buildNumber] = match;
  const jobPath = jobName
    .split("/")
    .map((s) => `job/${encodeURIComponent(s)}`)
    .join("/");
  return `${jenkinsBaseUrl}/${jobPath}/${buildNumber}`;
}

/** Build a direct Jenkins archived-artifact URL from a filesystem path. */
export function jenkinsArtifactUrl(buildRef: string | null | undefined, artifactPath: string): string | null {
  const buildUrl = jenkinsJobUrl(buildRef);
  if (!buildUrl) return null;
  const marker = "/artifacts/";
  const idx = artifactPath.indexOf(marker);
  if (idx === -1) return null;
  const relativePath = artifactPath.substring(idx + 1);
  return `${buildUrl}/artifact/${relativePath}`;
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {})
    },
    ...init
  });

  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        message = payload.detail;
      }
    } catch {
      // Keep the HTTP status text when the response is not JSON.
    }
    throw new Error(message);
  }

  return (await response.json()) as T;
}

export const api = {
  createRun(payload: RunCreatePayload) {
    return requestJson<RunCreateResponse>("/runs", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  triggerRun(runId: string) {
    return requestJson<RunTriggerResponse>(`/runs/${encodeURIComponent(runId)}/trigger`, {
      method: "POST"
    });
  },
  listRuns(params?: { executor_type?: string }) {
    const query = new URLSearchParams();
    if (params?.executor_type) query.set("executor_type", params.executor_type);
    const qs = query.toString();
    return requestJson<{ items: RunListItem[] }>(`/runs${qs ? `?${qs}` : ""}`);
  },
  getRun(runId: string) {
    return requestJson<RunDetail>(`/runs/${encodeURIComponent(runId)}`);
  },
  getArtifacts(runId: string) {
    return requestJson<{ run_id: string; items: ArtifactDescriptor[] }>(
      `/runs/${encodeURIComponent(runId)}/artifacts`
    );
  },
  getKpi(runId: string) {
    return requestJson<RunKpi>(`/runs/${encodeURIComponent(runId)}/kpi`);
  },
  async getAiAnalysis(runId: string) {
    try {
      return await requestJson<AIAnalysisResult>(`/runs/${encodeURIComponent(runId)}/ai-analysis`);
    } catch (err) {
      if (err instanceof Error && err.message === "AI analysis not generated.") {
        return null;
      }
      throw err;
    }
  },
  generateAiAnalysis(runId: string) {
    return requestJson<AIAnalysisCreateResponse>(`/runs/${encodeURIComponent(runId)}/ai-analysis`, {
      method: "POST",
      body: JSON.stringify({
        refresh: true,
        analysis_mode: "rules_first" satisfies AIAnalysisMode,
        include_console: true,
        include_artifacts: true,
      }),
    });
  },
  getAiReport(runId: string) {
    return requestJson<AIReportResponse>(`/runs/${encodeURIComponent(runId)}/ai-report`);
  },
  getOperationCatalog() {
    return requestJson<{ items: OperationDescriptor[] }>("/workflow/operation-catalog");
  },
  createToolRun(payload: ToolRunCreatePayload) {
    return requestJson<ToolRunCreateResponse>("/kpi/tool-runs", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  listToolRuns(params?: { tool_kind?: string; status?: string; testline?: string; scenario?: string }) {
    const query = new URLSearchParams();
    if (params?.tool_kind) query.set("tool_kind", params.tool_kind);
    if (params?.status) query.set("status", params.status);
    if (params?.testline) query.set("testline", params.testline);
    if (params?.scenario) query.set("scenario", params.scenario);
    const qs = query.toString();
    return requestJson<{ items: RunListItem[] }>(`/kpi/tool-runs${qs ? `?${qs}` : ""}`);
  },
  getRunProgress(runId: string) {
    return requestJson<RunProgressResponse>(`/runs/${encodeURIComponent(runId)}/progress`);
  },
  deleteRun(runId: string) {
    return requestJson<RunDeleteResponse>(`/runs/${encodeURIComponent(runId)}`, {
      method: "DELETE",
    });
  },
  rebuildRun(runId: string) {
    return requestJson<RunRebuildResponse>(`/runs/${encodeURIComponent(runId)}/rebuild`, {
      method: "POST",
    });
  },
  async uploadFile(file: File): Promise<{ path: string }> {
    const formData = new FormData();
    formData.append("file", file);
    const response = await fetch(`${apiBaseUrl}/uploads`, {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      let message = `${response.status} ${response.statusText}`;
      try {
        const payload = (await response.json()) as { detail?: string };
        if (payload.detail) message = payload.detail;
      } catch { /* keep HTTP status */ }
      throw new Error(message);
    }
    return (await response.json()) as { path: string };
  },
};
