# Step 8：Portal Workflow Builder 与 Jenkins 调度入口

## 这一步解决的问题

这一步把 Python KPI Runner 从“本地 dry-run CLI 能跑”推进到“可以被 Portal 创建 run，并通过 `platform-api` 触发 Jenkins 调度”的阶段。

当前主线只保留 Jenkins 调度：

```text
automation-portal
  -> platform-api
  -> Jenkins
  -> checkout robotws + testline_configuration
  -> prepare TAF/Python environment
  -> test-workflow-runner CLI
  -> callback platform-api
```

不再把 `automation-portal -> platform-api -> worker -> test-workflow-runner` 作为 KPI Runner CI/CD 方案。`internal_tools.worker` 仍只属于 standalone KPI generator/detector 工具线，不是 Python KPI Runner 主线。

Portal 侧不要求用户显式选择“是否用 UE”。页面根据 operation catalog 的 `requires_ue` 自动判断：

- 选了 `prepare_ue / attach / traffic / handover / swap / detach`，才要求 UE。
- 只选 `site_reset / ru_reset / cell_lock_unlock / alarm_check / syslog_check`，UE 可以为空。

## 改了哪些文件

- `platform-api/app/schemas/run.py`
  - 新增 `OperationDescriptor` / `OperationCatalogResponse`。
- `platform-api/app/services/run_service.py`
  - `python_orchestrator` trigger 走 Jenkins。
  - 新增 operation catalog 数据。
- `platform-api/app/services/jenkins_service.py`
  - 新增并补齐 `build_python_orchestrator_jenkins_parameters()`，包括 `BUILD`、repo ref、TAF 环境和 artifact 参数。
- `platform-api/app/core/config.py`
  - 新增 `JENKINS_PYTHON_ORCHESTRATOR_JOB_PATH`，避免 Python KPI Runner 误触发 Robot job。
- `jenkins-integration/jobs/kpi-runner-job.groovy`
  - 新增 KPI runner Job DSL，生成 `CIT/KPI_Testing/<SBTS>/<testline>` 和 `CRT/KPI_Testing/<SBTS>/<testline>` 入口。
- `jenkins-integration/pipelines/kpi-runner.Jenkinsfile`
  - 新增 KPI runner Jenkinsfile，复用 checkout/env/callback 脚本并执行 runner CLI。
- `jenkins-integration/scripts/materialize_python_orchestrator_request.py`
  - 新增 `python_orchestrator` request materializer，将 run detail / `WORKFLOW_SPEC_JSON` / Portal `runner_request` 物化为 runner CLI request。
- `platform-api/app/api/v1/router.py`
  - 新增 `GET /api/workflow/operation-catalog`。
- `platform-api/tests/test_runs.py`
  - 覆盖 Jenkins dispatch、operation catalog。
- `automation-portal/src/api.ts`
  - 增加 `python_orchestrator` create payload、operation catalog API。
- `automation-portal/src/pages/WorkflowBuilder.tsx`
  - 新增 Portal workflow builder MVP。
- `automation-portal/src/pages/RunDetail.tsx`
  - 展示 executor、workflow spec、runner request/result。
- `automation-portal/src/App.tsx` / `src/main.tsx` / `src/styles.css`
  - 接入页面路由、导航和样式。

## 核心调用链

```text
Portal Workflow Builder
  -> GET /api/workflow/operation-catalog
  -> 用户选择 testline / UE / operation / stage serial-parallel
  -> POST /api/runs executor_type=python_orchestrator
  -> POST /api/runs/{run_id}/trigger
     -> Jenkins buildWithParameters(WORKFLOW_SPEC_JSON)
  -> Run Detail 展示 workflow_spec / runner_request / runner_result
```

## 关键字段

- `metadata.runner_request`
  - Portal 根据 builder 生成的完整 runner request，后续 Jenkins job 可以直接消费。
