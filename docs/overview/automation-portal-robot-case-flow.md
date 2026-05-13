# Automation Portal 触发真实 Robot Case 流程

本文说明部署完成后，如何从 `automation-portal` 页面创建真实 Robot case run，以及这个 run 如何经过 `platform-api`、Jenkins、`jenkins-integration`、Robot 执行、callback，最终回到 Portal 详情页。

## 1. 是否可以直接从 Portal 创建

可以创建，但建议先确认下面几项已经就绪。只要其中一项没配置好，Portal 仍然能创建 run 记录，但触发 Jenkins 或执行 Robot 时会失败。

| 检查项 | 目标状态 | 相关位置 |
|---|---|---|
| Portal | `https://10.71.210.104/` 能打开 | Nginx `/` 指向 `automation-portal/dist` |
| API | `https://10.71.210.104/api/health` 正常 | `platform-api` systemd + Nginx `/api/` |
| Jenkins | `https://10.71.210.104/jenkins/` 能访问 | Jenkins prefix `/jenkins` |
| platform-api Jenkins 配置 | `.env` 中 Jenkins URL、job path、用户名和 token 正确 | `/opt/jenkins_robotframework/platform-api/.env` |
| Jenkins job | `robot/robot-execution` 已存在 | `jenkins-integration/jobs/robot-execution-job.groovy` |
| Jenkins Agent | 目标 Agent 在线且有 executor | Jenkins Nodes 页面 |
| 源码 checkout | Jenkins 全局环境或 job 参数能提供 `robotws` 和 `testline_configuration` repo URL / credentials | Jenkins global env / credentials / job 参数 |
| Python 环境 | Agent 上存在 `/home/ute/CIENV/<TESTLINE>/bin/activate`，除非 job 另行覆盖 | `prepare_taf_environment.py` |

最小 smoke 建议：

```bash
curl -k https://127.0.0.1/api/health
curl -k -I https://127.0.0.1/jenkins/
```

Jenkins job 页面建议也先手动点一次 `Build with Parameters`，确认 Agent、checkout、Python 环境和 Robot 基础链路是通的。

## 2. Jenkins 侧最短配置清单

Portal 能否真正把 run 跑起来，关键不在 Portal 页面本身，而在 Jenkins 这几项是否已经配齐。

### 2.1 Jenkins 全局环境变量

`checkout_sources.py` 默认从 Jenkins 全局环境里拿下面这些值。如果不配，Jenkins 虽然能启动 Pipeline，但会在 checkout 阶段失败。

当前推荐使用 JCasC 注入这些全局环境变量，不再手工到 Jenkins UI 维护。配置文件：

```text
jenkins-integration/jcasc/jenkins.yaml
```

JCasC 中至少应包含：

| 环境变量 | 作用 | 推荐值示例 |
|---|---|---|
| `ROBOTWS_REPO_URL` | `robotws` 源码仓库地址 | `git@your-git-host:team/robotws.git` 或对应 HTTPS 地址 |
| `TESTLINE_CONFIGURATION_REPO_URL` | `testline_configuration` 源码仓库地址 | `git@your-git-host:team/testline_configuration.git` 或对应 HTTPS 地址 |
| `ROBOTWS_GIT_SSH_KEY_PATH` | `t813-agent` 上 checkout `robotws` 使用的本机私钥路径 | `/home/jenkins/.ssh/jenkins_gitlab_rsa` |
| `TESTLINE_CONFIGURATION_GIT_SSH_KEY_PATH` | `t813-agent` 上 checkout `testline_configuration` 使用的本机私钥路径 | `/home/jenkins/.ssh/jenkins_gitlab_rsa` |
| `PIP_INDEX_URL` | `create-venv` 安装 TAF 依赖时使用的主 pip index | 内部 Artifactory PyPI URL |
| `PIP_EXTRA_INDEX_URL` | `create-venv` 安装 TAF 依赖时使用的额外 pip index | 第二内部 Artifactory PyPI URL |
| `PIP_TRUSTED_HOST` | `create-venv` 安装 TAF 依赖时的 pip trusted-host | 空格分隔的 Artifactory host 列表 |

当前环境如果采用 SSH 方式，`jenkins.yaml` 中已经固定：

```text
ROBOTWS_REPO_URL=git@wrgitlab.ext.net.nokia.com:RAN/robotws.git
TESTLINE_CONFIGURATION_REPO_URL=git@wrgitlab.ext.net.nokia.com:RAN/configuration-management/testline_configuration.git
ROBOTWS_GIT_SSH_KEY_PATH=/home/jenkins/.ssh/jenkins_gitlab_rsa
TESTLINE_CONFIGURATION_GIT_SSH_KEY_PATH=/home/jenkins/.ssh/jenkins_gitlab_rsa
```

这些敏感或环境私有值仍由 Jenkins controller 环境变量提供：

