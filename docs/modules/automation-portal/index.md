# Automation Portal 总索引

## 这份索引负责什么

这份文档现在只承担 2 个职责：

1. 预留 `automation-portal` 的独立 step 轨
2. 明确它当前排在 backend 和 execution 主线之后

## 当前状态

从当前开始，`automation-portal` 不再作为 `platform-api` step 里的附属说明出现，而是预留自己的模块入口。

但当前推荐顺序仍然是：

1. 先推进 `platform-api`
2. 再推进 `test-workflow-runner`
3. 最后再详细展开 `automation-portal`

## 预留的后续 step 方向

后续这条模块线最可能先展开的 step 包括：

1. 最小 run submission form
2. 最小 workflow builder（先结构化表单，不急着拖拽）
3. run list / detail / KPI summary 页面
4. artifact / detector 报告入口展示

## 当前入口建议

如果你现在只是想确认这条模块线未来要做什么，优先看：

- `docs/overview/gnb-kpi-regression-architecture.md`
- `docs/overview/gnb-kpi-system-runtime.md`

如果你现在要真正开始实现，先回到：

- `docs/modules/platform-api/`
- `docs/modules/test-workflow-runner/`
