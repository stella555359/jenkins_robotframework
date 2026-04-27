# Test Workflow Runner 总索引

## 这份索引负责什么

这份文档现在只承担 3 个职责：

1. 看当前执行层做到哪一步
2. 快速跳转到某个 runner / Jenkins step
3. 区分哪些内容属于执行层，哪些内容属于 `platform-api` 或 `automation-portal`

## Start Here / 先看这里

如果你是：

- 新开一个会话
- Cursor 刚重启
- 一时忘了执行层该从哪份文档继续

先按下面顺序恢复上下文：

1. 先看这份索引页的：
   - `当前进度看板`
   - `下一步入口`
2. 再看 overview：
   - `docs/overview/gnb-kpi-regression-architecture.md`
   - `docs/overview/gnb-kpi-system-runtime.md`
3. 再进入当前 step

最短恢复路径：

```text
先看索引 -> 再看 overview 边界 -> 再看当前 step
```

## 当前进度看板

- [ ] Step 1：冻结 runner request loader / workflow schema / CLI dry-run 入口
- [ ] Step 2：实现 stage / item engine 与并行安全边界
- [ ] Step 3：接入 `testline_configuration` / `robotws` / `TAF gateway`
- [ ] Step 4：统一 `result.json` / timeline / artifact manifest 输出
- [ ] Step 5：接入 `generator / detector` 作为 execution 后处理模块

当前 Step 5 的参数约定与接入方式，已经补到独立 step：

- `steps/step-05-generator-detector-internal-api-contract.md`

## 下一步入口

- [Step 00????? Test Workflow Runner](steps/step-00-rename-to-test-workflow-runner.md)
- [Step 1：runner request loader / workflow schema / CLI dry-run](steps/step-01-runner-request-loader-and-cli.md)
- [Step 5：generator / detector internal API params contract](steps/step-05-generator-detector-internal-api-contract.md)

## 这条模块线的边界

这里负责：

- runner 输入模型
- 执行层串并行调度
- Jenkins 侧执行资源组织
- generator / detector 的执行接入

当前这条模块线里，`generator / detector` 的默认接入约定已经变成：

- `internal_tools` 内部模块
- orchestrator handler 直接调用内部 service
- `params` 驱动，而不是 `params.command` 驱动

这里不负责：

- 前端 workflow builder
- `platform-api` 的 run API 契约
- React 页面展示

## 当前协作约定

- 每个新 step 优先写进独立 step 文件
- 稳定知识后续沉淀进 `guides/`
- 测试设计放 `testing-training/`
- 测试自动化交付放 `testing-automation/`
- 这条模块线默认排在 `platform-api` backend-first 主线之后