```text
PIP_INDEX_URL=https://<user>:<token>@artifactory-hz1.ext.net.nokia.com/artifactory/api/pypi/ute-pypi-virtual/simple
PIP_EXTRA_INDEX_URL=https://<user>:<token>@artifactory-espoo2.int.net.nokia.com/artifactory/api/pypi/ute-pypi-virtual/simple
PIP_TRUSTED_HOST=artifactory-hz1.ext.net.nokia.com artifactory-espoo2.int.net.nokia.com
```

JCasC 生效方式见 [jenkins-integration/jcasc/README.md](c:/TA/jenkins_robotframework/jenkins-integration/jcasc/README.md) 和 [deploy/DEPLOYMENT.md](c:/TA/jenkins_robotframework/deploy/DEPLOYMENT.md)。

如果你暂时不用 JCasC，才需要在 Jenkins UI 手工配置：

```text
Manage Jenkins -> System -> Global properties -> Environment variables
```

### 2.2 Jenkins 全局凭据

路径：

```text
Manage Jenkins -> Credentials -> System -> Global credentials
```

如果你的 Jenkins Console Output 报下面这种错误：

```text
No such DSL method 'sshagent'
```

说明当前 Jenkins 缺少的是 `SSH Agent` 插件提供的 Pipeline step，而不是 Agent 连接本身没配好。`SSH Build Agents` 用于让 Jenkins Master 连接执行节点，`SSH Agent` 才是 Pipeline 里 `sshagent { ... }` 这一步需要的插件。

#### 2.2.1 安装 `SSH Agent` 插件

路径通常是：

```text
Manage Jenkins -> Plugins
```

安装步骤：

1. 打开 `Available plugins`。
2. 搜索 `SSH Agent`。
3. 安装 `SSH Agent` 插件。
4. 安装完成后，如果 Jenkins 要求重启，就执行安全重启。

注意：这里要装的是 `SSH Agent`，不是 `SSH Build Agents`。前者提供 Pipeline 里的 `sshagent { ... }` step，后者负责 Jenkins Master 到 Agent 的 SSH 连接。

#### 2.2.2 仅保留 `t813-agent-ssh`

当前默认只要求 Jenkins controller 持有 `t813-agent-ssh`，用于连接执行节点。`robotws` 和 `testline_configuration` checkout 已改为直接使用 `t813-agent` 本机私钥路径，不再要求 `robotws-ssh` / `testline-config-ssh` 这两个 Jenkins credentials。

`t813-agent-ssh` 的 `Kind` 选择：

```text
SSH Username with private key
```

推荐填写方式：

| 字段 | `t813-agent-ssh` 推荐值 |
|---|---|---|
| `Kind` | `SSH Username with private key` |
| `Scope` | `Global` |
| `Username` | `jenkins` |
| `ID` | `t813-agent-ssh` |
| `Description` | `SSH key for t813-agent launcher` |
| `Private Key` | 贴入完整 PEM RSA 私钥文本 |

`Private Key` 里需要粘贴的是完整私钥，包括：

```text
-----BEGIN ... PRIVATE KEY-----
...
-----END ... PRIVATE KEY-----
```

#### 2.2.3 这把私钥怎么准备

当前链路里真正执行 `git clone` 的位置在 Agent 上，所以更推荐在 `t813-agent` 上以 Jenkins 执行用户生成 GitLab 访问 key：

```bash
sudo su - jenkins
ssh-keygen -t ed25519 -C "jenkins-gitlab" -f ~/.ssh/jenkins_gitlab_rsa -N ""
```

生成后会得到：

1. 私钥：`~/.ssh/jenkins_gitlab_rsa`
2. 公钥：`~/.ssh/jenkins_gitlab_rsa.pub`

然后：

1. 把 `cat ~/.ssh/jenkins_gitlab_rsa.pub` 输出的公钥，加到有权限访问这两个仓库的 GitLab 用户账号 `SSH Keys` 页面。
2. 把 `cat ~/.ssh/jenkins_gitlab_rsa` 输出的完整私钥文本，贴到 Jenkins credentials 的 `Private Key` 字段。

#### 2.2.4 在 `t813-agent` 上手工验证这把 key 能访问两个 GitLab 仓库

建议先直接登录 `t813-agent`，再切到实际执行 Jenkins job 的用户下验证。下面命令假设当前使用的是上面生成的私钥 `~/.ssh/jenkins_gitlab_rsa`。

先切用户：

```bash
sudo su - jenkins
```

先验证 SSH 到 GitLab 本身是否打通：

```bash
ssh -i ~/.ssh/jenkins_gitlab_rsa -T git@wrgitlab.ext.net.nokia.com
```

第一次连接通常会提示是否接受 host key，输入 `yes`。如果打通，通常会看到类似“Welcome”或“authenticated”之类的提示；即使返回“shell access is not supported”也不代表失败，只要说明认证成功即可。

然后分别验证两个仓库是否可读：

```bash
GIT_SSH_COMMAND='ssh -i ~/.ssh/jenkins_gitlab_rsa -o IdentitiesOnly=yes' \
git ls-remote git@wrgitlab.ext.net.nokia.com:RAN/robotws.git
```

