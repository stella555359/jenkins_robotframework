import { NavLink, Outlet } from "react-router-dom";

const title = import.meta.env.VITE_APP_TITLE || "Automation Portal";

export default function App() {
  return (
    <div className="layout">
      <aside className="sidebar">
        <p className="sidebar-brand">{title}</p>

        <div className="sidebar-section">
          <div className="sidebar-section-label">Robot Execution</div>
          <NavLink to="/runs">Run List</NavLink>
          <NavLink to="/runs/new">New Robot Run</NavLink>
        </div>

        <div className="sidebar-section">
          <div className="sidebar-section-label">KPI Tools</div>
          <span className="disabled-link">
            KPI Generator <span className="coming-soon-tag">Soon</span>
          </span>
          <span className="disabled-link">
            Anomaly Detector <span className="coming-soon-tag">Soon</span>
          </span>
        </div>

        <div className="sidebar-section">
          <div className="sidebar-section-label">Test Workflow</div>
          <span className="disabled-link">
            Workflow Designer <span className="coming-soon-tag">Soon</span>
          </span>
        </div>
      </aside>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
