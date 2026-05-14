import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, ProgressEvent, RunDetail as RunDetailModel } from "../api";

type StageEntry = {
  name: string;
  status: string;
  started_at?: string;
  finished_at?: string;
  message?: string;
};

const TERMINAL_STATUSES = new Set(["passed", "failed", "trigger_failed"]);

function StageTimeline({ stages }: { stages: StageEntry[] }) {
  if (stages.length === 0) return null;
  return (
    <div className="pipeline-progress">
      {stages.map((stage) => {
        let cls = "pipeline-step";
        if (stage.status === "completed") cls += " step-done";
        else if (stage.status === "started") cls += " step-active";
        else if (stage.status === "failed" || stage.status === "skipped") cls += " step-failed";
        return (
          <div key={stage.name} className={cls}>
            <div className="step-dot" />
            <span className="step-label">{stage.name}</span>
          </div>
        );
      })}
    </div>
  );
}

export function WorkflowRunDetail() {
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

  useEffect(() => {
    loadRun();
    loadProgress();
  }, [loadRun, loadProgress]);

  useEffect(() => {
    if (isTerminal) return;
    const timer = setInterval(() => {
      loadRun();
      loadProgress();
    }, 3000);
    return () => clearInterval(timer);
  }, [isTerminal, loadRun, loadProgress]);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events]);

  if (loading) return <p className="muted">Loading…</p>;
  if (error) return <div className="error">{error}</div>;
  if (!run) return <div className="error">Run not found.</div>;

  const metadata = run.metadata || {};
  const pipelineStages = (metadata.pipeline_stages as StageEntry[] | undefined) || [];
  const dispatchBackend = String(metadata.dispatch_backend || "-");
  const statusCls = `badge status-${run.status.replace(/_/g, "-")}`;

  // Extract workflow spec stage summary
  const workflowSpec = run.workflow_spec || {};
  const specStages = (workflowSpec.stages as Array<Record<string, unknown>>) || [];

  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Test Workflow</p>
          <h2>{run.run_id}</h2>
        </div>
        <div className="actions">
          <button className="small secondary" onClick={() => { loadRun(); loadProgress(); }}>Refresh</button>
          <Link className="button small secondary" to={`/workflows/new?from=${runId}`}>Rebuild</Link>
          <button className="small danger-btn" onClick={async () => {
            if (!runId || !confirm(`Delete workflow run ${runId}?`)) return;
            try { await api.deleteRun(runId); navigate("/workflows"); }
            catch (err: unknown) { alert(err instanceof Error ? err.message : String(err)); }
          }}>Delete</button>
          <Link className="button small secondary" to="/workflows">← Back</Link>
        </div>
      </div>

      {/* Pipeline stage progress (dynamic from metadata) */}
      {pipelineStages.length > 0 && <StageTimeline stages={pipelineStages} />}

      {/* Summary */}
      <div className="summary-grid">
        <div><span>Status</span><strong><span className={statusCls}>{run.status}</span></strong></div>
        <div><span>Testline</span><strong>{run.testline}</strong></div>
        <div><span>Build</span><strong>{run.build || "-"}</strong></div>
        <div><span>Dispatch</span><strong>{dispatchBackend}</strong></div>
        <div><span>Created</span><strong>{run.created_at ? new Date(run.created_at).toLocaleString() : "-"}</strong></div>
        {run.started_at && <div><span>Started</span><strong>{new Date(run.started_at).toLocaleString()}</strong></div>}
        {run.finished_at && <div><span>Finished</span><strong>{new Date(run.finished_at).toLocaleString()}</strong></div>}
        <div className="wide"><span>Message</span><strong>{run.message}</strong></div>
      </div>

      {/* Workflow Stages overview */}
      {specStages.length > 0 && (
        <div className="detail-section" style={{ marginTop: 16 }}>
          <h3 style={{ margin: "0 0 8px" }}>Workflow Stages ({specStages.length})</h3>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Stage</th>
                  <th>Mode</th>
                  <th>Items</th>
                </tr>
              </thead>
              <tbody>
                {specStages.map((stage, i) => {
                  const items = (stage.items as Array<Record<string, unknown>>) || [];
                  return (
                    <tr key={i}>
                      <td>{String(stage.stage_id ?? i + 1)}</td>
                      <td>{String(stage.stage_name || `step-${i + 1}`)}</td>
                      <td>{String(stage.execution_mode || "-")}</td>
                      <td>{items.map((it) => String(it.model || "")).join(", ") || "-"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Progress Log */}
      <div className="detail-section" style={{ marginTop: 16 }}>
        <div className="detail-section-header">
          <h3>Progress Log</h3>
          {!isTerminal && <span className="badge status-running">Live</span>}
        </div>
        <div className="progress-log">
          {events.length === 0 ? (
            <p className="muted">No progress events yet.</p>
          ) : (
            events.map((ev, i) => (
              <div key={i} className="progress-event">
                <span className="progress-ts">{ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : ""}</span>
                <span className="progress-stage">{ev.stage}</span>
                <span className="progress-msg">{ev.message}</span>
              </div>
            ))
          )}
          <div ref={logEndRef} />
        </div>
      </div>

      {/* Metadata / Spec (collapsible) */}
      <details className="detail-section" style={{ marginTop: 16 }}>
        <summary>Workflow Spec</summary>
        <pre className="json-compact">{JSON.stringify(run.workflow_spec || {}, null, 2)}</pre>
      </details>
      <details className="detail-section" style={{ marginTop: 8 }}>
        <summary>Metadata</summary>
        <pre className="json-compact">{JSON.stringify(metadata, null, 2)}</pre>
      </details>
    </section>
  );
}