```bash
GIT_SSH_COMMAND='ssh -i ~/.ssh/jenkins_gitlab_rsa -o IdentitiesOnly=yes' \
git ls-remote git@wrgitlab.ext.net.nokia.com:RAN/configuration-management/testline_configuration.git
```

预期结果：

1. 如果命令能打印出 `HEAD` 和若干分支/提交哈希，说明这把 key 对对应仓库有读取权限。
2. 如果报 `Permission denied (publickey)`，说明 GitLab 侧还没信任这把公钥，或者加错了账号 / Deploy Key。
3. 如果报 host key 相关错误，先完成第一次 `ssh -T` 的 host key 接受流程。
4. 如果只一个仓库成功、另一个失败，说明这把 key 还没有同时拿到两个仓库的读取权限。

如果你希望 Jenkins job 运行时默认就使用这把 key，也可以额外写一个临时 `~/.ssh/config` 做本机验证：

```bash
cat > ~/.ssh/config <<'EOF'
Host wrgitlab.ext.net.nokia.com
  User git
  IdentityFile ~/.ssh/jenkins_gitlab_rsa
  IdentitiesOnly yes
EOF
chmod 600 ~/.ssh/config
```

然后重新执行：

```bash
ssh -T git@wrgitlab.ext.net.nokia.com
git ls-remote git@wrgitlab.ext.net.nokia.com:RAN/robotws.git
git ls-remote git@wrgitlab.ext.net.nokia.com:RAN/configuration-management/testline_configuration.git
```

这一步主要用于人工验证。Jenkins Pipeline 里真正使用的还是 Jenkins credentials 注入出来的 key，不依赖你是否长期保留这份 `~/.ssh/config`。

建议至少有两类凭据：

| Credentials ID | 类型 | 用途 |
|---|---|---|
| `t813-agent-ssh` | SSH Username with private key | Jenkins Master 连接 `t813-agent` 节点 |

默认情况下，`robotws` 和 `testline_configuration` 通过 agent 本机 `ROBOTWS_GIT_SSH_KEY_PATH` / `TESTLINE_CONFIGURATION_GIT_SSH_KEY_PATH` 执行 checkout。只有旧 Jenkins credentials 还存在，并且显式指定 `credential_kind=sshagent` 时，才会回到 `sshagent` 分支。

如果你当前就是想先走最短链路：

1. 保证 `t813-agent` 上已经有可用的 GitLab 私钥文件。
2. 在 JCasC env 里设置 `ROBOTWS_GIT_SSH_KEY_PATH` 和 `TESTLINE_CONFIGURATION_GIT_SSH_KEY_PATH`。
3. 这样 Pipeline 会在 agent 上直接执行带 `GIT_SSH_COMMAND` 的 `git clone` / `git fetch`，不会依赖 Jenkins checkout credentials。

### 2.2.5 `create-venv` 的内部 PyPI / Artifactory 配置

如果你要让 Jenkins 在 `TAF mode=create-venv` 下自动安装 `robotws/dependencies.py<major><minor>-rf50.lock`，不要再依赖 Agent 宿主机已有的 `pip.conf`。当前实现改成了在 `create-venv` 自动安装分支里显式执行等价于下面这种命令：

```bash
python -m pip install -r /automation/workspace/workspace/robot/robot-execution/robotws/dependencies.py311-rf50.lock \
  --no-deps \
  -i https://artifactory-espoo2.int.net.nokia.com/artifactory/api/pypi/ute-pypi-virtual/simple \
  --proxy http://10.158.100.9:8080 \
  --trusted-host artifactory-espoo2.int.net.nokia.com
```

其中可配置部分仍然来自 Jenkins 环境变量：

```text
PIP_INDEX_URL
PIP_EXTRA_INDEX_URL
PIP_TRUSTED_HOST
```

推荐做法：

1. 在 Jenkins `Manage Jenkins -> System -> Global properties -> Environment variables` 配这三个值。
2. 如果某次构建想临时覆盖，也可以在 job 参数里填：

```text
PIP_INDEX_URL_OVERRIDE
PIP_EXTRA_INDEX_URL_OVERRIDE
PIP_TRUSTED_HOST_OVERRIDE
```

优先级：

```text
PIP_INDEX_URL_OVERRIDE > Jenkins 全局环境 PIP_INDEX_URL > PIP_EXTRA_INDEX_URL_OVERRIDE > Jenkins 全局环境 PIP_EXTRA_INDEX_URL
```

补充说明：

1. `create-venv` 自动安装 `robotws` lock 文件时会带 `--no-deps`。
2. 当前脚本只会选择一个生效的内部 index URL，优先主 index，主 index 为空时再退回 `PIP_EXTRA_INDEX_URL`。
3. 当前脚本固定使用 `--proxy http://10.158.100.9:8080`。
4. `PIP_TRUSTED_HOST` 如果配置了多个 host，会被展开成多个 `--trusted-host <host>`。
5. 如果 `create-venv` 下既没有配置 `PIP_INDEX_URL`，也没有配置 `PIP_EXTRA_INDEX_URL`，当前脚本会直接失败，并提示缺少内部 pip index 配置，而不是再去外网 PyPI 兜底。

