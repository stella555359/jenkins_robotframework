# Test Workflow Runner Docs

## 模块定位

这里承接的是执行层文档，不是 `platform-api` 的补充页。

它主要解释：

- Python runner 的 request / workflow / stage / item 执行语义
- `generator / detector` 如何作为 execution 后处理能力接入

如果你要看：

- Jenkins 公共 bootstrap
- Jenkins Pipeline
- checkout / workspace / callback 公共流程

请先看：

- `docs/modules/jenkins-integration/`

如果你当前在推进：

- runner
- generator / detector 接入

优先从这里进入。

如果你当前要对齐后处理参数面，优先看：

- `steps/step-05-generator-detector-internal-api-contract.md`

## 推荐阅读顺序

1. [模块总索引](index.md)
2. `steps/` 下当前正在推进的 step
3. `testing-training/` 和 `testing-automation/` 下对应 step 的测试文档

如果你要先确认系统级边界，请先回看：

- `docs/overview/gnb-kpi-regression-architecture.md`
- `docs/overview/gnb-kpi-system-runtime.md`

## 当前目录怎么理解

- `index.md`
  - 模块总索引，负责进度、入口和当前主线
- `guides/`
  - 稳定知识，后续沉淀 runner / Jenkins 的长期说明
- `steps/`
  - 单步实现记录
- `testing-training/`
  - 执行层测试设计训练材料
- `testing-automation/`
  - 执行层测试自动化交付记录

## 当前主线

从当前开始，这条模块主线固定按下面顺序推进：

1. 先冻结 runner request schema 和 CLI 入口
2. 再补 stage / item engine 与并行安全边界
3. 再接 `testline_configuration`、`robotws`、`TAF gateway`
4. 再统一 `result.json / timeline / artifact manifest`
5. 最后接 `generator / detector`

当前 `generator / detector` 的推荐接入方式已经固定为：

- 收编到 `test-workflow-runner/internal_tools/`
- 由 orchestrator handler 直接走内部 API
- 不再以 `params.command` 作为默认主线
- followup stage 默认按串行组织；这不只是风格建议，标准 CLI 主路径下 followup 域并行会被 safety 校验拦截
