import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, RunCreatePayload } from "../api";

function parseJsonObject(value: string): Record<string, unknown> {
  const trimmed = value.trim();
  if (!trimmed) {
    return {};
  }
  const parsed = JSON.parse(trimmed) as unknown;
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("Variables JSON must be an object.");
  }
  return parsed as Record<string, unknown>;
}

export function RobotRunForm() {
  const navigate = useNavigate();
  const [testline, setTestline] = useState("T813");
  const [robotcasePath, setRobotcasePath] = useState("testsuite/Hangzhou/RRM/example.robot");
  const [caseName, setCaseName] = useState("");
  const [selectedTests, setSelectedTests] = useState("");
  const [variablesJson, setVariablesJson] = useState("{\n  \"AF_PATH\": \"\"\n}");
  const [build, setBuild] = useState("");
  const [tafMode, setTafMode] = useState("reuse");
  const [robotwsGitRef, setRobotwsGitRef] = useState("master");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    let createdRunId: string | null = null;

    try {
      const robotVariables = parseJsonObject(variablesJson);
      const selected = selectedTests
        .split(/\r?\n/)
        .map((item) => item.trim())
        .filter(Boolean);
      const metadata: Record<string, unknown> = {
        case_name: caseName.trim(),
        selected_tests: selected,
        robot_variables: robotVariables,
        taf_mode: tafMode,
        robotws_ref: robotwsGitRef.trim() || "master"
      };
      const payload: RunCreatePayload = {
        testline: testline.trim(),
        robotcase_path: robotcasePath.trim(),
        executor_type: "robot",
        build: build.trim() || undefined,
        metadata
      };

      const created = await api.createRun(payload);
      createdRunId = created.run_id;
      await api.triggerRun(created.run_id);
      navigate(`/runs/${created.run_id}`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to submit run.";
      if (createdRunId) {
        navigate(`/runs/${createdRunId}`, { state: { triggerError: message } });
        return;
      }
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Robot</p>
          <h2>New Robot Run</h2>
        </div>
        <p className="muted">One button creates the run, triggers Jenkins, then opens the run detail page.</p>
      </div>

      <form className="form-grid" onSubmit={handleSubmit}>
        <label>
          Testline
          <input value={testline} onChange={(event) => setTestline(event.target.value)} required />
        </label>
        <label>
          Robot case path
          <input value={robotcasePath} onChange={(event) => setRobotcasePath(event.target.value)} required />
        </label>
        <label>
          Case name
          <input value={caseName} onChange={(event) => setCaseName(event.target.value)} placeholder="Optional - passed as -t" />
        </label>
        <label>
          Build
          <input value={build} onChange={(event) => setBuild(event.target.value)} placeholder="Optional build/version" />
        </label>
        <label>
          TAF mode
          <select value={tafMode} onChange={(event) => setTafMode(event.target.value)}>
            <option value="reuse">reuse</option>
            <option value="create-venv">create-venv</option>
            <option value="skip-install">skip-install</option>
          </select>
        </label>
        <label>
          Robotws git ref
          <input
            value={robotwsGitRef}
            onChange={(event) => setRobotwsGitRef(event.target.value)}
            placeholder="Optional branch/tag/commit, default master"
          />
        </label>
        <label className="span-2">
          Selected tests
          <textarea
            value={selectedTests}
            onChange={(event) => setSelectedTests(event.target.value)}
            placeholder="Optional, one Robot test name per line"
            rows={4}
          />
        </label>
        <label className="span-2">
          Robot variables JSON
          <textarea value={variablesJson} onChange={(event) => setVariablesJson(event.target.value)} rows={8} />
        </label>

        {error ? <p className="error span-2">{error}</p> : null}

        <div className="actions span-2">
          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Running..." : "Run"}
          </button>
        </div>
      </form>
    </section>
  );
}
