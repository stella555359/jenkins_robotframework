# Jenkins SSH Key Setup

本文专门说明当前 `t813-agent` + `robotws` / `testline_configuration` 链路里涉及的 3 个 SSH private key：

1. `T813_AGENT_SSH_PRIVATE_KEY`
2. `ROBOTWS_GIT_SSH_PRIVATE_KEY`
3. `TESTLINE_CONFIGURATION_GIT_SSH_PRIVATE_KEY`

目标是把这 3 个值的用途、生成命令、对应公钥该放哪里、以及在 Jenkins JCasC 中如何配置说明清楚。

## 1. 三个 key 的用途

| 变量名 | 用途 | 谁使用它 | 公钥放到哪里 |
|---|---|---|---|
| `T813_AGENT_SSH_PRIVATE_KEY` | Jenkins Controller 通过 SSH 连接 `t813-agent` | Jenkins 节点 launcher | 放到 `10.57.159.149` 上 `jenkins` 用户的 `~/.ssh/authorized_keys` |
| `ROBOTWS_GIT_SSH_PRIVATE_KEY` | checkout `robotws` 仓库 | Jenkins Pipeline 的 `sshagent` / Git checkout | 放到 GitLab 有权限账号的 SSH Keys，或 `robotws` 仓库 Deploy Key |
| `TESTLINE_CONFIGURATION_GIT_SSH_PRIVATE_KEY` | checkout `testline_configuration` 仓库 | Jenkins Pipeline 的 `sshagent` / Git checkout | 放到 GitLab 有权限账号的 SSH Keys，或 `testline_configuration` 仓库 Deploy Key |

关键点：

- `T813_AGENT_SSH_PRIVATE_KEY` 是 **Controller -> Agent 登录** 用的 key。
- `ROBOTWS_GIT_SSH_PRIVATE_KEY` 和 `TESTLINE_CONFIGURATION_GIT_SSH_PRIVATE_KEY` 是 **Jenkins Job -> GitLab checkout** 用的 key。
- 后两者可以是 **同一把私钥**，只要对应公钥同时有权限访问两个仓库。
- 一般不建议把 `T813_AGENT_SSH_PRIVATE_KEY` 和 Git checkout 用的 key 复用成同一把。

## 2. 推荐的 key 关系

当前推荐做法：

1. `T813_AGENT_SSH_PRIVATE_KEY` 单独一把。
2. `ROBOTWS_GIT_SSH_PRIVATE_KEY` 和 `TESTLINE_CONFIGURATION_GIT_SSH_PRIVATE_KEY` 共用一把 GitLab key。

也就是说，实际通常只需要生成两套 key：

1. 一套 `jenkins -> t813-agent` 登录 key。
2. 一套 `Jenkins -> GitLab` checkout key。

## 3. 生成 `T813_AGENT_SSH_PRIVATE_KEY`

### 3.1 在 Jenkins Controller 上生成

建议在 Jenkins Controller 上，用 Jenkins 管理员登录用户生成。

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh

ssh-keygen -t rsa -b 4096 -m PEM -C "jenkins-master" -f ~/.ssh/jenkins_agent_rsa -N ""
```

这里 `-m PEM` 很重要。当前 Jenkins SSH launcher 走的是 `ssh-slaves` / `trilead` 这条解析链，
更稳妥的做法是让 `T813_AGENT_SSH_PRIVATE_KEY` 使用传统 PEM RSA 格式，也就是：

```text
-----BEGIN RSA PRIVATE KEY-----
...
-----END RSA PRIVATE KEY-----
```

不要把它写成：

```text
-----BEGIN OPENSSH PRIVATE KEY-----
...
-----END OPENSSH PRIVATE KEY-----
```

否则 Jenkins 节点 launcher 很容易报：

```text
PEM problem: it is of unknown type
```

生成后会得到：

1. 私钥：`~/.ssh/jenkins_agent_rsa`
2. 公钥：`~/.ssh/jenkins_agent_rsa.pub`

### 3.2 把公钥放到 `t813-agent`

把公钥加入 `10.57.159.149` 上 `jenkins` 用户：

```bash
ssh-copy-id -i ~/.ssh/jenkins_agent_rsa.pub jenkins@10.57.159.149
```

如果不能用 `ssh-copy-id`，也可以手工追加：

```bash
cat ~/.ssh/jenkins_agent_rsa.pub
```

然后把输出内容追加到 `10.57.159.149` 上：

```bash
sudo su - jenkins
mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo '这里粘贴上面的公钥' >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### 3.3 手工验证 Controller 到 Agent