### 2.3 最短手工创建 `robot/robot-execution` job

如果当前 Jenkins 里还没有 `robot/robot-execution`，第一轮可以直接在 Jenkins 页面手工创建，不必先走 Job DSL。

操作步骤：

1. 打开 Jenkins：`https://10.71.210.104/jenkins/`
2. 登录 Jenkins。
3. 点击 `New Item`。
4. 名称填 `robot/robot-execution`。
5. 如果 Jenkins 不允许直接带 `/` 创建，就先建 Folder `robot`，再在里面新建 Pipeline `robot-execution`。
6. 类型选择 `Pipeline`。
7. 在 `Pipeline` 配置区按下面填写：

```text
Definition: Pipeline script from SCM
SCM: Git
Repository URL: https://github.com/stella555359/jenkins_robotframework.git
Credentials: public repo 第一轮可留空；受限网络或私有仓库再改成 PAT / SSH credentials
Branch Specifier: */feature/jenkins-integration
Script Path: jenkins-integration/pipelines/robot-execution.Jenkinsfile
Repository browser: Auto / 不填 / GitHub
Additional Behaviours: 先留空
Lightweight checkout: 第一轮不要勾选
```

如果你使用 SSH 读取当前仓库，`Repository URL` 改成：

```text
git@github.com:stella555359/jenkins_robotframework.git
```

此时 `Credentials` 不能留空，而应选择 Jenkins 中可访问 GitHub 的 SSH 凭据。

### 2.4 创建后立即验证

保存后，预期 job 页面地址是：

```text
https://10.71.210.104/jenkins/job/robot/job/robot-execution/
```

先在 Jenkins 页面打开 `Build with Parameters`，确认至少能看到这些参数：

```text
RUN_ID
TESTLINE
ROBOTCASE_PATH
CASE_NAME
ROBOT_SELECTED_TESTS
ROBOT_VARIABLES_JSON
PYTHON_ENV_ROOT
ROBOTWS_ROOT
TESTLINE_VARIABLES_PATH
PLATFORM_API_BASE_URL
```

第一轮建议手工点一次 smoke：

```text
TESTLINE=7_5_UTE5G402T813
ROBOTCASE_PATH=testsuite/Hangzhou/RRM/example.robot
PLATFORM_API_BASE_URL=https://10.71.210.104
```

如果 job 页面没有 `Build with Parameters`，或者参数不全，通常说明：

1. `Script Path` 不对。
2. 分支不对。
3. Jenkins 还没成功从 SCM 读取 Jenkinsfile。

## 3. Portal 表单字段怎么填

Portal 的 `New Robot Run` 表单当前会做两件事：

1. `POST /api/runs` 创建 run 记录。
2. `POST /api/runs/{run_id}/trigger` 触发 Jenkins job。

字段含义如下。

| Portal 字段 | 是否必填 | 传到 platform-api / Jenkins 的字段 | 含义 | 示例 |
|---|---:|---|---|---|
| `Testline` | 是 | `testline` / Jenkins `TESTLINE` | 目标测试线标识。Jenkins 默认会用它找 Python 环境 `/home/ute/CIENV/<TESTLINE>`，并找变量目录 `testline_configuration/<TESTLINE>`。 | `7_5_UTE5G402T813` 或现场实际 testline 名称 |
| `Robot case path` | 是 | `robotcase_path` / Jenkins `ROBOTCASE_PATH` | Robot suite 文件路径。可以相对 Jenkins workspace，也可以相对 checkout 后的 `robotws` 根目录。 | `testsuite/Hangzhou/RRM/example.robot` |
| `Case name` | 否 | metadata `case_name` / Jenkins `CASE_NAME` | 单个 Robot test case 名称。最终会转换为 Robot 命令中的 `-t <case name>`。 | `Attach UE` |
| `Build` | 否 | `build`，并自动进入 `ROBOT_VARIABLES_JSON.BUILD` | 版本号或构建号。platform-api 会把它补成 Robot 变量 `BUILD`，除非 JSON 里已经显式提供 `BUILD`。 | `SBTS26R3.ENB.9999` |
| `TAF mode` | 否 | metadata `taf_mode` / Jenkins `TAF_MODE` | Python/TAF 环境准备方式。`reuse` 复用已有 CIENV，`create-venv` 新建 CIENV 并从当前 `robotws` checkout 安装 TAF 依赖，`skip-install` 跳过安装步骤。 | `reuse` / `create-venv` |
| `Robotws git ref` | 否 | metadata `robotws_ref` / Jenkins `ROBOTWS_GIT_REF` | checkout `robotws` 时使用的 branch/tag/commit。默认 `master`。 | `feature/robot` |
| `Selected tests` | 否 | metadata `selected_tests` / Jenkins `ROBOT_SELECTED_TESTS` | 多个 Robot test case 名称，每行一个。最终每行都会转换为一个 `-t`。 | `Attach UE` 换行 `Detach UE` |
| `Robot variables JSON` | 否 | metadata `robot_variables` / Jenkins `ROBOT_VARIABLES_JSON` | Robot `-v KEY:VALUE` 变量映射。必须是 JSON object。 | `{ "AF_PATH": "/path/to/af", "UE_COUNT": "7" }` |

