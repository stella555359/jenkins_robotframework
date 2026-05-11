import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, ArtifactDescriptor, ProgressEvent, RunDetail as RunDetailModel } from "../api";

type Props = {
  toolKind: "kpi_generator" | "kpi_detector";
  listPath: string;
};

const TERMINAL_STATUSES = new Set(["passed", "failed", "trigger_failed"]);

export function KpiToolRunDetail({ toolKind, listPath }: Props) {
  const { runId } = useParams<{ runId: string }>();
  const navigate = useNavigate();
  const [run, setRun] = useState<RunDetailModel | null>(null);
  const [events, setEvents] = useState<ProgressEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const logEndRef = useRef<HTMLDivElement>(null);

  const isTerminal = run ? TERMINAL_STATUSES.has(run.status) : false;

  const loadRun = useCallback(async () => {
    if (!runId) return;
    try {
      const detail = await api.getRun(runId);
      setRun(detail);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, [runId]);

  const loadProgress = useCallback(async () => {
    if (!runId) return;
    try {
      const data = await api.getRunProgress(runId);
      setEvents(data.events);
    } catch {
      // best effort
    }
  }, [runId]);

  // Initial load
  useEffect(() => {
    loadRun();
    loadProgress();
  }, [loadRun, loadProgress]);

  // Poll while not terminal
  useEffect(() => {
    if (isTerminal) return;
    const timer = setInterval(() => {
      loadRun();
      loadProgress();
    }, 3000);
    return () => clearInterval(timer);
  }, [isTerminal, loadRun, loadProgress]);

  // Auto-scroll log
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events]);

  async function handleDelete() {
    if (!runId || !confirm(`Delete run ${runId}?`)) return;
    try {
      await api.deleteRun(runId);
      navigate(listPath);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : String(err));
    }
  }

  async function handleRebuild() {
    if (!runId) return;
    try {
      const resp = await api.rebuildRun(runId);
      navigate(`${listPath}/${resp.new_run_id}`);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : String(err));
    }
  }

  if (loading) return <p className="muted">Loading…</p>;
  if (error) return <div className="error">{error}</div>;
  if (!run) return <div className="error">Run not found.</div>;

  const metadata = run.metadata || {};
  const chainedFrom = metadata.chained_from as string | undefined;
  const autoDetect = metadata.auto_detect as boolean | undefined;

  const statusCls = `badge status-${run.status.replace(/_/g, "-")}`;

  return (
    <div className="panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">{toolKind === "kpi_generator" ? "KPI Generator" : "KPI Anomaly Detector"}</p>
          <h2>{run.run_id}</h2>
        </div>
        <div className="actions">
          <button className="small secondary" onClick={handleRebuild}>Rebuild</button>
          <button className="small danger-btn" onClick={handleDelete}>Delete</button>
          <Link className="button small secondary" to={listPath}>← Back</Link>
        </div>
      </div>

      {/* Summary info */}
      <div className="summary-grid">
        <div><span>Status</span><strong><span className={statusCls}>{run.status}</span></strong></div>
        <div><span>Testline</span><strong>{run.testline}</strong></div>
        <div><span>Build</span><strong>{run.build || "-"}</strong></div>
        <div><span>Created</span><strong>{run.created_at ? new Date(run.created_at).toLocaleString() : "-"}</strong></div>
        {run.started_at && <div><span>Started</span><strong>{new Date(run.started_at).toLocaleString()}</strong></div>}
        {run.finished_at && <div><span>Finished</span><strong>{new Date(run.finished_at).toLocaleString()}</strong></div>}
      </div>

      {/* Chained links */}
      {chainedFrom && (
        <div className="detail-section" style={{ marginTop: 16 }}>
          <p className="muted" style={{ fontSize: 13 }}>
            🔗 Chained from Generator run: <Link to={`/kpi/generator/${chainedFrom}`}>{chainedFrom}</Link>
          </p>
        </div>
      )}
      {autoDetect && toolKind === "kpi_generator" && (
        <div className="detail-section" style={{ marginTop: 16 }}>
          <p className="muted" style={{ fontSize: 13 }}>
            ⚡ Auto Detect enabled — Detector will run automatically after completion.
          </p>
        </div>
      )}

      {/* Message */}
      {run.message && (
        <div className="detail-section" style={{ marginTop: 16 }}>
          <h3 style={{ margin: "0 0 8px" }}>Message</h3>
          <p style={{ margin: 0 }}>{run.message}</p>
        </div>
      )}

      {/* Real-time Progress Log */}
      <div className="detail-section" style={{ marginTop: 16 }}>
        <div className="detail-section-header">
          <h3>Progress Log</h3>
          {!isTerminal && <span className="badge status-running">Live</span>}
        </div>
        <div className="progress-log">
          {events.length === 0 ? (
            <p className="muted" style={{ margin: 0, fontSize: 13 }}>
              {isTerminal ? "No progress events recorded." : "Waiting for progress events…"}
            </p>
          ) : (
            events.map((evt, i) => (
              <div key={i} className={`progress-event ${i === events.length - 1 && !isTerminal ? "progress-event-active" : ""}`}>
                <span className="progress-event-dot" />
                <span className="progress-event-stage">{evt.stage}</span>
                <span className="progress-event-msg">{evt.message}</span>
                <span className="progress-event-time">{evt.timestamp}</span>
              </div>
            ))
          )}
          <div ref={logEndRef} />
        </div>
      </div>

      {/* Artifacts */}
      {run.artifact_manifest && run.artifact_manifest.length > 0 && (
        <div className="detail-section" style={{ marginTop: 16 }}>
          <h3 style={{ margin: "0 0 8px" }}>Artifacts</h3>
          <div className="artifact-compact">
            {run.artifact_manifest.map((art: ArtifactDescriptor, i: number) => (
              <span key={i} className="artifact-chip">
                {art.path ? (
                  <span title={art.path}>{art.label}</span>
                ) : (
                  art.label
                )}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* KPI Summary / Detector Summary */}
      {toolKind === "kpi_generator" && Object.keys(run.kpi_summary).length > 0 && (
        <div className="detail-section" style={{ marginTop: 16 }}>
          <details>
            <summary>KPI Summary (JSON)</summary>
            <pre className="json-compact">{JSON.stringify(run.kpi_summary, null, 2)}</pre>
          </details>
        </div>
      )}
      {toolKind === "kpi_detector" && Object.keys(run.detector_summary).length > 0 && (
        <div className="detail-section" style={{ marginTop: 16 }}>
          <details>
            <summary>Detector Summary (JSON)</summary>
            <pre className="json-compact">{JSON.stringify(run.detector_summary, null, 2)}</pre>
          </details>
        </div>
      )}

      {/* Full Metadata */}
      <div className="detail-section" style={{ marginTop: 16 }}>
        <details>
          <summary>Full Metadata</summary>
          <pre className="json-compact">{JSON.stringify(metadata, null, 2)}</pre>
        </details>
      </div>
    </div>
  );
}
