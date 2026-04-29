# Robot Execution Job Template

## 文档目标

这份文档固定 `robot-execution.Jenkinsfile` 对应的 seed job / job 参数模板思路，重点是把：

- 哪些参数属于全局默认来源
- 哪些参数属于 job 级默认值
- `ROBOTWS_GIT_REF` 和 `TESTLINE_CONFIGURATION_GIT_REF` 默认值应该怎么定

写清楚，避免后续每条 job 都各写一套。

## 分层原则

当前推荐的参数分层是：

- Jenkins 全局环境 / JCasC
  - `ROBOTWS_REPO_URL`
  - `TESTLINE_CONFIGURATION_REPO_URL`
  - `ROBOTWS_CREDENTIALS_ID`
  - `TESTLINE_CONFIGURATION_CREDENTIALS_ID`
- Job 默认值
  - `ROBOTWS_GIT_REF`
  - `TESTLINE_CONFIGURATION_GIT_REF`
- Job 临时 override
  - `ROBOTWS_REPO_URL_OVERRIDE`
  - `TESTLINE_CONFIGURATION_REPO_URL_OVERRIDE`
  - `ROBOTWS_CREDENTIALS_ID_OVERRIDE`
  - `TESTLINE_CONFIGURATION_CREDENTIALS_ID_OVERRIDE`

这样做的目的很明确：

- 仓库地址和凭据是基础设施默认来源，应该集中管理
- branch / ref 更像“这次想跑哪个版本”，更适合留在 job 模板里
- 真遇到例外时，再通过 override 参数临时覆盖

## `ROBOTWS_GIT_REF` 和 `TESTLINE_CONFIGURATION_GIT_REF` 默认值策略

当前已经确认固定为：

- `ROBOTWS_GIT_REF = master`
- `TESTLINE_CONFIGURATION_GIT_REF = master`

理由：

- 旧 Jenkins 链路里 `testcaseBranch` 默认值是 `master`
- 旧 Jenkins 链路里 `testlineConfigurationBranch` 默认值也是 `master`
- 当前我们还没有在新平台里确认两个仓库已经统一切到 `main`

因此当前固定策略是：

- 沿用旧链路默认值 `master`
- 后续如果两个仓库正式统一切换默认分支，再只改 seed job 模板和 Jenkinsfile 参数默认值这一处

不要把这个变化散到多个 job 手工改。

## 推荐参数模板

完整参数清单和默认值同步以这两个文件为准：

- [robot-execution-job.groovy](robot-execution-job.groovy)
- [../pipelines/robot-execution.Jenkinsfile](../pipelines/robot-execution.Jenkinsfile)

下面这张表只保留默认值策略里最关键的参数。

| 参数名 | 建议默认值 | 说明 |
| --- | --- | --- |
| `TESTLINE` | 空 | 由触发方决定 |
| `ROBOTCASE_PATH` | 空 | 由触发方决定 |
| `ROBOTWS_GIT_REF` | `master` | 当前沿用旧链路默认值 |
| `TESTLINE_CONFIGURATION_GIT_REF` | `master` | 当前沿用旧链路默认值 |
| `ROBOTWS_REPO_URL_OVERRIDE` | 空 | 默认不覆盖全局环境 |
| `TESTLINE_CONFIGURATION_REPO_URL_OVERRIDE` | 空 | 默认不覆盖全局环境 |
| `ROBOTWS_CREDENTIALS_ID_OVERRIDE` | 空 | 默认不覆盖全局环境 |
| `TESTLINE_CONFIGURATION_CREDENTIALS_ID_OVERRIDE` | 空 | 默认不覆盖全局环境 |
| `CALLBACK_MAX_ATTEMPTS` | `3` | callback 失败重试次数 |
| `CALLBACK_BACKOFF_SECONDS` | `2` | callback 线性退避基数 |
| `CALLBACK_IGNORE_FAILURE` | `true` | callback 最终失败时不直接打断主执行结果 |

## 对应 Job DSL 文件

实际可落地的 Job DSL 已经放到：

- [robot-execution-job.groovy](robot-execution-job.groovy)

这个文件现在承担的是“参数清单和 job 物化定义的 source of truth”，模板文档主要保留分层原则和默认值策略，避免同一份 DSL 在文档里再复制一遍后产生漂移。

## 当前建议

如果后续开始正式做 seed job，优先把下面 3 件事先固定：

1. `ROBOTWS_GIT_REF` 和 `TESTLINE_CONFIGURATION_GIT_REF` 保持默认 `master`，直到仓库官方默认分支发生统一切换
2. `robot/robot-execution` 是否就是最终 job naming 约定
3. 例外场景是否允许使用 `*_OVERRIDE`，还是只开放给管理员 job