注意：

1. `Case name` 和 `Selected tests` 都会变成 Robot `-t`。如果两边都填，最终会合并去重后一起传给 Robot。
2. `Build` 不直接变成 Jenkins 参数里的 `BUILD`，而是进入 `ROBOT_VARIABLES_JSON`，最终成为 Robot 变量 `-v BUILD:<value>`。
3. `TAF mode=create-venv` 时，当前实现会新建 CIENV，并优先从当前 `robotws` checkout 里的 `dependencies.py<major><minor>-rf50.lock` 安装 TAF 依赖；如果对应 lock 不存在，再回退到 `requirements.cfg`。
4. `Robot variables JSON` 必须是对象，不能是数组或普通字符串。
5. 如果不确定 testline 的完整名称，应优先使用 Agent 上实际 Python 环境目录和 `testline_configuration` 目录里的名称。

一个较完整的示例：

```text
Testline: 7_5_UTE5G402T813
Robot case path: testsuite/Hangzhou/RRM/example.robot
Case name: Attach UE
Build: SBTS26R3.ENB.9999
TAF mode: create-venv
Robotws git ref: feature/robot
Selected tests:
  Attach UE
  Detach UE
Robot variables JSON:
{
  "AF_PATH": "/automation/downloads/SBTS26R3.ENB.9999",
  "UE_COUNT": "7"
}
```

如果只是第一轮连通性验证，可以先只填必填项，并让 `Robot variables JSON` 保持一个合法空对象：

```json
{}
```

## 4. Run 如何对应到 Jenkins Agent

当前链路里，Portal 表单不选择 Agent，platform-api 也不向 Jenkins 传 Agent 参数。

实际由 Jenkins 决定在哪个 Agent 上跑：

```text
Portal 表单 -> platform-api -> Jenkins job robot/robot-execution -> Jenkins 调度 Agent
```

当前 `jenkins-integration/pipelines/robot-execution.Jenkinsfile` 已固定为：

```groovy
pipeline {
  agent { label 't813 && robot' }
    ...
}
```

这表示 Jenkins 只会把构建分配给同时带有 `t813` 和 `robot` label 的 Agent。它仍然不会根据 Portal 的 `Testline` 动态切换到别的节点。

如果后续需要改成别的固定 Agent，常见方式有两种：

### 4.1 推荐方式：在 Jenkinsfile 中固定 label

把 `agent any` 改成目标 label，例如：

```groovy
pipeline {
    agent { label 't813 && robot' }
    ...
}
```

前提是目标 Agent 的 label 包含 `t813` 和 `robot`。

### 4.2 运维方式：让 job 只能调度到目标节点

在 Jenkins 页面中限制 `robot/robot-execution` 的运行节点，或只让目标 Agent 具备可用 executor。这样即使 Jenkinsfile 是 `agent any`，实际也只能落到指定 Agent。

建议第一轮真实 Robot case 前确认：

```text
Manage Jenkins -> Nodes
目标 Agent 在线
目标 Agent labels 包含期望 label
目标 Agent executors > 0
```

JCasC 示例里有一个参考节点：

```yaml
labelString: "robot linux ute"
```

但你当前页面里提到的 `t813-agent` 如果 label 是 `t813 robot`，那 Jenkinsfile label 应该按实际 label 写，例如：

```groovy
agent { label 't813 && robot' }
```

## 5. 端到端流程图

