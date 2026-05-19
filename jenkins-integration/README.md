# jenkins-integration

这里放 `Jenkins integration layer` 的公共骨架。

这层不属于某个具体执行器，而是同时服务：

- `robot` 执行链
- `python_orchestrator` 执行链

## 负责什么

- Jenkins master / agent 的基础集成约定
- Pipeline stage 编排与执行器分发
- workspace / artifact / callback 的公共组织
- checkout / bootstrap / request materialize / command dispatch 这类公共脚本

## 不负责什么

- `platform-api` 的 run contract 和数据库语义
- `test_workflow_runner` 内部的 stage / item orchestration
- `robotws` 具体测试用例内容

## 当前目录

- `jcasc/`
  - Jenkins Configuration as Code 相关配置骨架
- `jobs/`
  - Jenkins job 模板、seed job、DSL 入口骨架
- `pipelines/`
  - 通用 Pipeline / Jenkinsfile 骨架
- `scripts/`
  - 被 Pipeline 调用的 Python / shell helper 骨架
- [KPI CI/CD Flow](kpi_ci_cd_flow.md)
  - 解释 KPI Runner Job DSL、seed job、目录生成方式和多 SBTS / testline 扩展策略

## 当前推荐调用链

```text
automation-portal / caller
-> platform-api
-> jenkins-integration
-> robot executor | test-workflow-runner executor
-> callback -> platform-api
```

## 当前状态

这一层当前已经落下第一条真实 `robot` 执行链：

- `scripts/build_robot_command.py`
  - 把 `robotcase_path` 物化成可执行的 Robot 命令计划
- `scripts/materialize_run_request.py` / `scripts/checkout_sources.py` / `scripts/prepare_taf_environment.py` / `scripts/post_run_callback.py`
	- 覆盖 request 物化、源码 checkout、Python 环境准备和 callback 回传
- `pipelines/robot-execution.Jenkinsfile`
  - 提供最小 Robot 执行 Pipeline 模板
- `jobs/robot-execution-job.groovy`
	- 提供实际 Job DSL 文件
- `jcasc/jenkins.yaml`
	- 提供 controller / node / credentials 级别的 JCasC 示例

当前仍待继续补：

- seed job 已由 JCasC 代码化：
  - `jcasc/jenkins.yaml` 会创建 `seed/jenkins-robotframework-seed`
  - `pipelines/seed-jobs.Jenkinsfile` 会 checkout 本仓库并执行 `jenkins-integration/jobs/*.groovy`
- `python_orchestrator` 路径已经补第一版 Jenkins 入口：
  - `jobs/kpi-runner-job.groovy`
  - `pipelines/kpi-runner.Jenkinsfile`
  - `scripts/materialize_python_orchestrator_request.py`
- 后续仍需在服务器重载 JCasC、运行 seed job，实际生成 `CIT/KPI_Testing/<SBTS>/<testline>` / `CRT/KPI_Testing/<SBTS>/<testline>` job 并做 Jenkins smoke 验证
