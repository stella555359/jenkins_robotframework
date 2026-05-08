import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import App from "./App";
import { RunDetail } from "./pages/RunDetail";
import { RunList } from "./pages/RunList";
import { RobotRunForm } from "./pages/RobotRunForm";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />}>
          <Route index element={<Navigate to="/runs" replace />} />
          <Route path="runs" element={<RunList />} />
          <Route path="runs/new" element={<RobotRunForm />} />
          <Route path="runs/:runId" element={<RunDetail />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