```mermaid
flowchart TD
    User[Windows Browser User] --> Portal[automation-portal React UI]
    Portal --> Form[New Robot Run Form]

    Form --> CreateApi[POST /api/runs]
    CreateApi --> RunServiceCreate[platform-api run_service.run_create]
    RunServiceCreate --> Validate{executor_type == robot?\nrobotcase_path present?}
    Validate -->|no| CreateError[400 validation error]
    Validate -->|yes| SqliteCreate[(SQLite runs table\nstatus=created)]
    SqliteCreate --> CreateResp[run_id returned]

    CreateResp --> TriggerApi["POST /api/runs/RUN_ID/trigger"]
    TriggerApi --> RunServiceTrigger[platform-api run_service.trigger_run]
    RunServiceTrigger --> BuildParams[jenkins_service.build_robot_jenkins_parameters]
    BuildParams --> JenkinsPost[POST Jenkins buildWithParameters]
    JenkinsPost --> JenkinsQueue[Jenkins queue item]
    JenkinsQueue --> UpdateTriggered[(runs table\nstatus=triggered\njenkins_build_ref=queue_url)]
    UpdateTriggered --> PortalDetail["Portal navigates to /runs/RUN_ID"]

    JenkinsQueue --> JenkinsJob[Jenkins job robot/robot-execution]
    JenkinsJob --> PipelineScm[Read Jenkinsfile from jenkins_robotframework SCM]
    PipelineScm --> AgentSelect{Pipeline agent}
    AgentSelect -->|current| TargetAgent[t813-agent labels t813 and robot]

    subgraph Pipeline[jenkins-integration pipeline stages]
        Materialize[Materialize Run Request\nmaterialize_run_request.py]
        Checkout[Prepare Workspace\ncheckout_sources.py]
        EnvPrep[Prepare TAF Python env\nprepare_taf_environment.py]
        BuildCmd[Build Robot Command\nbuild_robot_command.py]
        RunRobot["Run Robot Case\nbash artifacts/run-robot.sh"]
        Callback[post_run_callback.py]
        Materialize --> Checkout --> EnvPrep --> BuildCmd --> RunRobot --> Callback
    end

      TargetAgent --> Workspace[/automation/workspace/workspace/robot/robot-execution/]
      Workspace --> Pipeline

      Checkout --> Robotws[(robotws checkout from ROBOTWS_REPO_URL)]
      Checkout --> TestlineConfig[(testline_configuration checkout from TESTLINE_CONFIGURATION_REPO_URL)]
    EnvPrep --> PythonEnv["/home/ute/CIENV/TESTLINE/bin/activate"]
    BuildCmd --> RobotCommand["python -m robot\n--pythonpath robotws\n-V testline_configuration/TESTLINE\n-t selected tests\n-v variables\nROBOTCASE_PATH"]

    RunRobot --> Artifacts["artifacts/**"]
    Callback --> CallbackApi["POST /api/runs/RUN_ID/callbacks/jenkins"]
    CallbackApi --> ApplyCallback[platform-api apply_run_callback]
    ApplyCallback --> UpdateFinal[(runs table\nstatus=passed/failed\njenkins_build_ref=JOB#BUILD\nartifact_manifest)]
    UpdateFinal --> PortalPoll[Portal run detail refresh]
    PortalPoll --> FinalView[Status, Jenkins ref, artifacts shown]

      DeployCopy[/opt/jenkins_robotframework deployment copy/] -. not used as Jenkins build workspace .-> JenkinsJob
```

## 6. 关键配置关系

### 6.1 platform-api `.env`

`platform-api` 触发 Jenkins 时使用这些配置：

```text
JENKINS_BASE_URL=http://127.0.0.1:8080/jenkins
JENKINS_ROBOT_JOB_PATH=job/robot/job/robot-execution
JENKINS_USERNAME=<jenkins-user>
JENKINS_API_TOKEN=<jenkins-api-token>
JENKINS_INSECURE_TLS=false
JENKINS_CALLBACK_INSECURE_TLS=true
PUBLIC_BASE_URL=https://10.71.210.104
```

含义：

| 配置 | 作用 |
|---|---|
| `JENKINS_BASE_URL` | platform-api 触发 Jenkins 的内部地址。 |
| `JENKINS_ROBOT_JOB_PATH` | 要触发的 Jenkins job 路径。当前目标是 `robot/robot-execution`。 |
| `JENKINS_USERNAME` / `JENKINS_API_TOKEN` | Jenkins buildWithParameters 鉴权。 |
| `JENKINS_INSECURE_TLS` | `platform-api` 触发 Jenkins 时是否跳过 TLS 证书校验。只有 `JENKINS_BASE_URL` 指向自签名 HTTPS Jenkins 时才需要设成 `true`。 |
| `JENKINS_CALLBACK_INSECURE_TLS` | `platform-api` 触发 Jenkins 时默认透传给 job 的 `CALLBACK_INSECURE_TLS`。当前自签名 HTTPS 部署建议保持 `true`。 |
| `PUBLIC_BASE_URL` | 传给 Jenkins，供 callback 回写 `https://10.71.210.104/api/runs/{run_id}/callbacks/jenkins`。 |

### 6.2 Jenkins job 参数

platform-api 会把 run record 转成 Jenkins 参数。核心映射如下：

| Jenkins 参数 | 来源 | 用途 |
|---|---|---|
| `RUN_ID` | platform-api 生成 | callback 时定位 run。 |
| `TESTLINE` | Portal `Testline` | Python env 和 testline variables 默认路径。 |
| `ROBOTCASE_PATH` | Portal `Robot case path` | Robot suite 文件路径。 |
| `CASE_NAME` | Portal `Case name` | 作为 Robot `-t`。 |
| `ROBOT_SELECTED_TESTS` | Portal `Selected tests` | 每行一个 Robot `-t`。 |
| `ROBOT_VARIABLES_JSON` | Portal `Robot variables JSON` + `Build` | 转成 Robot `-v KEY:VALUE`。 |
| `TAF_MODE` | Portal `TAF mode` | 控制 Python/TAF 环境准备方式。 |
| `PIP_INDEX_URL_OVERRIDE` | Jenkins job 参数覆盖 | `create-venv` 安装依赖时覆盖主 pip index。 |
| `PIP_EXTRA_INDEX_URL_OVERRIDE` | Jenkins job 参数覆盖 | `create-venv` 安装依赖时作为主 index 为空时的备用 pip index。 |
| `PIP_TRUSTED_HOST_OVERRIDE` | Jenkins job 参数覆盖 | `create-venv` 安装依赖时覆盖 trusted-host。 |
| `PLATFORM_API_BASE_URL` | `PUBLIC_BASE_URL` 或 metadata override | Jenkins callback 目标根地址。 |
| `CALLBACK_INSECURE_TLS` | Jenkins job 参数默认值 | callback 回写 `platform-api` 时是否跳过 TLS 证书校验。自签名 HTTPS 部署通常应保持开启。 |
| `ROBOTWS_GIT_REF` | metadata override，否则 `master` | checkout `robotws` ref。 |
| `TESTLINE_CONFIGURATION_GIT_REF` | metadata override，否则 `master` | checkout `testline_configuration` ref。 |

