import { DragEvent, FormEvent, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, DispatchBackend, OperationDescriptor, RunCreatePayload } from "../api";

type SelectedUe = {
  ue_index: number;
  label: string;
  ue_type: string;
  ue_family?: string;
};

type RowItem = {
  item_id: string;
  model: string;
  label: string;
  ue_scope: Record<string, unknown>;
  params: Record<string, unknown>;
};

type WorkflowRow = {
  row_id: string;
  items: RowItem[];
};

const DEFAULT_UES: SelectedUe[] = [
  { ue_index: 1, label: "_android", ue_type: "qct_dx50", ue_family: "qualcomm" },
  { ue_index: 2, label: "_sigspark_1", ue_type: "huawei_sigspark", ue_family: "pioneer" },
  { ue_index: 3, label: "_sigspark_2", ue_type: "huawei_sigspark", ue_family: "pioneer" },
  { ue_index: 4, label: "_sigspark_3", ue_type: "huawei_sigspark", ue_family: "pioneer" },
  { ue_index: 5, label: "_sigspark_4", ue_type: "huawei_sigspark", ue_family: "pioneer" },
  { ue_index: 6, label: "_sigspark_5", ue_type: "huawei_sigspark", ue_family: "pioneer" },
  { ue_index: 7, label: "_sigspark_6", ue_type: "huawei_sigspark", ue_family: "pioneer" },
];

