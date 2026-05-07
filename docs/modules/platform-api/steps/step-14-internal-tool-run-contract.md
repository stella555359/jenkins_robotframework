# Step 14: internal tool run contract

## 这一步解决的问题

`kpi_generator` 和 `kpi_detector` 过去只能作为 `test-workflow-runner` 的 followup item 出现。Portal 后续需要把它们作为两个独立功能入口使用，因此 `platform-api` 需要能创建、查询和接收这类 standalone 工具 run 的结果。

## 改了哪些文件

- `platform-api/app/schemas/run.py`
  - `ExecutorType` 增加 `internal_tool`
  - 新增 `ToolKind`、`ToolRunCreateRequest`、`ToolRunCreateResponse`、`ToolExecutionHandoff`
- `platform-api/app/services/run_service.py`
  - 新增 `tool_run_create`
  - 新增 `get_tool_run_list`
  - 普通 `/api/runs` 拒绝直接创建 `internal_tool`
- `platform-api/app/api/v1/router.py`
  - 新增 `POST /api/kpi/tool-runs`
  - 新增 `GET /api/kpi/tool-runs`
  - 新增 `POST /api/runs/{run_id}/callbacks/worker`
- `platform-api/tests/test_runs.py`
  - 增加 standalone generator / detector tool run 的契约测试

## 核心调用链

```text
Portal
  -> POST /api/kpi/tool-runs
  -> platform-api 写 runs 表 executor_type=internal_tool
  -> 返回 handoff detail_url / callback_url
  -> internal_tools.worker 轮询 created 工具 run
  -> internal_tools.tool_runner 执行 generator / detector
  -> POST /api/runs/{run_id}/callbacks/worker 回写 artifact / summary
```

## 关键字段

- `tool_kind`: `kpi_generator` 或 `kpi_detector`
- `payload`: 原样保存到 `metadata.tool_payload`，由 worker 物化成 tool request
- `metadata.tool_kind`: 执行层判断调用哪个 internal tool
- `kpi_summary_json`: generator 回调摘要
- `detector_summary_json`: detector 回调摘要

## 验证命令

由用户在目标环境执行：

```bash
cd /path/to/jenkins_robotframework/platform-api
python -m pytest tests/test_runs.py
```

预期：

- 新增的 `POST /api/kpi/tool-runs` 测试通过
- `GET /api/kpi/tool-runs` 只返回 `executor_type == internal_tool` 的记录
- `GET /api/kpi/tool-runs?status=created` 可作为 worker 轮询入口
- `/api/runs` 直接传 `executor_type=internal_tool` 会返回 400

常见失败：

- `422`：请求 schema 字段名不匹配
- `500`：SQLite JSON 列写入或读取异常
- list 测试失败：过滤逻辑没有只筛 `internal_tool`

## 需要用户确认

- Portal 表单是否直接暴露原始 `payload` JSON，还是拆成 generator / detector 两套结构化表单。
- worker 是 standalone tool run 的主路径；Jenkins 只保留给 Robot / workflow 执行链。
