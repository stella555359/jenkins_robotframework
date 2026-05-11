import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, RunListItem, ToolKind } from "../api";

type Props = {
  toolKind: ToolKind;
  title: string;
  newPath: string;
  detailPrefix: string;
};

export function KpiToolRunList({ toolKind, title, newPath, detailPrefix }: Props) {
  const navigate = useNavigate();
  const [items, setItems] = useState<RunListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [filterTestline, setFilterTestline] = useState("");
  const [filterScenario, setFilterScenario] = useState("");

  const load = useCallback(async () => {
    try {
      const params: Record<string, string> = { tool_kind: toolKind };
      if (filterTestline.trim()) params.testline = filterTestline.trim();
      if (filterScenario.trim()) params.scenario = filterScenario.trim();
      const data = await api.listToolRuns(params);
      setItems(data.items);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, [toolKind, filterTestline, filterScenario]);

  useEffect(() => {
    setLoading(true);
    load();
  }, [load]);

  async function handleDelete(runId: string) {
    if (!confirm(`Delete run ${runId}?`)) return;
    try {
      await api.deleteRun(runId);
      setItems((prev) => prev.filter((r) => r.run_id !== runId));
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : String(err));
    }
  }

  async function handleRebuild(runId: string) {
    try {
      const resp = await api.rebuildRun(runId);
      navigate(`${detailPrefix}/${resp.new_run_id}`);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : String(err));
    }
  }

  function statusBadge(status: string) {
    const cls = `badge status-${status.replace(/_/g, "-")}`;
    return <span className={cls}>{status}</span>;
  }

  return (
    <div className="panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">KPI Tools</p>
          <h2>{title}</h2>
        </div>
        <div className="actions">
          <Link className="button" to={newPath}>
            + New Run
          </Link>
        </div>
      </div>

      {/* Filter bar */}
      <div className="filter-bar">
        <label className="filter-item">
          Testline
          <input
            value={filterTestline}
            onChange={(e) => setFilterTestline(e.target.value)}
            placeholder="Filter by testline…"
          />
        </label>
        <label className="filter-item">
          Scenario
          <input
            value={filterScenario}
            onChange={(e) => setFilterScenario(e.target.value)}
            placeholder="Filter by scenario…"
          />
        </label>
      </div>

      {error && <div className="error">{error}</div>}

      {loading ? (
        <p className="muted">Loading…</p>
      ) : items.length === 0 ? (
        <p className="muted">No runs found.</p>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Run ID</th>
                <th>Testline</th>
                <th>Build</th>
                <th>Status</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((run) => (
                <tr key={run.run_id}>
                  <td>
                    <Link to={`${detailPrefix}/${run.run_id}`}>{run.run_id}</Link>
                  </td>
                  <td>{run.testline}</td>
                  <td>{run.build || "-"}</td>
                  <td>{statusBadge(run.status)}</td>
                  <td>{run.created_at ? new Date(run.created_at).toLocaleString() : "-"}</td>
                  <td>
                    <div className="actions">
                      <button className="small secondary" onClick={() => handleRebuild(run.run_id)}>
                        Rebuild
                      </button>
                      <button className="small danger-btn" onClick={() => handleDelete(run.run_id)}>
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
