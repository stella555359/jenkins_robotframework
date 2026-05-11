import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, jenkinsJobUrl, RunListItem } from "../api";

function StatusBadge({ status }: { status: string }) {
  return <span className={`badge status-${status.replace(/_/g, "-")}`}>{status}</span>;
}

function JenkinsLink({ buildRef }: { buildRef: string | null | undefined }) {
  const url = jenkinsJobUrl(buildRef);
  if (!url) return null;
  return (
    <a className="jenkins-link" href={url} target="_blank" rel="noreferrer" title="Open in Jenkins">
      <span className="jenkins-link-icon">⚙</span> Jenkins
    </a>
  );
}

export function RunList() {
  const [items, setItems] = useState<RunListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadRuns() {
    setError(null);
    try {
      const response = await api.listRuns();
      setItems(response.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load runs.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadRuns();
  }, []);

  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Robot Execution</p>
          <h2>Run List</h2>
        </div>
        <div className="actions">
          <button type="button" className="secondary" onClick={() => void loadRuns()}>
            Refresh
          </button>
          <Link className="button" to="/runs/new">
            New Robot Run
          </Link>
        </div>
      </div>

      {isLoading ? <p className="muted">Loading runs...</p> : null}
      {error ? <p className="error">{error}</p> : null}

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Run ID</th>
              <th>Testline</th>
              <th>Status</th>
              <th>Jenkins</th>
              <th>Updated</th>
              <th>Robot case</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.run_id}>
                <td>
                  <Link to={`/runs/${item.run_id}`}>{item.run_id}</Link>
                </td>
                <td>{item.testline}</td>
                <td>
                  <StatusBadge status={item.status} />
                </td>
                <td>
                  <JenkinsLink buildRef={item.jenkins_build_ref} />
                </td>
                <td>{item.updated_at}</td>
                <td className="muted">{item.robotcase_path || "-"}</td>
                <td>
                  <Link className="button small secondary" to={`/runs/new?from=${item.run_id}`}>
                    Rebuild
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {!isLoading && items.length === 0 ? <p className="muted">No runs yet.</p> : null}
    </section>
  );
}
