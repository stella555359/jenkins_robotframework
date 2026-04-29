# jobs

这里放 Jenkins job 定义骨架。

建议承接：

- seed job
- Job DSL
- 参数模板
- 不同执行器的 job 入口定义

这一层的职责是把：

```text
platform-api 传来的 run 语义
```

映射成：

```text
Jenkins job 需要的参数、标签、凭据和执行模式
```

这里先不写死所有 job 名，但 `robot` 路径已经补了“模板文档 + 实际 Job DSL 文件”两层入口：

- [robot-execution-job-template.md](robot-execution-job-template.md)
	- 固定 seed job / job 参数模板思路
	- 固定 `ROBOTWS_GIT_REF` 和 `TESTLINE_CONFIGURATION_GIT_REF` 的默认值策略
	- 说明哪些参数应该走全局环境，哪些保留 job 级配置
- [robot-execution-job.groovy](robot-execution-job.groovy)
	- 可直接放进 seed job 流程的实际 Job DSL 文件
	- 参数列表与 `pipelines/robot-execution.Jenkinsfile` 当前定义保持一一对应
	- 把 `robot/robot-execution` 这个 pipeline job 真正物化出来