function makeRowItem(operation: OperationDescriptor): RowItem {
  return {
    item_id: `${operation.model}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    model: operation.model,
    label: operation.label,
    ue_scope: { ...operation.default_ue_scope },
    params: { ...operation.default_params },
  };
}

function JsonPreview({ value }: { value: unknown }) {
  return <pre className="json-compact">{JSON.stringify(value, null, 2)}</pre>;
}

export function WorkflowBuilder() {
  const navigate = useNavigate();
  const [catalog, setCatalog] = useState<OperationDescriptor[]>([]);
  const [rows, setRows] = useState<WorkflowRow[]>([{ row_id: "row-1", items: [] }]);
  const [testline, setTestline] = useState("7_5_UTE5G402T813");
  const [build, setBuild] = useState("");
  const [workflowName, setWorkflowName] = useState("Python KPI Runner Dry Run");
  const [dispatchBackend, setDispatchBackend] = useState<DispatchBackend>("worker");
  const [selectedUeIndexes, setSelectedUeIndexes] = useState<number[]>([1, 2]);
  const [draggedModel, setDraggedModel] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    api
      .getOperationCatalog()
      .then((response) => setCatalog(response.items))
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load operation catalog."));
  }, []);

  const selectedUes = useMemo(
    () => DEFAULT_UES.filter((ue) => selectedUeIndexes.includes(ue.ue_index)),
    [selectedUeIndexes],
  );

  const allModels = useMemo(() => rows.flatMap((row) => row.items.map((item) => item.model)), [rows]);

  const requiresUe = useMemo(() => {
    const requires = new Set(catalog.filter((item) => item.requires_ue).map((item) => item.model));
    return allModels.some((model) => requires.has(model));
  }, [catalog, allModels]);

  const workflowSpec = useMemo(
    () => ({
      name: workflowName,
      stages: rows
        .filter((row) => row.items.length > 0)
        .map((row, index) => ({
          stage_id: index + 1,
          stage_name: `step-${index + 1}`,
          execution_mode: row.items.length > 1 ? ("parallel" as const) : ("serial" as const),
          items: row.items.map((item, itemIndex) => ({
            item_id: item.item_id,
            model: item.model,
            enabled: true,
            order: (itemIndex + 1) * 10,
            execution_mode: row.items.length > 1 ? ("parallel" as const) : ("serial" as const),
            continue_on_failure: item.model === "detach",
            ue_scope: item.ue_scope,
            params: item.params,
          })),
        })),
      runtime_options: {
        dry_run: true,
        stop_on_failure: true,
        max_parallel_workers: 4,
        log_level: "INFO",
      },
      portal_followups: {},
    }),
    [rows, workflowName],
  );

  const runnerRequest = useMemo(
    () => ({
      testline,
      ue_selection: {
        selected_ues: requiresUe ? selectedUes : [],
      },
      traffic_plan: {
        stages: workflowSpec.stages,
      },
      runtime_options: workflowSpec.runtime_options,
    }),
    [requiresUe, selectedUes, testline, workflowSpec],
  );

  function addOperationToRow(operation: OperationDescriptor, rowId: string) {
    setRows((current) =>
      current.map((row) =>
        row.row_id === rowId ? { ...row, items: [...row.items, makeRowItem(operation)] } : row,
      ),
    );
  }

  function addNewRow() {
    setRows((current) => [...current, { row_id: `row-${Date.now()}`, items: [] }]);
  }

  function removeRow(rowId: string) {
    setRows((current) => {
      const filtered = current.filter((row) => row.row_id !== rowId);
      return filtered.length === 0 ? [{ row_id: `row-${Date.now()}`, items: [] }] : filtered;
    });
  }

  function removeItem(rowId: string, itemId: string) {
    setRows((current) =>
      current.map((row) =>
        row.row_id === rowId ? { ...row, items: row.items.filter((item) => item.item_id !== itemId) } : row,
      ),
    );
  }

  function handleDropOnRow(event: DragEvent<HTMLDivElement>, rowId: string) {
    event.preventDefault();
    const model = draggedModel || event.dataTransfer.getData("text/plain");
    const operation = catalog.find((item) => item.model === model);
    if (operation) addOperationToRow(operation, rowId);
    setDraggedModel(null);
  }

  function handleDropOnNewRow(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    const model = draggedModel || event.dataTransfer.getData("text/plain");
    const operation = catalog.find((item) => item.model === model);
    if (operation) {
      const newRowId = `row-${Date.now()}`;
      setRows((current) => [...current, { row_id: newRowId, items: [makeRowItem(operation)] }]);
    }
    setDraggedModel(null);
  }

  function toggleUe(ueIndex: number) {
    setSelectedUeIndexes((current) =>
      current.includes(ueIndex) ? current.filter((item) => item !== ueIndex) : [...current, ueIndex].sort((a, b) => a - b),
    );
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    if (requiresUe && selectedUes.length === 0) {
      setError("At least one UE is required by the selected operations.");
      return;
    }
    setIsSubmitting(true);
    try {
      const payload: RunCreatePayload = {
        testline: testline.trim(),
        executor_type: "python_orchestrator",
        dispatch_backend: dispatchBackend,
        workflow_spec: workflowSpec,
        build: build.trim() || undefined,
        metadata: {
          dispatch_backend: dispatchBackend,
          selected_ues: requiresUe ? selectedUes : [],
          runner_request: runnerRequest,
          portal_workflow_builder: "v2",
        },
        enable_kpi_generator: allModels.includes("kpi_generator"),
        enable_kpi_anomaly_detector: allModels.includes("kpi_detector"),
      };
      const created = await api.createRun(payload);
      await api.triggerRun(created.run_id);
      navigate(`/workflows/${created.run_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit workflow.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Test Workflow</p>
          <h2>Python KPI Workflow Builder</h2>
        </div>
        <p className="muted">
          Drag operations to Selected Operations. Same row = parallel, different rows = serial (top to bottom).
        </p>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="form-grid">
          <label>
            Testline
            <input value={testline} onChange={(event) => setTestline(event.target.value)} required />
          </label>
          <label>
            Workflow name
            <input value={workflowName} onChange={(event) => setWorkflowName(event.target.value)} required />
          </label>
          <label>
            Dispatch backend
            <select value={dispatchBackend} onChange={(event) => setDispatchBackend(event.target.value as DispatchBackend)}>
              <option value="worker">worker</option>
              <option value="jenkins">jenkins</option>
            </select>
          </label>
          <label>
            Build
            <input value={build} onChange={(event) => setBuild(event.target.value)} placeholder="Optional" />
          </label>
        </div>

        {/* ── Supported Operations ─────────────────────── */}
        <div className="supported-operations">
          <h3>Supported Operations</h3>
          <div className="operation-chip-grid">
            {catalog.map((operation) => (
              <button
                className="operation-chip"
                draggable
                key={operation.model}
                onClick={() => {
                  const lastRow = rows[rows.length - 1];
                  addOperationToRow(operation, lastRow.row_id);
                }}
                onDragStart={(event) => {
                  setDraggedModel(operation.model);
                  event.dataTransfer.setData("text/plain", operation.model);
                }}
                type="button"
              >
                <strong>{operation.label}</strong>
                <span className="chip-tag">{operation.requires_ue ? "UE" : "No UE"}</span>
              </button>
            ))}
          </div>
        </div>

        {/* ── Selected Operations ─────────────────────── */}
        <div className="selected-operations">
          <div className="selected-operations-header">
            <h3>Selected Operations</h3>
            <button className="small" type="button" onClick={addNewRow}>+ Add Row</button>
          </div>
          <p className="muted" style={{ margin: "0 0 8px" }}>
            Each row executes in parallel. Rows run serially from top to bottom.
          </p>

          {rows.map((row, rowIndex) => (
            <div
              className="workflow-row"
              key={row.row_id}
              onDragOver={(event) => event.preventDefault()}
              onDrop={(event) => handleDropOnRow(event, row.row_id)}
            >
              <div className="workflow-row-header">
                <span className="row-label">
                  Row {rowIndex + 1}
                  {row.items.length > 1 ? " (parallel)" : row.items.length === 1 ? " (serial)" : ""}
                </span>
                <button className="small secondary" type="button" onClick={() => removeRow(row.row_id)}>
                  Remove Row
                </button>
              </div>
              <div className="workflow-row-items">
                {row.items.length === 0 ? (
                  <p className="muted drop-hint">Drop operations here</p>
                ) : (
                  row.items.map((item) => (
                    <div className="workflow-row-item" key={item.item_id}>
                      <span>{item.label}</span>
                      <button
                        className="small secondary"
                        type="button"
                        onClick={() => removeItem(row.row_id, item.item_id)}
                      >
                        ×
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          ))}

          <div
            className="workflow-row workflow-row-new"
            onDragOver={(event) => event.preventDefault()}
            onDrop={handleDropOnNewRow}
          >
            <p className="muted">Drop here to create a new row</p>
          </div>
        </div>

        <div className="detail-section">
          <div className="detail-section-header">
            <h3>UE Selection {requiresUe ? "" : "(not required by current workflow)"}</h3>
          </div>
          <div className="ue-grid">
            {DEFAULT_UES.map((ue) => (
              <label className="checkbox-card" key={ue.ue_index}>
                <input
                  checked={selectedUeIndexes.includes(ue.ue_index)}
                  disabled={!requiresUe}
                  onChange={() => toggleUe(ue.ue_index)}
                  type="checkbox"
                />
                <span>{ue.label}</span>
                <small>{ue.ue_type}</small>
              </label>
            ))}
          </div>
        </div>

        <details className="detail-section">
          <summary>Generated runner request preview</summary>
          <JsonPreview value={runnerRequest} />
        </details>

        {error ? <p className="error">{error}</p> : null}

        <div className="actions">
          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Submitting..." : "Create And Trigger"}
          </button>
        </div>
      </form>
    </section>
  );
}