### 6.3 Jenkins global env / credentials

`checkout_sources.py` 默认需要这些 Jenkins 全局环境或 job 参数：

```text
ROBOTWS_REPO_URL
TESTLINE_CONFIGURATION_REPO_URL
ROBOTWS_GIT_SSH_KEY_PATH
TESTLINE_CONFIGURATION_GIT_SSH_KEY_PATH
```

如果这些变量没配，Jenkins 会像你已经看到的那样生成 `source-checkout.json`，但其中 `repo_url` 会是 `null`，后续 `checkout-sources.sh` 会直接报：

```text
Missing repo URL for robotws. Set ROBOTWS_REPO_URL.
Missing repo URL for testline_configuration. Set TESTLINE_CONFIGURATION_REPO_URL.
```

推荐的最小对应关系：

| Jenkins 全局变量 | 建议来源 |
|---|---|
| `ROBOTWS_REPO_URL` | `robotws` 实际 Git 地址 |
| `TESTLINE_CONFIGURATION_REPO_URL` | `testline_configuration` 实际 Git 地址 |
| `ROBOTWS_GIT_SSH_KEY_PATH` | `t813-agent` 上可读的 GitLab 私钥路径 |
| `TESTLINE_CONFIGURATION_GIT_SSH_KEY_PATH` | `t813-agent` 上可读的 GitLab 私钥路径 |

如果 workspace 下已经存在非 git 目录 `robotws/` 或 `testline_configuration/`，脚本可以复用目录。但真实部署建议配置 repo URL 和 agent 本机 key path，让 Jenkins 每次能同步源码。

如果当前已经改成 SSH 地址，但构建日志仍然报：

```text
No such DSL method 'sshagent'
```

那通常说明某次运行仍显式指定了 `credential_kind=sshagent`，但当前 Jenkins 没安装 `SSH Agent` 插件。默认 agent-local key 路径不依赖这个插件。

### 6.4 Jenkins workspace 与服务器部署代码的关系

当前链路里至少有三份代码副本：

| 副本 | 典型位置 | 用途 |
|---|---|---|
| 开发副本 | 开发机本地仓库 | 改代码、提交、push |
| 部署副本 | `/opt/jenkins_robotframework` | 给 `platform-api`、`automation-portal`、文档和部署侧使用 |
| Jenkins 构建副本 | `/automation/workspace/workspace/robot/robot-execution` | 给 `robot/robot-execution` job 运行时使用 |

关键点：

1. Jenkins job 运行时不会直接读取 `/opt/jenkins_robotframework`。
2. Jenkins job 会按它自己的 SCM 配置重新拉取 `jenkins_robotframework`。
3. `/opt/jenkins_robotframework` 上的本地修改，如果没有 push 到 GitHub，Jenkins job 看不到。
4. 你改了部署侧代码后，如果服务器本机要生效，仍然需要在 `/opt/jenkins_robotframework` 手动 `git pull`，然后重启对应服务或重新构建。

### 6.5 Robot 命令最终形态

`build_robot_command.py` 最终会生成类似命令：

```bash
. /home/ute/CIENV/<TESTLINE>/bin/activate
export http_proxy=''
export https_proxy=''
python -m robot \
  --pythonpath <workspace>/robotws \
  -v AF_PATH:<value> \
  -v BUILD:<build> \
  -x quicktest.xml \
  -b debug.log \
  -d <workspace>/artifacts/quicktest/retry-0/<suite-name> \
  -V <workspace>/testline_configuration/<TESTLINE> \
  -L TRACE \
  -t "Attach UE" \
  <workspace>/robotws/testsuite/Hangzhou/RRM/example.robot
```

如果 `Robot case path` 在 workspace 根目录下找不到，脚本会继续在 `<workspace>/robotws/` 下找。

## 7. Run 状态如何变化

| 阶段 | status | 说明 |
|---|---|---|
| Portal 创建 run | `created` | 已写入 SQLite，还没触发 Jenkins。 |
| trigger 成功 | `triggered` | Jenkins build 已进入 queue，`jenkins_build_ref` 暂时可能是 queue URL。 |
| trigger 失败 | `trigger_failed` | Jenkins URL、token、job path 或权限有问题。 |
| Jenkins callback 成功 | `passed` 或 `failed` | Jenkins 执行完后回写结果，`jenkins_build_ref` 变为 `JOB_NAME#BUILD_NUMBER`。 |

