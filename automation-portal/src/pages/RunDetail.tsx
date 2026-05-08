import { useCallback, useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { api, ArtifactDescriptor, RunDetail as RunDetailModel, RunKpi } from "../api";

type LocationState = {
  triggerError?: string;
};

function JsonBlock({ value }: { value: unknown }) {
  return <pre className="json">{JSON.stringify(value, null, 2)}</pre>;
}

function ArtifactList({ items }: { items: ArtifactDescriptor[] }) {
  if (items.length === 0) {
    return <p className="muted">No artifacts reported yet.</p>;
  }

  return (
    <ul className="artifact-list">
      {items.map((item, index) => (
        <li key={`${item.kind}-${index}`}>
          <strong>{item.label}</strong>
          <span>{item.kind}</span>
          {item.url ? (
            <a href={item.url} target="_blank" rel="noreferrer">
              Open
            </a>
          ) : (
            <code>{item.path || "-"}</code>
          )}
        </li>
      ))}
    </ul>
  );
}

export function RunDetail() {
  const { runId = "" } = useParams();
  const location = useLocation();
  const triggerError = (location.state as LocationState | null)?.triggerError;
  const [detail, setDetail] = useState<RunDetailModel | null>(null);
  const [artifacts, setArtifacts] = useState<ArtifactDescriptor[]>([]);
  const [kpi, setKpi] = useState<RunKpi | null>(null);
  const [error, setError] = useState<string | null>(triggerError || null);
  const [isLoading, setIsLoading] = useState(true);
  const [isTriggering, setIsTriggering] = useState(false);

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

  const canRetryTrigger = detail?.executor_type === "robot" && ["created", "trigger_failed"].includes(detail.status);

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
          <Link className="button secondary" to="/runs">
            Back
          </Link>
        </div>
      </div>

      {isLoading ? <p className="muted">Loading run detail...</p> : null}
      {error ? <p className="error">{error}</p> : null}

      {detail ? (
        <>
          <div className="summary-grid">
            <div>
              <span>Status</span>
              <strong className={`badge status-${detail.status.replace(/_/g, "-")}`}>{detail.status}</strong>
            </div>
            <div>
              <span>Executor</span>
              <strong>{detail.executor_type}</strong>
            </div>
            <div>
              <span>Testline</span>
              <strong>{detail.testline}</strong>
            </div>
            <div>
              <span>Build</span>
              <strong>{detail.build || "-"}</strong>
            </div>
            <div className="wide">
              <span>Robot case</span>
              <strong>{detail.robotcase_path || "-"}</strong>
            </div>
            <div className="wide">
              <span>Jenkins ref</span>
              <strong>{detail.jenkins_build_ref || "-"}</strong>
            </div>
            <div className="wide">
              <span>Message</span>
              <strong>{detail.message}</strong>
            </div>
          </div>

          <div className="detail-grid">
            <article>
              <h3>Artifacts</h3>
              <ArtifactList items={artifacts} />
            </article>
            <article>
              <h3>KPI</h3>
              <p className="muted">
                Generator: {kpi?.generator_enabled ? "enabled" : "disabled"} | Detector:{" "}
                {kpi?.detector_enabled ? "enabled" : "disabled"}
              </p>
              <JsonBlock value={{ kpi_summary: kpi?.kpi_summary || {}, detector_summary: kpi?.detector_summary || {} }} />
            </article>
            <article>
              <h3>Metadata</h3>
              <JsonBlock value={detail.metadata} />
            </article>
            <article>
              <h3>Timing</h3>
              <JsonBlock
                value={{
                  created_at: detail.created_at,
                  updated_at: detail.updated_at,
                  started_at: detail.started_at,
                  finished_at: detail.finished_at
                }}
              />
            </article>
          </div>
        </>
      ) : null}
    </section>
  );
}
