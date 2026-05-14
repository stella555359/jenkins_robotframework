import { useCallback, useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { api, ArtifactDescriptor, jenkinsArtifactUrl, jenkinsJobUrl, RunDetail as RunDetailModel, RunKpi } from "../api";

type LocationState = {
  triggerError?: string;
};

/* ── Pipeline stage progress ──────────────────────────── */

const PIPELINE_STAGES = [
  "Materialize Run Request",
  "Prepare Workspace",
  "Build Robot Command",
  "Run Robot Case",
  "Callback",
] as const;

type StageEntry = {
  name: string;
  status: string;
  started_at?: string;
  finished_at?: string;
  message?: string;
};

function resolveStageStatus(
  stages: StageEntry[] | undefined,
  runStatus: string,
): ("pending" | "started" | "completed" | "failed")[] {
  const result: ("pending" | "started" | "completed" | "failed")[] = PIPELINE_STAGES.map(() => "pending");

  if (stages && stages.length > 0) {
    // Use real stage data from backend
    const stageMap = new Map(stages.map((s) => [s.name, s.status]));
    for (let i = 0; i < PIPELINE_STAGES.length; i++) {
      const real = stageMap.get(PIPELINE_STAGES[i]);
      if (real === "started") result[i] = "started";
      else if (real === "completed") result[i] = "completed";
      else if (real === "failed" || real === "skipped") result[i] = "failed";
    }
  } else if (runStatus === "triggered") {
    // Fallback: just mark first stage as active when triggered
    result[0] = "started";
  }

  // Terminal run status overrides everything
  if (runStatus === "passed") {
    return PIPELINE_STAGES.map(() => "completed");
  }
  if (runStatus === "failed") {
    return PIPELINE_STAGES.map(() => "failed");
  }

  return result;
}

function PipelineProgress({
  status,
  stages,
}: {
  status: string;
  stages?: StageEntry[];
}) {
  if (status === "created" || status === "trigger_failed") return null;

  const stageStatuses = resolveStageStatus(stages, status);

  return (
    <div className="pipeline-progress">
      {PIPELINE_STAGES.map((stage, i) => {
        const s = stageStatuses[i];
        let cls = "pipeline-step";
        if (s === "completed") cls += " step-done";
        else if (s === "started") cls += " step-active";
        else if (s === "failed") cls += " step-failed";
        return (
          <div key={stage} className={cls}>
            <div className="step-dot" />
            <span className="step-label">{stage}</span>
          </div>
        );
      })}
    </div>
  );
}

/* ── Compact info table ───────────────────────────────── */

function InfoTable({ items }: { items: [string, string | null | undefined][] }) {
  return (
    <table className="info-table">
      <tbody>
        {items.map(([label, value]) => (
          <tr key={label}>
            <td className="info-label">{label}</td>
            <td>{value || "-"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/* ── Main component ───────────────────────────────────── */

export function RunDetail() {
  const { runId = "" } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const triggerError = (location.state as LocationState | null)?.triggerError;
  const [detail, setDetail] = useState<RunDetailModel | null>(null);
  const [artifacts, setArtifacts] = useState<ArtifactDescriptor[]>([]);
  const [kpi, setKpi] = useState<RunKpi | null>(null);
  const [error, setError] = useState<string | null>(triggerError || null);
  const [isLoading, setIsLoading] = useState(true);
  const [isTriggering, setIsTriggering] = useState(false);
  const [showMeta, setShowMeta] = useState(false);

  const load = useCallback(async () => {
    if (!runId) {
      return;
    }
    setError(triggerError || null);
    try {
      const [detailResponse, artifactsResponse, kpiResponse] = await Promise.all([
        api.getRun(runId),
        api.getArtifacts(runId),
        api.getKpi(runId)
      ]);
      setDetail(detailResponse);
      setArtifacts(artifactsResponse.items);
      setKpi(kpiResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load run.");
    } finally {
      setIsLoading(false);
    }
  }, [runId, triggerError]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!detail || ["passed", "failed"].includes(detail.status)) {
      return;
    }
    const timer = window.setInterval(() => {
      void load();
    }, 5000);
    return () => window.clearInterval(timer);
  }, [detail, load]);

  async function handleRetryTrigger() {
    if (!runId) {
      return;
    }
    setIsTriggering(true);
    setError(null);
    try {
      await api.triggerRun(runId);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to trigger run.");
      await load();
    } finally {
      setIsTriggering(false);
    }
  }

  const canRetryTrigger = detail && ["robot", "python_orchestrator"].includes(detail.executor_type) && ["created", "trigger_failed"].includes(detail.status);

  async function handleDelete() {
    if (!runId || !confirm(`Delete run ${runId}?`)) return;
    try {
      await api.deleteRun(runId);
      navigate("/runs");
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : String(err));
    }
  }

  // Find the primary log.html artifact for quick access
  const logHtmlArtifact = artifacts.find(
    (a) => a.label === "log.html" || a.label.endsWith("/log.html")
  );
  const logHtmlUrl = logHtmlArtifact
    ? logHtmlArtifact.url || (logHtmlArtifact.path ? jenkinsArtifactUrl(detail?.jenkins_build_ref, logHtmlArtifact.path) : null)
    : null;

  // Build Jenkins artifacts zip URL
  const jenkinsUrl = jenkinsJobUrl(detail?.jenkins_build_ref);
  const artifactsZipUrl = jenkinsUrl ? `${jenkinsUrl}/artifact/artifacts/*zip*/artifacts.zip` : null;

  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Run Detail</p>
          <h2>{runId}</h2>
        </div>
        <div className="actions">
          <button type="button" className="secondary" onClick={() => void load()}>
            Refresh
          </button>
          {canRetryTrigger ? (
            <button type="button" onClick={() => void handleRetryTrigger()} disabled={isTriggering}>
              {isTriggering ? "Triggering..." : "Retry Trigger"}
            </button>
          ) : null}
          <Link className="button secondary" to={`/runs/new?from=${runId}`}>
            Rebuild
          </Link>
          <button type="button" className="secondary danger-btn" onClick={() => void handleDelete()}>
            Delete
          </button>
          <Link className="button secondary" to="/runs">
            Back
          </Link>
        </div>
      </div>

      {isLoading ? <p className="muted">Loading run detail...</p> : null}
      {error ? <p className="error">{error}</p> : null}

      {detail ? (
        <>
          {/* ── Pipeline stage progress ── */}
          <PipelineProgress
            status={detail.status}
            stages={detail.metadata?.pipeline_stages as StageEntry[] | undefined}
          />

          {/* ── Summary cards (2-col grid) ── */}
          <div className="summary-grid">
            <div>
              <span>Status</span>
              <strong className={`badge status-${detail.status.replace(/_/g, "-")}`}>{detail.status}</strong>
            </div>
            <div>
              <span>Testline</span>
              <strong>{detail.testline}</strong>
            </div>
            <div>
              <span>Build</span>
              <strong>{detail.build || "-"}</strong>
            </div>
            <div>
              <span>Robot case</span>
              <strong>{detail.robotcase_path || "-"}</strong>
            </div>
            <div>
              <span>Executor</span>
              <strong>{detail.executor_type}</strong>
            </div>
            <div>
              <span>Dispatch</span>
              <strong>{String(detail.metadata?.dispatch_backend || (detail.executor_type === "robot" ? "jenkins" : "-"))}</strong>
            </div>
            <div>
              <span>Jenkins Build</span>
              {detail.jenkins_build_ref ? (
                <a className="jenkins-link" href={jenkinsUrl || "#"} target="_blank" rel="noreferrer">
                  <span className="jenkins-link-icon">⚙</span> {detail.jenkins_build_ref}
                </a>
              ) : (
                <strong className="muted">-</strong>
              )}
            </div>
            <div>
              <span>Robot Log</span>
              {logHtmlUrl ? (
                <a className="jenkins-link" href={logHtmlUrl} target="_blank" rel="noreferrer">
                  <span className="jenkins-link-icon">📄</span> Open log.html
                </a>
              ) : (
                <strong className="muted">-</strong>
              )}
            </div>
            <div className="wide">
              <span>Message</span>
              <strong>{detail.message}</strong>
            </div>
          </div>

          {/* ── Artifacts (single zip download) ── */}
          <div className="detail-section">
            <div className="detail-section-header">
              <h3>Artifacts ({artifacts.length})</h3>
              {artifactsZipUrl ? (
                <a className="button small secondary" href={artifactsZipUrl} target="_blank" rel="noreferrer">
                  ⬇ Download All (ZIP)
                </a>
              ) : null}
            </div>
            {artifacts.length === 0 ? (
              <p className="muted">No artifacts reported yet.</p>
            ) : (
              <div className="artifact-compact">
                {artifacts.map((item, index) => {
                  const directUrl = item.url || (item.path ? jenkinsArtifactUrl(detail.jenkins_build_ref, item.path) : null);
                  return (
                    <span key={`${item.kind}-${index}`} className="artifact-chip">
                      {directUrl ? (
                        <a href={directUrl} target="_blank" rel="noreferrer">{item.label}</a>
                      ) : (
                        item.label
                      )}
                    </span>
                  );
                })}
              </div>
            )}
          </div>

          {/* ── Metadata / KPI / Timing — compact collapsible ── */}
          <div className="detail-section">
            <div className="detail-section-header">
              <h3>Details</h3>
              <button type="button" className="small secondary" onClick={() => setShowMeta(!showMeta)}>
                {showMeta ? "Collapse" : "Expand"}
              </button>
            </div>
            {!showMeta ? (
              <InfoTable
                items={[
                  ["Created", detail.created_at],
                  ["Started", detail.started_at],
                  ["Finished", detail.finished_at],
                  ["TAF mode", detail.metadata?.taf_mode as string | undefined],
                  ["Robotws ref", detail.metadata?.robotws_ref as string | undefined],
                  ["KPI Generator", kpi?.generator_enabled ? "enabled" : "disabled"],
                  ["Anomaly Detector", kpi?.detector_enabled ? "enabled" : "disabled"],
                ]}
              />
            ) : (
              <div className="meta-expanded">
                <details open>
                  <summary>Timing</summary>
                  <InfoTable
                    items={[
                      ["Created", detail.created_at],
                      ["Updated", detail.updated_at],
                      ["Started", detail.started_at],
                      ["Finished", detail.finished_at],
                    ]}
                  />
                </details>
                <details open>
                  <summary>Metadata</summary>
                  <pre className="json-compact">{JSON.stringify(detail.metadata, null, 2)}</pre>
                </details>
                <details open={detail.executor_type === "python_orchestrator"}>
                  <summary>Workflow Spec</summary>
                  <pre className="json-compact">{JSON.stringify(detail.workflow_spec || {}, null, 2)}</pre>
                </details>
                <details open={detail.executor_type === "python_orchestrator"}>
                  <summary>Runner Request / Result</summary>
                  <pre className="json-compact">
                    {JSON.stringify(
                      {
                        runner_request: detail.metadata?.runner_request || {},
                        runner_result: detail.metadata?.runner_result || detail.metadata?.workflow_result || {},
                        worker_handoff: detail.metadata?.worker_handoff || {},
                      },
                      null,
                      2,
                    )}
                  </pre>
                </details>
                <details>
                  <summary>KPI Summary</summary>
                  <pre className="json-compact">
                    {JSON.stringify({ kpi_summary: kpi?.kpi_summary || {}, detector_summary: kpi?.detector_summary || {} }, null, 2)}
                  </pre>
                </details>
              </div>
            )}
          </div>
        </>
      ) : null}
    </section>
  );
}