```bash
ssh -i ~/.ssh/jenkins_agent_rsa jenkins@10.57.159.149 "echo 'SSH OK'"
```

如果返回 `SSH OK`，说明这套 key 可用。

如果你手里已经有一把现成的 RSA key，但格式是 `OPENSSH PRIVATE KEY`，可以在 Controller 上转成 PEM：

```bash
ssh-keygen -p -m PEM -f ~/.ssh/jenkins_agent_rsa -N "" -P ""
```

转换完成后，再确认文件头已经变成：

```bash
head -n 1 ~/.ssh/jenkins_agent_rsa
```

输出应该是：

```text
-----BEGIN RSA PRIVATE KEY-----
```

## 4. 生成 `ROBOTWS_GIT_SSH_PRIVATE_KEY` 和 `TESTLINE_CONFIGURATION_GIT_SSH_PRIVATE_KEY`

### 4.1 推荐方式：生成一把 GitLab checkout key 并复用

当前推荐在 `t813-agent` 上、切到实际 Jenkins 执行用户 `jenkins` 后生成。这样便于你在 Agent 机器上直接做 GitLab 连通性验证。

```bash
sudo su - jenkins
mkdir -p ~/.ssh
chmod 700 ~/.ssh

ssh-keygen -t ed25519 -C "jenkins-gitlab" -f ~/.ssh/jenkins_gitlab_rsa -N ""
```

生成后会得到：

1. 私钥：`~/.ssh/jenkins_gitlab_rsa`
2. 公钥：`~/.ssh/jenkins_gitlab_rsa.pub`

### 4.2 把公钥加到 GitLab

查看公钥：

```bash
cat ~/.ssh/jenkins_gitlab_rsa.pub
```

把这把公钥加到以下任一位置：

1. 一个对两个仓库都有读取权限的 GitLab 用户 `SSH Keys` 页面。
2. 或者分别加到两个仓库的 Deploy Key。

如果是共用一把 key 给两个仓库，最简单的是：

1. 把公钥加到有权限访问两个仓库的 GitLab 用户账号。
2. 用同一把私钥同时填到：
   - `ROBOTWS_GIT_SSH_PRIVATE_KEY`
   - `TESTLINE_CONFIGURATION_GIT_SSH_PRIVATE_KEY`

### 4.3 手工验证 GitLab SSH 登录

```bash
sudo su - jenkins
ssh -i ~/.ssh/jenkins_gitlab_rsa -T git@wrgitlab.ext.net.nokia.com
```

第一次通常会提示接受 host key，输入 `yes`。

如果看到类似：

- `Welcome ...`
- `authenticated`
- 或 `shell access is not supported`

都说明认证本身已经成功。

### 4.4 分别验证两个仓库是否可读

验证 `robotws`：

```bash
sudo su - jenkins
GIT_SSH_COMMAND='ssh -i ~/.ssh/jenkins_gitlab_rsa -o IdentitiesOnly=yes' \
git ls-remote git@wrgitlab.ext.net.nokia.com:RAN/robotws.git
```

验证 `testline_configuration`：

```bash
sudo su - jenkins
GIT_SSH_COMMAND='ssh -i ~/.ssh/jenkins_gitlab_rsa -o IdentitiesOnly=yes' \
git ls-remote git@wrgitlab.ext.net.nokia.com:RAN/configuration-management/testline_configuration.git
```

只要都能列出 refs，这把 key 就可以同时给两个仓库使用。

## 5. 如何填到 Jenkins JCasC 环境文件

当前 JCasC 真实引用来自：

- `T813_AGENT_SSH_USER`
- `T813_AGENT_SSH_PRIVATE_KEY`
- `ROBOTWS_GIT_SSH_USER`
- `ROBOTWS_GIT_SSH_PRIVATE_KEY`
- `TESTLINE_CONFIGURATION_GIT_SSH_USER`
- `TESTLINE_CONFIGURATION_GIT_SSH_PRIVATE_KEY`

参考文件：

- `deploy/env/jenkins-jcasc.env.example`

服务器上建议落到真实 env 文件，例如：

