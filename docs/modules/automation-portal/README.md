# Automation Portal Docs

## 模块定位

这里承接的是 `automation-portal` 自己的前端文档。

它主要解释：

- workflow builder
- run list / detail / KPI summary 页面
- artifact / detector 报告入口展示

但从当前开始，这条模块线先只做占位，不抢 `platform-api` 和 `test-workflow-runner` 的主线顺序。

## 推荐阅读顺序

1. [模块总索引](index.md)
2. overview 中的系统级架构文档
3. 等 backend 和 execution 主线稳定后，再进入当前 step

优先回看的 overview 文档：

- `docs/overview/gnb-kpi-regression-architecture.md`
- `docs/overview/gnb-kpi-system-runtime.md`

## 当前策略

这一轮先只固定 4 个事实：

1. `automation-portal` 会有自己的独立 step 轨
2. 它不再和 `platform-api` step 混写
3. 当前先不展开大量前端细节
4. 等 backend 和 execution 主线稳定后，再按 step 往下写
