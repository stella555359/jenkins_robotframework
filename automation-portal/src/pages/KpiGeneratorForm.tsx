import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";

/** Extract Txxx/Txxxx environment code from a testline string. */
function deriveEnvironment(testline: string): string {
  const match = testline.match(/T(\d{3,4})/i);
  return match ? match[0].toUpperCase() : "";
}

type CompassFields = {
  testline: string;
  template_set_name: string;
  template_names: string;
  build: string;
  scenario: string;
  report_timestamps_list: string;
  timestamp_delta_minutes: string;
  max_interval_workers: string;
  compass_username: string;
  compass_password: string;
};

type ScoutFields = {
  testline: string;
  scout_report_path: string;
  dist_name_filter: string;
  build: string;
  scenario: string;
};

const INITIAL_COMPASS: CompassFields = {
  testline: "",
  template_set_name: "",
  template_names: "",
  build: "",
  scenario: "",
  report_timestamps_list: "",
  timestamp_delta_minutes: "",
  max_interval_workers: "",
  compass_username: "",
  compass_password: "",
};

const INITIAL_SCOUT: ScoutFields = {
  testline: "",
  scout_report_path: "",
  dist_name_filter: "",
  build: "",
  scenario: "",
};

export function KpiGeneratorForm() {
  const navigate = useNavigate();
  const [tab, setTab] = useState<"compass" | "scout">("compass");
  const [compass, setCompass] = useState<CompassFields>(INITIAL_COMPASS);
  const [scout, setScout] = useState<ScoutFields>(INITIAL_SCOUT);
  const [autoDetect, setAutoDetect] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const compassEnv = deriveEnvironment(compass.testline);
  const scoutEnv = deriveEnvironment(scout.testline);

  const handleCompass = (field: keyof CompassFields) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setCompass((prev) => ({ ...prev, [field]: e.target.value }));

  const handleScout = (field: keyof ScoutFields) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setScout((prev) => ({ ...prev, [field]: e.target.value }));

  async function submit() {
    setError(null);
    setSubmitting(true);
    try {
      if (tab === "compass") {
        if (!compass.testline || !compass.build || !compass.scenario) {
          throw new Error("Testline, Build, and Scenario are required.");
        }
        if (!compass.template_set_name && !compass.template_names) {
          throw new Error("At least one of Template Set Name or Template Names is required.");
        }
        const payload: Record<string, unknown> = {
          mode: "compass",
          template_set_name: compass.template_set_name,
          template_names: compass.template_names,
          build: compass.build,
          environment: compassEnv,
          scenario: compass.scenario,
          report_timestamps_list: compass.report_timestamps_list,
        };
        if (compass.timestamp_delta_minutes) payload.timestamp_delta_minutes = Number(compass.timestamp_delta_minutes);
        if (compass.max_interval_workers) payload.max_interval_workers = Number(compass.max_interval_workers);
        if (compass.compass_username) payload.compass_username = compass.compass_username;
        if (compass.compass_password) payload.compass_password = compass.compass_password;

        const resp = await api.createToolRun({
          tool_kind: "kpi_generator",
          payload,
          testline: compass.testline,
          build: compass.build,
          metadata: { auto_detect: autoDetect },
        });
        navigate(`/kpi/generator/${resp.run_id}`);
      } else {
        if (!scout.testline || !scout.build || !scout.scenario) {
          throw new Error("Testline, Build, and Scenario are required.");
        }
        if (!scout.scout_report_path || !scout.dist_name_filter) {
          throw new Error("Scout Report Path and Dist Name Filter are required.");
        }
        const payload: Record<string, unknown> = {
          mode: "scout",
          scout_report_path: scout.scout_report_path,
          dist_name_filter: scout.dist_name_filter,
          build: scout.build,
          environment: scoutEnv,
          scenario: scout.scenario,
        };

        const resp = await api.createToolRun({
          tool_kind: "kpi_generator",
          payload,
          testline: scout.testline,
          build: scout.build,
          metadata: { auto_detect: autoDetect },
        });
        navigate(`/kpi/generator/${resp.run_id}`);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">KPI Tools</p>
          <h2>New KPI Generator Run</h2>
        </div>
      </div>

      <div className="tab-bar">
        <button className={`tab-btn${tab === "compass" ? " tab-active" : ""}`} onClick={() => setTab("compass")} type="button">
          Compass Report
        </button>
        <button className={`tab-btn${tab === "scout" ? " tab-active" : ""}`} onClick={() => setTab("scout")} type="button">
          Scout Report Convert
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      {tab === "compass" ? (
        <div className="form-grid" style={{ marginTop: 16 }}>
          <label>
            Testline *
            <input value={compass.testline} onChange={handleCompass("testline")} placeholder="e.g. 7_5_UTE5G402T813" />
          </label>
          <label>
            Environment <span className="muted">(auto)</span>
            <input value={compassEnv} readOnly className="readonly-input" />
          </label>
          <label>
            Template Set Name
            <input value={compass.template_set_name} onChange={handleCompass("template_set_name")} placeholder="e.g. 26R2" />
          </label>
          <label>
            Build *
            <input value={compass.build} onChange={handleCompass("build")} placeholder="e.g. 26R2.0126.7" />
          </label>
          <label>
            Scenario *
            <input value={compass.scenario} onChange={handleCompass("scenario")} placeholder="e.g. 7UEs_SFTPDL" />
          </label>
          <label>
            Timestamp Delta (min)
            <input type="number" value={compass.timestamp_delta_minutes} onChange={handleCompass("timestamp_delta_minutes")} placeholder="Optional" />
          </label>
          <label>
            Max Interval Workers
            <input type="number" value={compass.max_interval_workers} onChange={handleCompass("max_interval_workers")} placeholder="Default: 4" />
          </label>
          <label>
            Compass Username
            <input value={compass.compass_username} onChange={handleCompass("compass_username")} placeholder="Optional (env var fallback)" />
          </label>
          <label>
            Compass Password
            <input type="password" value={compass.compass_password} onChange={handleCompass("compass_password")} placeholder="Optional" />
          </label>
          <label className="span-2">
            Template Names
            <textarea rows={3} value={compass.template_names} onChange={handleCompass("template_names")} placeholder="Comma or newline separated template names" />
          </label>
          <label className="span-2">
            Report Timestamps List (JSON)
            <textarea rows={3} value={compass.report_timestamps_list} onChange={handleCompass("report_timestamps_list")} placeholder='e.g. [["2026-05-10 10:00:00","2026-05-10 11:00:00"]]' />
          </label>
        </div>
      ) : (
        <div className="form-grid" style={{ marginTop: 16 }}>
          <label>
            Testline *
            <input value={scout.testline} onChange={handleScout("testline")} placeholder="e.g. 7_5_UTE5G402T813" />
          </label>
          <label>
            Environment <span className="muted">(auto)</span>
            <input value={scoutEnv} readOnly className="readonly-input" />
          </label>
          <label className="span-2">
            Scout Report Path *
            <input value={scout.scout_report_path} onChange={handleScout("scout_report_path")} placeholder="Absolute path to scout xlsx file" />
          </label>
          <label className="span-2">
            Dist Name Filter *
            <input value={scout.dist_name_filter} onChange={handleScout("dist_name_filter")} placeholder="e.g. gNB" />
          </label>
          <label>
            Build *
            <input value={scout.build} onChange={handleScout("build")} placeholder="e.g. 26R2.0126.7" />
          </label>
          <label>
            Scenario *
            <input value={scout.scenario} onChange={handleScout("scenario")} placeholder="e.g. 7UEs_SFTPDL" />
          </label>
        </div>
      )}

      <div style={{ marginTop: 16, display: "flex", alignItems: "center", gap: 16 }}>
        <label style={{ display: "flex", alignItems: "center", gap: 6, cursor: "pointer" }}>
          <input type="checkbox" checked={autoDetect} onChange={(e) => setAutoDetect(e.target.checked)} />
          <span style={{ fontWeight: 600, fontSize: 13 }}>Auto Detect — run KPI Anomaly Detector after generation</span>
        </label>
      </div>

      <div className="actions" style={{ marginTop: 20 }}>
        <button onClick={submit} disabled={submitting}>
          {submitting ? "Creating…" : "Create Generator Run"}
        </button>
        <button className="secondary" onClick={() => navigate("/kpi/generator")} type="button">
          Cancel
        </button>
      </div>
    </div>
  );
}
