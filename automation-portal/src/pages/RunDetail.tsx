import { useCallback, useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { api, ArtifactDescriptor, jenkinsArtifactUrl, jenkinsJobUrl, RunDetail as RunDetailModel, RunKpi } from "../api";

type LocationState = {
  triggerError?: string;
};

function JsonBlock({ value }: { value: unknown }) {
  return <pre className="json">{JSON.stringify(value, null, 2)}</pre>;
}

function ArtifactList({ items, buildRef }: { items: ArtifactDescriptor[]; buildRef?: string | null }) {
  if (items.length === 0) {
    return <p className="muted">No artifacts reported yet.</p>;
  }

  return (
    <ul className="artifact-list">
      {items.map((item, index) => {
        const directUrl = item.url || (item.path ? jenkinsArtifactUrl(buildRef, item.path) : null);
        const isHtml = item.label.endsWith(".html") || item.content_type === "text/html";
        return (
          <li key={`${item.kind}-${index}`}>
            <span className="artifact-icon">{isHtml ? "📄" : "📎"}</span>
            <div className="artifact-info">
              <div className="artifact-label">{item.label}</div>
              {item.path ? <div className="artifact-path">{item.path}</div> : null}
            </div>
            <div className="artifact-actions">
              {directUrl ? (
                <a href={directUrl} target="_blank" rel="noreferrer">
                  {isHtml ? "Open" : "Download"}
                </a>
              ) : null}
            </div>
          </li>
        );
      })}
    </ul>
  );
}

function JenkinsBuildLink({ buildRef }: { buildRef: string | null | undefined }) {
  const url = jenkinsJobUrl(buildRef);
  if (!url || !buildRef) return null;
  return (
    <a className="jenkins-link" href={url} target="_blank" rel="noreferrer" title="View build in Jenkins">
      <span className="jenkins-link-icon">⚙</span> {buildRef}
    </a>
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

  // Find the primary log.html artifact for quick access
  const logHtmlArtifact = artifacts.find(
    (a) => a.label === "log.html" || a.label.endsWith("/log.html")
  );
  const logHtmlUrl = logHtmlArtifact
    ? logHtmlArtifact.url || (logHtmlArtifact.path ? jenkinsArtifactUrl(detail?.jenkins_build_ref, logHtmlArtifact.path) : null)
    : null;

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
            <div className="wide">
              <span>Jenkins Build</span>
              {detail.jenkins_build_ref ? (
                <JenkinsBuildLink buildRef={detail.jenkins_build_ref} />
              ) : (
                <strong className="muted">-</strong>
              )}
            </div>
            {logHtmlUrl ? (
              <div className="wide">
                <span>Robot Log</span>
                <a className="jenkins-link" href={logHtmlUrl} target="_blank" rel="noreferrer">
                  <span className="jenkins-link-icon">📄</span> Open log.html
                </a>
              </div>
            ) : null}
            <div className="wide">
              <span>Message</span>
              <strong>{detail.message}</strong>
            </div>
          </div>

          <div className="detail-grid">
            <article>
              <h3>Artifacts ({artifacts.length})</h3>
              <ArtifactList items={artifacts} buildRef={detail.jenkins_build_ref} />
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
