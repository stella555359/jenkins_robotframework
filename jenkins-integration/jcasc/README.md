# jcasc

这里放 Jenkins Configuration as Code 相关文件。

这一层建议承接：

- controller / agent 的基础配置
- tools / nodes / clouds / plugin catalog
- credentials 引用名和 secret 使用约定

这里不直接放真实 secret。

建议后续按下面方向继续收口：

- `jenkins.yaml`
- plugin catalog / plugin list
- node / label 约定
- credentials id 命名规范

当前已补：

- `jenkins.yaml`
	- 一份围绕 `robot` 执行链的 JCasC 示例
	- 包含 controller 基础项，例如 system message、controller executor 策略、location
	- 包含一个静态 inbound node 示例，固定 `robot linux ute` 这类 agent label 约定写法
	- 直接固定真实 Robot 主线需要的 `ROBOTWS_REPO_URL` / `TESTLINE_CONFIGURATION_REPO_URL`
	- 创建 `seed/jenkins-robotframework-seed`，用于执行 `jenkins-integration/jobs/*_job.groovy`
	- checkout 默认改为 agent-local key，不再要求 controller 维护 `robotws-ssh` / `testline-config-ssh`
	- 通过 controller 环境变量注入 pip token，以及 agent launcher 所需的 SSH private key path

## 当前落地方式

之前真实 Robot case 跑通时，如果是在 Jenkins UI 里手工配置：

```text
Manage Jenkins -> System -> Global properties -> Environment variables
```

现在应改为由 `jenkins.yaml` 管理。也就是说：

- `ROBOTWS_REPO_URL`
- `TESTLINE_CONFIGURATION_REPO_URL`
- `JENKINS_ROBOTFRAMEWORK_REPO_URL`
- `JENKINS_ROBOTFRAMEWORK_GIT_REF`
- `JENKINS_ROBOTFRAMEWORK_CREDENTIALS_ID`
- `ROBOTWS_CREDENTIALS_ID`
- `TESTLINE_CONFIGURATION_CREDENTIALS_ID`
- `PIP_INDEX_URL`
- `PIP_EXTRA_INDEX_URL`
- `PIP_TRUSTED_HOST`

这些 Jenkins 全局环境变量都从 JCasC 注入，不再依赖 UI 手工填写。

当前 `jenkins.yaml` 里，非敏感值直接写死在 YAML：

```text
ROBOTWS_REPO_URL=git@wrgitlab.ext.net.nokia.com:RAN/robotws.git
TESTLINE_CONFIGURATION_REPO_URL=git@wrgitlab.ext.net.nokia.com:RAN/configuration-management/testline_configuration.git
```

敏感值里，单行值仍从 controller 环境变量读取；controller 只持有 agent launcher 私钥。checkout 所需的 GitLab key 保留在 agent 本机，通过 node env 注入 key path：

```text
PIP_INDEX_URL
PIP_EXTRA_INDEX_URL
PIP_TRUSTED_HOST
T813_AGENT_SSH_PRIVATE_KEY_PATH
ROBOTWS_GIT_SSH_KEY_PATH
TESTLINE_CONFIGURATION_GIT_SSH_KEY_PATH
```

可参考 `deploy/env/jenkins-jcasc.env.example` 在服务器上准备真实环境变量。

## 当前推荐的 repo 与 credentials 约定

针对 `robot` 执行链，当前更推荐把“稳定不变的仓库来源”固定在 Jenkins 全局环境 / JCasC 里，而不是分散到每个 job 的参数默认值。

推荐分层如下：

- Jenkins 全局环境 / JCasC
	- `ROBOTWS_REPO_URL`
	- `TESTLINE_CONFIGURATION_REPO_URL`
	- `ROBOTWS_CREDENTIALS_ID`
	- `TESTLINE_CONFIGURATION_CREDENTIALS_ID`
	- `PIP_INDEX_URL`
	- `PIP_EXTRA_INDEX_URL`
	- `PIP_TRUSTED_HOST`
- Job / seed job 默认值
	- `ROBOTWS_GIT_REF`，当前默认 `master`
	- `TESTLINE_CONFIGURATION_GIT_REF`，当前默认 `master`
- Job 级临时 override
	- `ROBOTWS_REPO_URL_OVERRIDE`
	- `TESTLINE_CONFIGURATION_REPO_URL_OVERRIDE`
	- `ROBOTWS_CREDENTIALS_ID_OVERRIDE`
	- `TESTLINE_CONFIGURATION_CREDENTIALS_ID_OVERRIDE`

这样分层的目的很明确：

- repo URL 和 credentials id 属于基础设施配置，应该尽量有单一来源
- branch / ref 更容易随环境或阶段变化，适合留在 job 模板里配置
- 真遇到例外场景时，再通过 `*_OVERRIDE` 参数临时覆盖

## credentials id 命名建议

当前推荐：

- `t813-agent-ssh`
	- 用于 Jenkins controller 连接 `t813-agent`

如果后续仍需要回退到 Jenkins credentials 模式，可以在 job metadata 里显式指定 `credentials_id` 和 `credential_kind=sshagent`。默认路径已经改为 agent-local key。

## 为什么不推荐直接把 repo URL 做成 job 参数默认值

因为一旦真实仓库地址散到多个 job 里：

- 容易漂移
- 难集中替换
- 凭据和 URL 的关系也更难统一管理

当前 `checkout_sources.py` 已经支持“显式 override 优先，否则回落到全局环境变量”的模式，所以更适合把默认正式来源放在 JCasC / 全局环境里。

## 示例文件

- [jenkins.yaml](jenkins.yaml)
	- 围绕 `robot` 执行链的 controller / node / credentials 示例

## node 示例说明

当前 `jenkins.yaml` 里的 node 示例故意先用静态 inbound agent，原因是：

- 字段结构更稳定，适合作为仓库内默认样板
- 不强绑定某一种 SSH launcher 或 cloud plugin
- 更适合先把 label、remoteFS、agent 环境变量这些公共约定固定下来

如果你的正式 Jenkins 环境后续使用的是 SSH agent、Kubernetes agent 或 cloud agent，推荐做法是：

- 先在 Jenkins UI 里配通真实 agent
- 再从 JCasC export 结果里拿对应 launcher 片段
- 替换 `jenkins.yaml` 里的 `launcher` 部分，而不是重写整个 node 结构
