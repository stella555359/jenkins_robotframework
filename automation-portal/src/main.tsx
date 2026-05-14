import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import App from "./App";
import { RunDetail } from "./pages/RunDetail";
import { RunList } from "./pages/RunList";
import { RobotRunForm } from "./pages/RobotRunForm";
import { KpiGeneratorForm } from "./pages/KpiGeneratorForm";
import { KpiDetectorForm } from "./pages/KpiDetectorForm";
import { KpiToolRunList } from "./pages/KpiToolRunList";
import { KpiToolRunDetail } from "./pages/KpiToolRunDetail";
import { WorkflowBuilder } from "./pages/WorkflowBuilder";
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
          <Route
            path="kpi/generator"
            element={
              <KpiToolRunList
                toolKind="kpi_generator"
                title="KPI Generator Runs"
                newPath="/kpi/generator/new"
                detailPrefix="/kpi/generator"
              />
            }
          />
          <Route path="kpi/generator/new" element={<KpiGeneratorForm />} />
          <Route
            path="kpi/generator/:runId"
            element={<KpiToolRunDetail toolKind="kpi_generator" listPath="/kpi/generator" />}
          />
          <Route
            path="kpi/detector"
            element={
              <KpiToolRunList
                toolKind="kpi_detector"
                title="KPI Anomaly Detector Runs"
                newPath="/kpi/detector/new"
                detailPrefix="/kpi/detector"
              />
            }
          />
          <Route path="kpi/detector/new" element={<KpiDetectorForm />} />
          <Route
            path="kpi/detector/:runId"
            element={<KpiToolRunDetail toolKind="kpi_detector" listPath="/kpi/detector" />}
          />
          <Route path="workflows/new" element={<WorkflowBuilder />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
