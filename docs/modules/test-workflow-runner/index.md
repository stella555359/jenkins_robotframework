# Test Workflow Runner 总索引

## 这份索引负责什么

这份文档现在只承担 3 个职责：

1. 看当前执行层做到哪一步
2. 快速跳转到某个 runner step
3. 区分哪些内容属于执行层，哪些内容属于 `platform-api`、`jenkins-integration` 或 `automation-portal`

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

- [x] Step 1：冻结 runner request loader / workflow schema / CLI dry-run 入口
- [x] Step 2：实现 stage / item engine 与并行安全边界
- [ ] Step 3：接入 `testline_configuration` / `robotws` / `TAF gateway`
- [x] Step 4：统一 `result.json` / timeline / artifact manifest 输出
- [x] Step 5：接入 `generator / detector` 作为 execution 后处理模块

当前 Step 5 的参数约定与接入方式，已经补到独立 step：

- `steps/step-05-generator-detector-internal-api-contract.md`

当前状态：

- Step 1 已冻结 request schema / loader / CLI dry-run 入口
- Step 2 已完成且已文档化：stage / item engine、protected parallel stage 拦截和结果分桶语义已收口
- Step 4 已把 `result.json` 顶层统一到 `timeline + artifact_manifest + results`
- Step 5 已冻结 generator / detector 的 internal API params contract
- 当前剩余主缺口集中在 Step 3：把真实 `testline_configuration` / `robotws` / TAF 调用链进一步收口
- 当前 Step 3 已先收口一部分运行时契约：`repository_root` 已进入 `TestlineContext`，相对 `script_path / working_directory` 已按仓库根目录稳定解析

## 下一步入口

- [Step 00：重命名为 Test Workflow Runner](steps/step-00-rename-to-test-workflow-runner.md)
- [Step 1：runner request loader / workflow schema / CLI dry-run](steps/step-01-runner-request-loader-and-cli.md)
- [Step 2：实现 stage / item engine 与并行安全边界](steps/step-02-stage-item-engine-and-safety-boundary.md)
- [Step 3：接入 testline_configuration / robotws / TAF gateway 的运行时契约](steps/step-03-testline-robotws-taf-gateway-runtime-contract.md)
- [Step 4：统一 result.json / timeline / artifact manifest 输出](steps/step-04-result-timeline-and-artifact-manifest.md)
- [Step 5：generator / detector internal API params contract](steps/step-05-generator-detector-internal-api-contract.md)

测试自动化入口：

- [Testing Automation：step 级 pytest / CLI 与跨模块 Postman / SQLite / JMeter 验证](testing-automation/README.md)

公共 Jenkins 集成入口：

- [Jenkins Integration：公共 bootstrap / pipeline / job / script 流程](../jenkins-integration/README.md)

## 这条模块线的边界

这里负责：

- runner 输入模型
- 执行层串并行调度
- 消费 Jenkins 已准备好的本地 workspace / 配置 / bindings
- generator / detector 的执行接入

当前这条模块线里，`generator / detector` 的默认接入约定已经变成：

- `internal_tools` 内部模块
- orchestrator handler 直接调用内部 service
- `params` 驱动，而不是 `params.command` 驱动

这里不负责：

- 前端 workflow builder
- `platform-api` 的 run API 契约
- 通用 Jenkins trigger / pipeline / checkout / callback
- React 页面展示

## 当前协作约定

- 每个新 step 优先写进独立 step 文件
- 稳定知识后续沉淀进 `guides/`
- 测试设计放 `testing-training/`
- 测试自动化交付放 `testing-automation/`
- 这条模块线默认排在 `platform-api` backend-first 主线之后

