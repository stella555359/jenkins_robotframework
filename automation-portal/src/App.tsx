import { NavLink, Outlet } from "react-router-dom";

const title = import.meta.env.VITE_APP_TITLE || "Automation Portal";

export default function App() {
  return (
    <div className="shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">5G gNB Test Automation</p>
          <h1>{title}</h1>
        </div>
        <nav>
          <NavLink to="/runs">Runs</NavLink>
          <NavLink to="/runs/new">New Robot Run</NavLink>
        </nav>
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  );
}
