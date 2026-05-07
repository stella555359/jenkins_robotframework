# Step 6: internal tools standalone tool runner

## 这一步解决的问题

`internal_tools/kpi_generator` 和 `internal_tools/kpi_detector` 需要同时支持两种调用方式：

1. `test-workflow-runner` workflow 内的 followup handler 调用。
2. Portal 独立工具入口触发后，由 `internal_tools.worker` 单独执行。

本步骤增加一个薄的 `internal_tools.tool_runner` 和一个 API polling worker，统一 standalone 执行入口，但不复制 generator / detector 的业务逻辑。

## 改了哪些文件

- `test-workflow-runner/internal_tools/tool_runner.py`
  - 读取 `tool_request.json`
  - 按 `tool_kind` 调用 `run_generator_from_payload` 或 `run_detector_from_payload`
  - 输出统一 `tool_result.json`
- `test-workflow-runner/internal_tools/worker.py`
  - 轮询 `platform-api` 的 `GET /api/kpi/tool-runs?status=created`
  - 标记任务 running
  - 调用 `tool_runner`
  - 通过 `/api/runs/{run_id}/callbacks/worker` 回写结果
- `test-workflow-runner/tests/test_orchestrator.py`
  - 增加 monkeypatch 单测，避免真实 Compass / Excel 依赖

## 核心调用链

```text
platform-api /api/kpi/tool-runs?status=created
  -> python -m internal_tools.worker
  -> internal_tools.tool_runner
  -> kpi_generator.service.run_generator_from_payload
     or kpi_detector.service.run_detector_from_payload
  -> tool-result.json
  -> platform-api /callbacks/worker
```

## 关键字段

- `tool_kind`: `kpi_generator` 或 `kpi_detector`
- `payload`: 传给对应 service 的参数
- `item_id`: 作为 artifact/runtime 默认目录的一部分
- `output_dir`: generator 映射为 `payload.output_dir`，detector 映射为 `payload.runtime_root`
- `artifact_manifest`: 从 service 返回的 artifacts 标准化而来，供 callback 使用
- `kpi_summary` / `detector_summary`: 分别回写到 platform-api

## 验证命令

由用户在目标环境执行：

```bash
cd /path/to/jenkins_robotframework/test-workflow-runner
python -m pytest tests/test_orchestrator.py
```

预期：

- 现有 runner dry-run 测试继续通过
- standalone tool runner 的 dispatch / failure result 测试通过
- standalone worker 的 request materialize / callback payload 测试通过

常见失败：

- `ModuleNotFoundError: internal_tools`: 执行目录不是 `test-workflow-runner` 根目录
- Compass 凭据错误：真实 generator 执行时缺少 `COMPASS_USERNAME` / `COMPASS_PASSWORD`
- detector 文件不存在：`payload.source_file` 指向的 xlsx 不存在
- worker 不处理任务：确认 platform-api 中工具 run 状态仍为 `created`，且 worker 的 `--platform-api-base-url` 指向正确

## 需要用户确认

- standalone detector 的输入文件是由用户上传到 Portal，还是从已有 generator artifact 选择。
- standalone generator 的 Compass 并发上限是否需要在 Portal 表单中开放 `max_interval_workers`。
