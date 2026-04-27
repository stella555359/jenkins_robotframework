# Overview Docs

## 目录定位

这里放的是项目级文档，不隶属于某一个具体模块。

适合放在这里的内容通常包括：

- 全项目路线图
- 跨模块架构说明
- 系统级 runtime 文档
- 集成顺序
- 端到端主线说明

一句话规则：

```text
只要文档需要同时解释 React、Jenkins、UTE、Robot、runner 里的两个以上角色，
默认它属于 overview，而不是某一个 module。
```

## 当前文档

- [项目路线图](roadmap.md)
- [GNB KPI Regression Architecture](gnb-kpi-regression-architecture.md)
- [GNB KPI System Runtime](gnb-kpi-system-runtime.md)

## 当前推荐推进顺序

从当前这轮架构冻结开始，默认按下面这条主线推进：

1. 先走 `platform-api`
   - 先把执行器无关的 run contract、Jenkins callback、artifact/KPI metadata 查询面打稳
2. 再走 `test-workflow-runner`
   - 单独推进 runner、generator、detector 的执行层实现
3. 最后再走 `automation-portal`
   - 当前先预留独立 step 轨，等 backend 和 execution 主线更稳后再细化

对应入口：

- `docs/modules/platform-api/`
- `docs/modules/test-workflow-runner/`
- `docs/modules/automation-portal/`

## 怎么区分 overview 和 modules

### 放在 `overview/`

- 系统级 runtime 架构
- 跨模块执行链路
- `React / FastAPI / Jenkins / UTE / Robot / runner / TAF` 的职责关系
- 公共 bootstrap / 公共前置层
- 整个平台的端到端流程图

### 放在 `docs/modules/<module>/`

- 单模块内部职责
- API 设计
- schema / service / repository 关系
- step、testing、implementation notes

## 使用建议

如果你想继续推进某一个具体模块，优先回到：

- `docs/modules/<module>/`

如果你想先确认整个项目大方向、系统边界或运行链路，优先从这里进入。
