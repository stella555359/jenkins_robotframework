import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, RunListItem } from "../api";

function StatusBadge({ status }: { status: string }) {
  return <span className={`badge status-${status.replace(/_/g, "-")}`}>{status}</span>;
}

export function WorkflowRunList() {
  const navigate = useNavigate();
  const [items, setItems] = useState<RunListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await api.listRuns({ executor_type: "python_orchestrator" });
      setItems(data.items);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    setLoading(true);
    load();
  }, [load]);

  async function handleDelete(runId: string) {
    if (!confirm(`Delete workflow run ${runId}?`)) return;
    try {
      await api.deleteRun(runId);
      setItems((prev) => prev.filter((r) => r.run_id !== runId));
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : String(err));
    }
  }

  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Test Workflow</p>
          <h2>Workflow Runs</h2>
        </div>
        <div className="actions">
          <button type="button" className="secondary" onClick={() => { setLoading(true); load(); }}>
            Refresh
          </button>
          <Link className="button" to="/workflows/new">
            + New Workflow
          </Link>
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      {loading ? (
        <p className="muted">Loading…</p>
      ) : items.length === 0 ? (
        <p className="muted">No workflow runs found.</p>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Run ID</th>
                <th>Testline</th>
                <th>Build</th>
                <th>Status</th>
                <th>Dispatch</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((run) => {
                const dispatch = (run as Record<string, unknown>).metadata
                  ? String(((run as Record<string, unknown>).metadata as Record<string, unknown>)?.dispatch_backend || "-")
                  : "-";
                return (
                  <tr key={run.run_id}>
                    <td>
                      <Link to={`/workflows/${run.run_id}`}>{run.run_id}</Link>
                    </td>
                    <td>{run.testline}</td>
                    <td>{run.build || "-"}</td>
                    <td><StatusBadge status={run.status} /></td>
                    <td>{dispatch}</td>
                    <td>{run.created_at ? new Date(run.created_at).toLocaleString() : "-"}</td>
                    <td>
                      <div className="actions">
                        <Link className="button small secondary" to={`/workflows/new?from=${run.run_id}`}>
                          Rebuild
                        </Link>
                        <button className="small danger-btn" onClick={() => handleDelete(run.run_id)}>
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
