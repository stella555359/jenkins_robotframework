import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";

export function KpiDetectorForm() {
  const navigate = useNavigate();
  const [sourceFile, setSourceFile] = useState<File | null>(null);
  const [testline, setTestline] = useState("");
  const [build, setBuild] = useState("");
  const [sheetName, setSheetName] = useState("");
  const [allowScoutSummary, setAllowScoutSummary] = useState(true);
  const [generateHtml, setGenerateHtml] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    setError(null);
    if (!sourceFile) {
      setError("Please select a source file (.xlsx).");
      return;
    }
    setSubmitting(true);
    try {
      // Upload file first, then create run with the server-side path
      const uploaded = await api.uploadFile(sourceFile);

      const payload: Record<string, unknown> = {
        source_file: uploaded.path,
        generate_html: generateHtml ? "true" : "false",
        allow_scout_summary: allowScoutSummary ? "true" : "false",
      };
      if (sheetName.trim()) payload.sheet_name = sheetName.trim();

      const resp = await api.createToolRun({
        tool_kind: "kpi_detector",
        payload,
        testline: testline.trim() || undefined,
        build: build.trim() || undefined,
      });
      navigate(`/kpi/detector/${resp.run_id}`);
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
          <h2>New KPI Anomaly Detector Run</h2>
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      <div className="form-grid" style={{ marginTop: 16 }}>
        <label className="span-2">
          Source File (xlsx) *
          <input
            type="file"
            accept=".xlsx,.xls"
            onChange={(e) => setSourceFile(e.target.files?.[0] ?? null)}
          />
          {sourceFile && <span className="muted" style={{ fontSize: 13 }}>{sourceFile.name}</span>}
        </label>
        <label>
          Testline
          <input value={testline} onChange={(e) => setTestline(e.target.value)} placeholder="e.g. 7_5_UTE5G402T813" />
        </label>
        <label>
          Build
          <input value={build} onChange={(e) => setBuild(e.target.value)} placeholder="e.g. 26R2.0126.7" />
        </label>
        <label>
          Sheet Name
          <input value={sheetName} onChange={(e) => setSheetName(e.target.value)} placeholder="Optional (default: auto)" />
        </label>
        <div style={{ display: "flex", flexDirection: "column", gap: 10, justifyContent: "center" }}>
          <label style={{ display: "flex", alignItems: "center", gap: 6, cursor: "pointer" }}>
            <input type="checkbox" checked={allowScoutSummary} onChange={(e) => setAllowScoutSummary(e.target.checked)} />
            <span style={{ fontWeight: 600, fontSize: 13 }}>Allow Scout Summary</span>
          </label>
          <label style={{ display: "flex", alignItems: "center", gap: 6, cursor: "pointer" }}>
            <input type="checkbox" checked={generateHtml} onChange={(e) => setGenerateHtml(e.target.checked)} />
            <span style={{ fontWeight: 600, fontSize: 13 }}>Generate HTML Report</span>
          </label>
        </div>
      </div>

      <div className="actions" style={{ marginTop: 20 }}>
        <button onClick={submit} disabled={submitting}>
          {submitting ? "Uploading & Creating…" : "Create Detector Run"}
        </button>
        <button className="secondary" onClick={() => navigate("/kpi/detector")} type="button">
          Cancel
        </button>
      </div>
    </div>
  );
}