Portal 详情页显示的数据来自：

```text
GET /api/runs/{run_id}
GET /api/runs/{run_id}/artifacts
GET /api/runs/{run_id}/kpi
```

## 8. 第一轮真实 Robot Case 操作建议

1. 先在 Jenkins 页面确认 `robot/robot-execution` 可以手动 `Build with Parameters`。
2. 如果要固定 Agent，先把 Jenkinsfile 或 job 调度限制改好。
3. 在 Portal 只填最小字段：`Testline`、`Robot case path`、合法 JSON `{}`。
4. 创建后进入 run detail，确认状态从 `created` 到 `triggered`。
5. 到 Jenkins 对应 build 页面看 Console Output。
6. Jenkins 结束后回到 Portal detail，确认状态变为 `passed` 或 `failed`，并出现 `jenkins_build_ref` 和 artifacts。

第一轮建议不要同时填很多 Robot 变量。先跑一个最小 smoke case，链路通了再逐步补 `Build`、`Selected tests`、`AF_PATH` 等业务参数。

## 9. 常见失败点

| 现象 | 常见原因 | 排查方向 |
|---|---|---|
| Portal 创建失败 | `Robot variables JSON` 不是 object，或必填项为空 | 浏览器错误提示、platform-api 日志 |
| 创建成功但 trigger 失败，`platform-api` 日志里是 `CERTIFICATE_VERIFY_FAILED` | `platform-api` 用 `JENKINS_BASE_URL=https://...` 访问了自签名 Jenkins，但 `JENKINS_INSECURE_TLS` 没打开 | `journalctl -u platform-api -f`，以及 `/opt/jenkins_robotframework/platform-api/.env` |
| Jenkins 一直排队 | 没有在线 Agent，或 label / executor 不匹配 | Jenkins Queue、Nodes 页面 |
| Jenkins checkout 失败 | repo URL 未配置，或 agent 本机 key path 不可读 / GitLab 不接受这把 key | Console Output、Jenkins node env、agent 本机私钥文件、GitLab SSH Keys / Deploy Keys |
| `create-venv` 安装 lock 文件时报 `No matching distribution found` | Jenkins 没配置内部 `PIP_INDEX_URL` / `PIP_EXTRA_INDEX_URL`，或配置仍指向外部公共源 | Jenkins 全局环境、job 参数 `PIP_*_OVERRIDE`、pip 日志里的 `Looking in indexes` |
| `No such DSL method 'sshagent'` | 某次运行显式走了旧 `credential_kind=sshagent` 分支，但 Jenkins 缺少 `SSH Agent` 插件 | 回到默认 agent-local key 模式；或安装 Jenkins `SSH Agent` 插件 |
| `fatal: could not read Username for 'https://...'` | 仍在使用需要鉴权的 HTTPS 仓库地址，但当前 checkout 逻辑没有注入 HTTPS 用户名密码 | 把 repo URL 改成 SSH 地址，或扩展 Pipeline 支持 HTTPS credentials |
| SSH clone 首次连接 GitLab 失败 | GitLab host key 未接受，或 known_hosts 校验失败 | 在 Agent 上先手工 `ssh -T git@wrgitlab.ext.net.nokia.com` 接受 host key；检查 Jenkins Git host key 策略 |
| SSH clone 权限被拒绝 | 私钥没有仓库读取权限，或公钥还没加到 GitLab 用户/Deploy Key | 在 Agent 上用同一把 key 执行 `git ls-remote` 验证两个仓库 |
| `source-checkout.json` 里 `repo_url: null` | Jenkins 全局环境未配置 `ROBOTWS_REPO_URL` / `TESTLINE_CONFIGURATION_REPO_URL` | Jenkins System -> Global properties |
| Missing activate script | `/home/ute/CIENV/<TESTLINE>/bin/activate` 不存在 | Agent 文件系统、`PYTHON_ENV_ROOT` |
| Robot case path not found | `ROBOTCASE_PATH` 不在 workspace 或 robotws 下 | Jenkins artifacts 中 `robot-request.json`、`robot-command.json` |
| Portal 页面创建后 run 一直不回写最终状态，`callback-send-result.json` 里是 `CERTIFICATE_VERIFY_FAILED` | Jenkins 回调 `https://.../api/runs/{run_id}/callbacks/jenkins` 时校验了自签名证书 | 保持 `CALLBACK_INSECURE_TLS=true`，或改用受信任证书 / 内部 CA |
| Portal 触发后 Jenkins 一开始就在 `materialize_run_request.py --run-id ... --platform-api-base-url https://...` 处报 `CERTIFICATE_VERIFY_FAILED` | Jenkins 在第一阶段通过 `https://.../api/runs/{run_id}` 拉 run 详情时校验了自签名证书 | 保持 `CALLBACK_INSECURE_TLS=true`，这样 Jenkins 会同时对 run-detail 拉取和 callback 回写都跳过 TLS 校验 |
| Portal 不更新最终状态 | Jenkins callback 到 `PLATFORM_API_BASE_URL` 失败 | Jenkins Console Output、`callback-fallback.json` |
