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
          <NavLink to="/kpi/generator">KPI Generator</NavLink>
          <NavLink to="/kpi/detector">KPI Anomaly Detector</NavLink>
        </div>

        <div className="sidebar-section">
          <div className="sidebar-section-label">Test Workflow</div>
          <NavLink to="/workflows/new">KPI Workflow Builder</NavLink>
        </div>
      </aside>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
