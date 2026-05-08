# Automation Portal 总索引

## 这份索引负责什么

这份文档现在只承担 2 个职责：

1. 记录 `automation-portal` 的独立 step 轨
2. 标记当前 Robot Portal B1 MVP 的实现状态

## 当前状态

从当前开始，`automation-portal` 不再作为 `platform-api` step 里的附属说明出现，而是有自己的模块入口。

当前 B1 MVP 已实现：

1. `POST /api/runs`
2. `POST /api/runs/{run_id}/trigger`
3. 跳转到 `/runs/{run_id}` 查看状态、artifact、KPI summary

## 当前进度看板

- [x] Step 1：Robot Portal B1 MVP

## 预留的后续 step 方向

后续这条模块线最可能先展开的 step 包括：

1. internal_tool 独立工具页面
2. 最小 workflow builder（先结构化表单，不急着拖拽）
3. KPI followup 配置页面
4. artifact / detector 报告增强展示

## 当前入口建议

如果你现在只是想确认这条模块线未来要做什么，优先看：

- `docs/modules/automation-portal/steps/step-01-robot-portal-b1-mvp.md`
- `docs/overview/gnb-kpi-regression-architecture.md`
- `docs/overview/gnb-kpi-system-runtime.md`

如果你现在要确认后端契约，先回到：

- `docs/modules/platform-api/`
- `docs/modules/test-workflow-runner/`
