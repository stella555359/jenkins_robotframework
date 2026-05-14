# Step 8 Test Automation：Portal Workflow Builder 与双调度

## 已补充的自动化覆盖

- `test_trigger_python_orchestrator_run_queues_worker`
  - 验证 `dispatch_backend=worker` 的 `python_orchestrator` run 会进入 `queued`。
  - 验证 `metadata.worker_handoff.detail_url / callback_url` 被写入。
- `test_trigger_python_orchestrator_run_dispatches_to_jenkins`
  - 验证 `dispatch_backend=jenkins` 会调用 Jenkins trigger。
  - 验证 Jenkins 参数包含 `RUN_ID`、`EXECUTOR_TYPE`、`TESTLINE`、`WORKFLOW_SPEC_JSON`、`DRY_RUN`。
- `test_operation_catalog_returns_operation_rules`
  - 验证 operation catalog 提供前端判断规则。
  - 验证 `attach.requires_ue=true`、`ru_reset.requires_ue=false`。

## 服务器侧验证命令

```bash
cd /opt/jenkins_robotframework/platform-api
source .venv/bin/activate
python -m pytest tests/test_runs.py
```

```bash
cd /opt/jenkins_robotframework/automation-portal
npm install
npm run build
```

## 预期结果

- 后端 pytest 通过。
- 前端 build 通过。
- Portal 能打开 `KPI Workflow Builder` 页面。
- Worker dispatch run detail 中显示 `queued`。
- Jenkins dispatch 在 Jenkins 配置正确时显示 `triggered`。

## 暂未自动化覆盖

- 浏览器拖拽交互没有接 Playwright 自动化。
- worker 实际消费 `metadata.runner_request` 执行 runner CLI 还没接入。
- Jenkins runner job 的真实 pipeline 参数消费还没接入。
