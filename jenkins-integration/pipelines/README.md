# pipelines

这里放 Jenkins Pipeline 骨架。

建议承接的公共 stage：

- prepare workspace
- checkout `robotws` / `testline_configuration` / integration scripts
- choose executor type
- run `robot` or `test-workflow-runner`
- archive artifacts
- callback `platform-api`

这层只负责公共调度，不承载：

- `test_workflow_runner` 内部 stage / item 逻辑
- Robot case 内容本身

建议后续至少拆成两类 Pipeline：

- 测试执行 Pipeline
- 平台发布 / 部署 Pipeline

当前已落地：

- `robot-execution.Jenkinsfile`
	- 最小 Robot 执行 Pipeline 模板