- `workflow_spec`
  - `platform-api` 存储的标准 workflow 描述。
- `BUILD`
  - 本次 KPI testing 的 CIT 包 / 软件包版本。
  - Jenkins job 中是一等参数。
  - materializer 会写入 runner request 顶层 `build`，并自动补到 `kpi_generator` item 的 `params.build`。
- `JENKINS_PYTHON_ORCHESTRATOR_JOB_PATH`
  - Python KPI Runner 专用 Jenkins job path。
  - 当前默认：`job/CIT/job/KPI_Testing/job/SBTS26R1/job/7_5_UTE5G402T813`。
- `OperationDescriptor.requires_ue`
  - 前端判断是否必须选择 UE 的依据。

## Jenkins 前置 checkout 方案

因为 runner 后续通过 `TafGateway` / binding adapter 调用 TAF 或 robotws Python 能力，同时 `config_resolver` 需要读取 `testline_configuration` 中的 `tl` 对象，所以 Jenkins job 前置步骤仍需要准备：

```text
jenkins_robotframework
robotws
testline_configuration
/home/ute/CIENV/<testline>
```

当前可复用：

- `jenkins-integration/scripts/checkout_sources.py`
  - 已支持 `robotws` 和 `testline_configuration` checkout。
- `jenkins-integration/scripts/prepare_taf_environment.py`
  - 已支持复用或创建 `/home/ute/CIENV/<testline>`。

当前需要新增或扩展：

- `python_orchestrator` request materializer：已落地到 `jenkins-integration/scripts/materialize_python_orchestrator_request.py`。
- KPI runner 专用 Jenkinsfile：已落地到 `jenkins-integration/pipelines/kpi-runner.Jenkinsfile`。
- KPI runner Job DSL：已落地到 `jenkins-integration/jobs/kpi-runner-job.groovy`。
- runner CLI 执行 stage：已落地。
- artifact collect + callback stage：已落地。

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
- 提交后 `platform-api` 触发 Jenkins，run detail 状态为 `triggered`。

## 常见失败模式

- `workflow_spec is required when executor_type is python_orchestrator`
  - Portal payload 没生成 workflow spec。
- `jenkins_base_url is not configured`
  - 后端 Jenkins 配置未设置。
- Portal build 失败找不到类型
  - 检查 `api.ts` 的 `RunCreatePayload` 和 `WorkflowBuilder.tsx` 的 payload 是否一致。

## 需要用户确认的问题

- Jenkins 侧是否新建独立 `python-orchestrator` / `KPI_Testing` job，还是先复用现有 job path 做 smoke。
- KPI runner job 的 folder 是否按 `CIT/KPI_Testing/<SBTS>/<testline>` / `CRT/KPI_Testing/<SBTS>/<testline>` 作为最终目录结构。
- Portal 默认 UE 列表当前是 T813 示例，后续是否要由 backend 根据 `testline` 动态返回。

## 学习记录

- 解决的问题：把 Python KPI Runner 的 CI/CD 主线收口到 Jenkins，避免 Portal/API/worker 与 Jenkins 双路径造成主线不清晰。
- 文件变更原因：本文档从双调度说明改为 Jenkins-only 方案说明，明确 checkout 和 TAF 环境准备仍需复用 Robot 线的前置能力。
- 核心调用流：Portal builder 生成 workflow -> `platform-api` 创建/触发 run -> Jenkins checkout `robotws` 和 `testline_configuration` -> runner CLI 执行 -> callback。
- 关键字段：`RUN_ID`、`TESTLINE`、`BUILD`、`WORKFLOW_SPEC_JSON`、`CALLBACK_URL`、`DRY_RUN`、`RUNNER_REPOSITORY_ROOT`、`RESULT_JSON_PATH`。
- 复盘问题：确认 KPI runner Job folder、Jenkins label、robotws/testline_configuration ref 默认值、TAF venv 复用策略。
