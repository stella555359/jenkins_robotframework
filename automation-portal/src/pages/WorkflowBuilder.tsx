import { DragEvent, FormEvent, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, DispatchBackend, OperationDescriptor, RunCreatePayload } from "../api";

type SelectedUe = {
  ue_index: number;
  label: string;
  ue_type: string;
  ue_family?: string;
};

type WorkflowItemDraft = {
  item_id: string;
  model: string;
  label: string;
  enabled: boolean;
  order: number;
  execution_mode: "serial" | "parallel";
  continue_on_failure: boolean;
  ue_scope: Record<string, unknown>;
  params: Record<string, unknown>;
};

type StageDraft = {
  stage_id: number;
  stage_name: string;
  execution_mode: "serial" | "parallel";
  items: WorkflowItemDraft[];
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

const INITIAL_STAGES: StageDraft[] = [
  { stage_id: 1, stage_name: "prepare-ue", execution_mode: "serial", items: [] },
  { stage_id: 2, stage_name: "attach", execution_mode: "serial", items: [] },
  { stage_id: 3, stage_name: "optional-operation", execution_mode: "parallel", items: [] },
  { stage_id: 4, stage_name: "detach", execution_mode: "serial", items: [] },
  { stage_id: 5, stage_name: "kpi-followup", execution_mode: "serial", items: [] },
];

function stageIdForOperation(operation: OperationDescriptor, stages: StageDraft[]): number {
  const matched = stages.find((stage) => stage.stage_name === operation.default_stage);
  return matched?.stage_id || stages[0].stage_id;
}

function makeItem(operation: OperationDescriptor, order: number): WorkflowItemDraft {
  return {
    item_id: `${operation.model}-${Date.now()}-${order}`,
    model: operation.model,
    label: operation.label,
    enabled: true,
    order,
    execution_mode: operation.default_execution_mode,
    continue_on_failure: operation.model === "detach",
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
  const [stages, setStages] = useState<StageDraft[]>(INITIAL_STAGES);
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

  const requiresUe = useMemo(() => {
    const requires = new Set(catalog.filter((item) => item.requires_ue).map((item) => item.model));
    return stages.some((stage) => stage.items.some((item) => item.enabled && requires.has(item.model)));
  }, [catalog, stages]);

  const workflowSpec = useMemo(
    () => ({
      name: workflowName,
      stages: stages.map((stage) => ({
        stage_id: stage.stage_id,
        stage_name: stage.stage_name,
        execution_mode: stage.execution_mode,
        items: stage.items.map((item, index) => ({
          item_id: item.item_id,
          model: item.model,
          enabled: item.enabled,
          order: (index + 1) * 10,
          execution_mode: item.execution_mode,
          continue_on_failure: item.continue_on_failure,
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
    [stages, workflowName],
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

  function addOperationToStage(operation: OperationDescriptor, targetStageId?: number) {
    setStages((current) => {
      const stageId = targetStageId || stageIdForOperation(operation, current);
      return current.map((stage) => {
        if (stage.stage_id !== stageId) return stage;
        return {
          ...stage,
          items: [...stage.items, makeItem(operation, (stage.items.length + 1) * 10)],
        };
      });
    });
  }

  function handleDrop(event: DragEvent<HTMLDivElement>, stageId: number) {
    event.preventDefault();
    const model = draggedModel || event.dataTransfer.getData("text/plain");
    const operation = catalog.find((item) => item.model === model);
    if (operation) addOperationToStage(operation, stageId);
    setDraggedModel(null);
  }

  function toggleUe(ueIndex: number) {
    setSelectedUeIndexes((current) =>
      current.includes(ueIndex) ? current.filter((item) => item !== ueIndex) : [...current, ueIndex].sort((a, b) => a - b),
    );
  }

  function removeItem(stageId: number, itemId: string) {
    setStages((current) =>
      current.map((stage) =>
        stage.stage_id === stageId ? { ...stage, items: stage.items.filter((item) => item.item_id !== itemId) } : stage,
      ),
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
      const models = stages.flatMap((stage) => stage.items.filter((item) => item.enabled).map((item) => item.model));
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
          portal_workflow_builder: "mvp",
        },
        enable_kpi_generator: models.includes("kpi_generator"),
        enable_kpi_anomaly_detector: models.includes("kpi_detector"),
      };
      const created = await api.createRun(payload);
      await api.triggerRun(created.run_id);
      navigate(`/runs/${created.run_id}`);
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
        <p className="muted">Drag operations into stages. UE selection is only required when selected operations need UE.</p>
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

        <div className="workflow-layout">
          <div className="operation-palette">
            <h3>Operations</h3>
            {catalog.map((operation) => (
              <button
                className="operation-card"
                draggable
                key={operation.model}
                onClick={() => addOperationToStage(operation)}
                onDragStart={(event) => {
                  setDraggedModel(operation.model);
                  event.dataTransfer.setData("text/plain", operation.model);
                }}
                type="button"
              >
                <strong>{operation.label}</strong>
                <span>{operation.requires_ue ? "Requires UE" : "No UE"}</span>
              </button>
            ))}
          </div>

          <div className="stage-board">
            {stages.map((stage) => (
              <div
                className="stage-card"
                key={stage.stage_id}
                onDragOver={(event) => event.preventDefault()}
                onDrop={(event) => handleDrop(event, stage.stage_id)}
              >
                <div className="stage-card-header">
                  <strong>{stage.stage_id}. {stage.stage_name}</strong>
                  <select
                    value={stage.execution_mode}
                    onChange={(event) =>
                      setStages((current) =>
                        current.map((item) =>
                          item.stage_id === stage.stage_id
                            ? { ...item, execution_mode: event.target.value as "serial" | "parallel" }
                            : item,
                        ),
                      )
                    }
                  >
                    <option value="serial">serial</option>
                    <option value="parallel">parallel</option>
                  </select>
                </div>
                {stage.items.length === 0 ? <p className="muted">Drop operations here.</p> : null}
                {stage.items.map((item) => (
                  <div className="stage-item" key={item.item_id}>
                    <span>{item.label}</span>
                    <button className="small secondary" type="button" onClick={() => removeItem(stage.stage_id, item.item_id)}>
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            ))}
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
