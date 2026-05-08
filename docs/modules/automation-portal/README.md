# Automation Portal Docs

## 模块定位

这里承接的是 `automation-portal` 自己的前端文档。

它主要解释：

- Robot run submission form
- run list / detail / KPI summary 页面
- artifact / detector 报告入口展示

当前已经有一个最小 Vite React TypeScript MVP，位于 `automation-portal/`。它先聚焦 B1 Robot 主线：表单一键 Run，内部调用 create + trigger，然后展示 run detail、artifact 和 KPI 区域。

## 推荐阅读顺序

1. [模块总索引](index.md)
2. overview 中的系统级架构文档
3. [Step 1：Robot Portal B1 MVP](steps/step-01-robot-portal-b1-mvp.md)

优先回看的 overview 文档：

- `docs/overview/gnb-kpi-regression-architecture.md`
- `docs/overview/gnb-kpi-system-runtime.md`

## 当前策略

这一轮先固定 4 个事实：

1. `automation-portal` 有自己的独立 step 轨
2. 它不再和 `platform-api` step 混写
3. MVP 先服务 Robot case 真实执行链路
4. standalone `internal_tool` 仍由 worker 路径执行，后续可加独立页面
