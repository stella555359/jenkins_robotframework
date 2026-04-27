# Step 00：重命名为 Test Workflow Runner

## 这一步的目标

把原来的 `jenkins-kpi-platform` 模块完整重命名为 `test-workflow-runner`。

这次重命名解决的是语义边界问题：

- `platform-api` 是 Web API 平台层，负责接收 run、保存状态、聚合结果。
- `test-workflow-runner` 是执行层，负责读取 workflow、调度 stage / item、接入 Jenkins / UTE / Robot，并输出 result / artifact manifest。
- 模块名不再带 `platform`，避免和 `platform-api` 混淆。

## 改动范围

代码目录：

- `jenkins-kpi-platform/` -> `test-workflow-runner/`

docs 目录：

- `docs/modules/jenkins-kpi-platform/` -> `docs/modules/test-workflow-runner/`

Python 包名：

- `gnb_kpi_orchestrator` -> `test_workflow_runner`

主要引用更新：

- `test-workflow-runner/tests/test_orchestrator.py`
- `test-workflow-runner/README.md`
- `test-workflow-runner/internal_tools/__init__.py`
- `docs/README.md`
- `docs/overview/README.md`
- `docs/overview/roadmap.md`
- `docs/overview/8-day-full-project-execution-plan.md`
- `docs/modules/platform-api/`
- `docs/modules/automation-portal/`

## 核心调用链

重命名前：

```text
tests/test_orchestrator.py
  -> gnb_kpi_orchestrator.request_loader
  -> gnb_kpi_orchestrator.runner
  -> gnb_kpi_orchestrator.models
```

重命名后：

```text
tests/test_orchestrator.py
  -> test_workflow_runner.request_loader
  -> test_workflow_runner.runner
  -> test_workflow_runner.models
```

外层模块边界也同步变成：

```text
platform-api
  -> 创建 run / 查询状态 / 接收 callback

test-workflow-runner
  -> 执行 workflow / 调用 Robot 或后处理工具 / 产出 result 和 artifact manifest

automation-portal
  -> React 页面创建 run / 展示执行状态和结果
```

## 开发侧验收步骤

在服务器上执行：

```bash
cd /opt/jenkins_robotframework
ls
ls test-workflow-runner
ls docs/modules/test-workflow-runner
```

预期：

- 能看到 `test-workflow-runner`。
- 不再需要进入 `jenkins-kpi-platform`。
- `test-workflow-runner/test_workflow_runner/` 存在。

再执行 import 级验证：

```bash
cd /opt/jenkins_robotframework/test-workflow-runner
python -m pytest tests
```

预期：

- `tests/test_orchestrator.py` 能正常 import `test_workflow_runner`。
- 不再报 `ModuleNotFoundError: No module named 'gnb_kpi_orchestrator'`。

如果 CLI 后续已经接好，再补：

```bash
python -m test_workflow_runner.cli --help
```

## 旧名称残留检查

在服务器上执行：

```bash
cd /opt/jenkins_robotframework
grep -R "jenkins-kpi-platform\|Jenkins KPI Platform\|gnb_kpi_orchestrator" -n docs test-workflow-runner platform-api automation-portal
```

预期：

- 当前有效代码和 docs 不再出现旧名称。
- 本文档作为迁移说明，会保留旧名称用于解释重命名前后的对应关系。
- 如果只在 `docs/archive/` 里出现，属于历史文档，可以保留。

如果看到当前 docs 或代码仍然出现旧名称，需要判断是哪一类：

- import 旧包名：需要改成 `test_workflow_runner`。
- 文档链接旧目录：需要改成 `docs/modules/test-workflow-runner/`。
- 历史 archive：可以不改。

## 学习版说明

这一步不是业务功能变化，而是工程边界整理。

你可以这样理解：

- 目录名 `test-workflow-runner` 描述“这一层做什么”：运行测试 workflow。
- Python 包名 `test_workflow_runner` 描述“代码里怎么 import”：Python 包不能用连字符，所以用下划线。
- 文档模块名和代码模块名保持一致，后续恢复上下文时不会再找错入口。

## 复盘问题

1. 为什么外层目录可以叫 `test-workflow-runner`，但 Python import 包必须叫 `test_workflow_runner`？
2. 为什么这个模块不适合继续叫 `platform`？
3. 后续 `platform-api` 和 `test-workflow-runner` 之间最关键的交互字段是什么？
4. 如果 pytest 报 `ModuleNotFoundError`，你会先检查目录名、包名，还是 `sys.path`？
