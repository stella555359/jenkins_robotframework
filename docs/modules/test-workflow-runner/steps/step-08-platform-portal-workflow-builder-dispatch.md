# Step 8：Portal Workflow Builder 与双调度入口

## 这一步解决的问题

这一步把 Python KPI Runner 从“本地 dry-run CLI 能跑”推进到“可以被 Portal 创建 run，并通过 `platform-api` 选择 worker 或 Jenkins 调度”的阶段。

当前固定两种调度方式：

- `dispatch_backend=worker`
  - `platform-api` 把 `python_orchestrator` run 标记为 `queued`。
  - `metadata.worker_handoff` 提供 detail/callback URL，后续 Python worker 拉取并执行。
- `dispatch_backend=jenkins`
  - `platform-api` 复用 Jenkins trigger 能力，把 `WORKFLOW_SPEC_JSON` 等参数传给 Jenkins。
  - 后续 Jenkins job 负责 checkout / runner CLI / callback。

Portal 侧不要求用户显式选择“是否用 UE”。页面根据 operation catalog 的 `requires_ue` 自动判断：

- 选了 `prepare_ue / attach / traffic / handover / swap / detach`，才要求 UE。
- 只选 `site_reset / ru_reset / cell_lock_unlock / alarm_check / syslog_check`，UE 可以为空。

## 改了哪些文件

- `platform-api/app/schemas/run.py`
  - 新增 `DispatchBackend`。
  - `RunCreateRequest` 增加 `dispatch_backend`。
  - 新增 `OperationDescriptor` / `OperationCatalogResponse`。
- `platform-api/app/services/run_service.py`
  - `python_orchestrator` trigger 支持 `worker` 和 `jenkins`。
  - 新增 operation catalog 数据。
- `platform-api/app/services/jenkins_service.py`
  - 新增 `build_python_orchestrator_jenkins_parameters()`。
- `platform-api/app/api/v1/router.py`
  - 新增 `GET /api/workflow/operation-catalog`。
- `platform-api/tests/test_runs.py`
  - 覆盖 worker queue、Jenkins dispatch、operation catalog。
- `automation-portal/src/api.ts`
  - 增加 `python_orchestrator` create payload、`dispatch_backend`、operation catalog API。
- `automation-portal/src/pages/WorkflowBuilder.tsx`
  - 新增 Portal workflow builder MVP。
- `automation-portal/src/pages/RunDetail.tsx`
  - 展示 executor、dispatch、workflow spec、runner request/result。
- `automation-portal/src/App.tsx` / `src/main.tsx` / `src/styles.css`
  - 接入页面路由、导航和样式。

## 核心调用链

```text
Portal Workflow Builder
  -> GET /api/workflow/operation-catalog
  -> 用户选择 testline / UE / operation / stage serial-parallel / dispatch backend
  -> POST /api/runs executor_type=python_orchestrator
  -> POST /api/runs/{run_id}/trigger
     -> worker: status=queued + metadata.worker_handoff
     -> jenkins: buildWithParameters(WORKFLOW_SPEC_JSON)
  -> Run Detail 展示 workflow_spec / runner_request / worker_handoff / runner_result
```

## 关键字段

- `dispatch_backend`
  - `worker` 或 `jenkins`。
- `metadata.runner_request`
  - Portal 根据 builder 生成的完整 runner request，后续 worker/Jenkins 可以直接消费。
- `workflow_spec`
  - `platform-api` 存储的标准 workflow 描述。
- `metadata.worker_handoff`
  - worker 调度时给后续 worker 使用的 detail/callback URL。
- `OperationDescriptor.requires_ue`
  - 前端判断是否必须选择 UE 的依据。

## 服务器验证命令

按项目规则，这些命令由用户在目标服务器执行：

```bash
cd /opt/jenkins_robotframework/platform-api
source .venv/bin/activate
python -m pytest tests/test_runs.py
```

Portal 构建验证：

```bash
cd /opt/jenkins_robotframework/automation-portal
npm install
npm run build
```

手工 API smoke：

```bash
curl -k https://10.71.210.104/api/workflow/operation-catalog
```

## 预期结果

- `tests/test_runs.py` 通过。
- `GET /api/workflow/operation-catalog` 返回 `attach.requires_ue=true`、`ru_reset.requires_ue=false`。
- Portal 左侧出现 `KPI Workflow Builder`。
- Builder 页面能拖 operation 到 stage。
- 选择 `worker` 提交后，run detail 状态为 `queued`，dispatch 为 `worker`。
- 选择 `jenkins` 提交后，run detail 状态为 `triggered`，dispatch 为 `jenkins`。

## 常见失败模式

- `workflow_spec is required when executor_type is python_orchestrator`
  - Portal payload 没生成 workflow spec。
- `robot runs only support dispatch_backend=jenkins`
  - Robot run 错传了 `dispatch_backend=worker`。
- `jenkins_base_url is not configured`
  - 选择 Jenkins dispatch 但后端 Jenkins 配置未设置。
- Portal build 失败找不到类型
  - 检查 `api.ts` 的 `RunCreatePayload` 和 `WorkflowBuilder.tsx` 的 payload 是否一致。

## 需要用户确认的问题

- Jenkins 侧是否新建独立 `python-orchestrator` job，还是先复用现有 job path。
- worker 侧后续是否和 `internal_tools.worker` 合并，还是新增 `python_orchestrator_worker.py`。
- Portal 默认 UE 列表当前是 T813 示例，后续是否要由 backend 根据 `testline` 动态返回。
