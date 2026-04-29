# Jenkins Integration 总索引

## 这份索引负责什么

这份文档现在只承担 3 个职责：

1. 看 Jenkins 公共集成层放什么
2. 快速跳转到公共流程和目录骨架
3. 区分哪些内容属于 `jenkins-integration`，哪些属于具体执行器

## Start Here / 先看这里

如果你是：

- 新开一个会话
- 正在收口 Jenkins / UTE / Agent 侧边界
- 想确认 `platform-api` 和执行器之间中间层该放什么

先按下面顺序恢复上下文：

1. 先看这份索引页的：
   - `当前状态`
   - `目录入口`
2. 再看 guide：
   - [Jenkins Integration Layer 与执行流程](guides/jenkins-integration-layer-and-flow.md)
3. 再进入具体执行器模块

## 当前状态

- [x] 已确认这层应独立于 `platform-api` / `automation-portal` / `test-workflow-runner`
- [x] 已建立 `jcasc / jobs / pipelines / scripts` 四个目录骨架
- [x] 已补模块入口文档和公共流程文档
- [x] 已补第一版 `robot` command helper 和最小 Pipeline 模板
- [x] `robot` 路径的 checkout / request materialize / callback helper 已落地
- [x] 已补 controller / node / credentials 级别的 `jenkins.yaml` 示例，以及 `robot` job 参数模板文档和实际 Job DSL 文件
- [ ] `python_orchestrator` 的 `workflow_spec -> request.json` 物化仍未落地

## 目录入口

- [顶层模块 README](../../../jenkins-integration/README.md)
- [jcasc 目录说明](../../../jenkins-integration/jcasc/README.md)
- [JCasC 示例](../../../jenkins-integration/jcasc/jenkins.yaml)
- [jobs 目录说明](../../../jenkins-integration/jobs/README.md)
- [Robot Job 模板文档](../../../jenkins-integration/jobs/robot-execution-job-template.md)
- [Robot Job DSL](../../../jenkins-integration/jobs/robot-execution-job.groovy)
- [pipelines 目录说明](../../../jenkins-integration/pipelines/README.md)
- [scripts 目录说明](../../../jenkins-integration/scripts/README.md)
- [Jenkins Integration Layer 与执行流程](guides/jenkins-integration-layer-and-flow.md)
- [Robot 最小执行路径](guides/robot-minimal-execution-path.md)

## 这条模块线的边界

这里负责：

- Jenkins 公共 bootstrap
- Job / Pipeline / Agent / Workspace 组织
- checkout / request materialize / command dispatch / callback 这类公共脚本
- 按执行器类型分发到 `robot` 或 `python_orchestrator`

这里不负责：

- `platform-api` 的 run schema / 持久化 / 查询 API
- `test_workflow_runner` 内部 stage / item / handler 逻辑
- `robotws` 用例内容和 `testline_configuration` 业务建模内容
