# Jenkins Integration Docs

## 模块定位

这里承接的是 `Jenkins integration layer` 文档，不属于某个具体执行器。

它主要解释：

- Jenkins 公共 bootstrap
- job / pipeline / jcasc / scripts 怎么分层
- `platform-api`、`robot`、`test-workflow-runner` 怎么通过 Jenkins 协作

如果你当前在推进：

- Jenkins trigger / callback
- Pipeline stage 设计
- Agent / workspace / checkout 流程
- `workflow_spec -> request.json` 物化边界

优先从这里进入。

## 推荐阅读顺序

1. [模块总索引](index.md)
2. [Jenkins Integration Layer 与执行流程](guides/jenkins-integration-layer-and-flow.md)
3. [Robot 最小执行路径](guides/robot-minimal-execution-path.md)
4. 再回到具体执行器模块

## 当前目录怎么理解

- `index.md`
  - 模块总索引，负责入口、边界和当前骨架状态
- `guides/`
  - 稳定的 Jenkins integration 说明

## 当前主线

这条模块线当前先做 4 件事：

1. 固定公共层边界
2. 固定 `jcasc / jobs / pipelines / scripts` 目录骨架
3. 固定 `platform-api -> Jenkins -> executor -> callback` 流程
4. 为后续真实 Jenkins 资产落库留出明确位置

当前第一条实现主线已经切到：

- 先做 `robot` 最小闭环
- 先固定 `robotcase_path -> robot command`
- 再逐步补 checkout / callback / runner bridge