```bash
sudo tee /etc/default/jenkins-jcasc > /dev/null <<'EOF'
JENKINS_URL=https://10.71.210.104/jenkins/
JENKINS_ADMIN_EMAIL=admin@example.com

T813_AGENT_SSH_USER=jenkins
T813_AGENT_SSH_PRIVATE_KEY="-----BEGIN OPENSSH PRIVATE KEY-----
...这里粘贴 ~/.ssh/jenkins_agent_rsa 的完整内容...
-----END OPENSSH PRIVATE KEY-----"

ROBOTWS_GIT_SSH_USER=git
ROBOTWS_GIT_SSH_PRIVATE_KEY="-----BEGIN OPENSSH PRIVATE KEY-----
...这里粘贴 ~/.ssh/jenkins_gitlab_rsa 的完整内容...
-----END OPENSSH PRIVATE KEY-----"

TESTLINE_CONFIGURATION_GIT_SSH_USER=git
TESTLINE_CONFIGURATION_GIT_SSH_PRIVATE_KEY="-----BEGIN OPENSSH PRIVATE KEY-----
...如果共用，同样粘贴 ~/.ssh/jenkins_gitlab_rsa 的完整内容...
-----END OPENSSH PRIVATE KEY-----"
EOF
```

如果 `robotws` 和 `testline_configuration` 复用同一把 GitLab key，那么最后两段私钥内容完全相同是正常的。

## 6. 这些值如何映射到 Jenkins credentials

当前 JCasC 会创建 3 个 Jenkins credentials：

| Jenkins credentials ID | 来源环境变量 | 用途 |
|---|---|---|
| `t813-agent-ssh` | `T813_AGENT_SSH_USER` + `T813_AGENT_SSH_PRIVATE_KEY` | Jenkins Controller 连接 `t813-agent` |
| `robotws-ssh` | `ROBOTWS_GIT_SSH_USER` + `ROBOTWS_GIT_SSH_PRIVATE_KEY` | checkout `robotws` |
| `testline-config-ssh` | `TESTLINE_CONFIGURATION_GIT_SSH_USER` + `TESTLINE_CONFIGURATION_GIT_SSH_PRIVATE_KEY` | checkout `testline_configuration` |

## 7. JCasC reload 与生效

env 文件更新后，需要重启 Jenkins 或重新加载 JCasC：

```bash
sudo systemctl restart jenkins
```

或者在 Jenkins UI：

```text
Manage Jenkins -> Configuration as Code -> Reload existing configuration
```

## 8. 最短检查清单

### 8.1 检查 `t813-agent` SSH 登录 key

在 Controller 上：

```bash
ssh -i ~/.ssh/jenkins_agent_rsa jenkins@10.57.159.149 "hostname && whoami && java -version"
```

### 8.2 检查 GitLab checkout key

在 `t813-agent` 上：

```bash
sudo su - jenkins
ssh -i ~/.ssh/jenkins_gitlab_rsa -T git@wrgitlab.ext.net.nokia.com
GIT_SSH_COMMAND='ssh -i ~/.ssh/jenkins_gitlab_rsa -o IdentitiesOnly=yes' git ls-remote git@wrgitlab.ext.net.nokia.com:RAN/robotws.git
GIT_SSH_COMMAND='ssh -i ~/.ssh/jenkins_gitlab_rsa -o IdentitiesOnly=yes' git ls-remote git@wrgitlab.ext.net.nokia.com:RAN/configuration-management/testline_configuration.git
```

### 8.3 检查 Jenkins 中 credentials 是否出现

```text
Manage Jenkins -> Credentials -> System -> Global credentials
```

应该能看到：

1. `t813-agent-ssh`
2. `robotws-ssh`
3. `testline-config-ssh`

## 9. 最终推荐

推荐最终保留两套私钥：

1. `jenkins_agent_rsa`
   - 对应 `T813_AGENT_SSH_PRIVATE_KEY`
   - 只用于 Controller 登录 `t813-agent`
2. `jenkins_gitlab_rsa`
   - 对应 `ROBOTWS_GIT_SSH_PRIVATE_KEY`
   - 同时也可对应 `TESTLINE_CONFIGURATION_GIT_SSH_PRIVATE_KEY`
   - 只用于 Jenkins Job checkout GitLab 仓库

这样权限边界更清楚，也更方便后续轮换。