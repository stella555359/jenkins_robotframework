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

注意，这种情况很常见：

- 公钥看起来是 `ssh-rsa ...`
- 文件名也可能叫 `jenkins_agent_rsa`
- 但私钥文件头仍然是 `-----BEGIN OPENSSH PRIVATE KEY-----`

这时 Jenkins SSH launcher 仍然可能无法识别，需要继续做下面这一步转换。

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

当前更推荐把 launcher 私钥作为 controller 本机文件保存，再在 env 文件里只放路径。这样可以避免 `EnvironmentFile` 直接承载多行私钥导致的格式污染、截断或复制错误。

对于 `robotws` / `testline_configuration` checkout，当前改为使用 `t813-agent` 本机已有的 GitLab key，不再要求 controller 持有这把 checkout 私钥。

先准备 key 文件目录：

```bash
sudo install -d -m 0700 /etc/jenkins/keys
sudo install -o jenkins -g jenkins -m 0600 ~/.ssh/jenkins_agent_rsa /etc/jenkins/keys/jenkins_agent_rsa
```

这里不要只验证 root 自己能读。因为 `render_jcasc.py` 是在 Jenkins 启动链路里执行，私钥文件必须对 Jenkins 服务用户可读。

服务器上建议落到真实 env 文件，例如：

```bash
sudo tee /etc/default/jenkins-jcasc > /dev/null <<'EOF'
JENKINS_URL=https://10.71.210.104/jenkins/
JENKINS_ADMIN_EMAIL=admin@example.com

T813_AGENT_SSH_USER=jenkins
T813_AGENT_SSH_PRIVATE_KEY_PATH=/etc/jenkins/keys/jenkins_agent_rsa

ROBOTWS_CREDENTIALS_ID=robotws-ssh

TESTLINE_CONFIGURATION_CREDENTIALS_ID=testline-config-ssh
EOF
```

如果 `robotws` 和 `testline_configuration` 复用同一把 GitLab key，那么两个 Jenkins credential 使用同一把私钥也是正常的。

## 6. 这些值如何映射到 Jenkins credentials

当前默认 checkout 模式重新回到 Jenkins credentials。JCasC 负责提供默认的 credential ID，实际私钥仍可在 Jenkins UI 中维护：

| Jenkins credentials ID | 来源环境变量 | 用途 |
|---|---|---|
| `t813-agent-ssh` | `T813_AGENT_SSH_USER` + `T813_AGENT_SSH_PRIVATE_KEY_PATH` | Jenkins Controller 连接 `t813-agent` |
| `robotws-ssh` | `ROBOTWS_CREDENTIALS_ID` | checkout `robotws` |
| `testline-config-ssh` | `TESTLINE_CONFIGURATION_CREDENTIALS_ID` | checkout `testline_configuration` |

如果以后需要排查或临时回到 agent-local key 模式，仍可以对单次 run 显式指定 `credential_kind=agent-local-key`。

### 6.1 Script Console 打印旧 checkout credential 的公钥和指纹

仓库里已经提供了一份只打印公钥和指纹、不输出私钥正文的 Groovy：

- [jenkins-integration/scripts/print_ssh_credential_pubkeys.groovy](c:/TA/jenkins_robotframework/jenkins-integration/scripts/print_ssh_credential_pubkeys.groovy)

在 Jenkins UI 执行路径：

```text
Manage Jenkins -> Script Console
```

把脚本内容粘进去运行后，会打印：

1. `robotws-ssh` 的 username / public key / fingerprint
2. `testline-config-ssh` 的 username / public key / fingerprint

然后再和 agent 上当前文件的指纹做比对：

```bash
sudo -u jenkins ssh-keygen -lf /home/jenkins/.ssh/jenkins_gitlab_rsa
```

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

在默认 Jenkins credential 模式下，优先验证 Jenkins 里 `robotws-ssh` / `testline-config-ssh` 是否可用；如需和 agent 本机文件做比对，可在 `t813-agent` 上执行：

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

### 8.4 如果 Jenkins 报 `Illegal base64 character 2e`

典型报错类似：

```text
java.lang.IllegalArgumentException: Illegal base64 character 2e
```

这里的 `2e` 对应字符 `.`。

这说明 Jenkins 当前读到的 `T813_AGENT_SSH_PRIVATE_KEY` 内容里，PEM 正文混入了不属于 base64 的字符。最常见的是下面几种情况：

1. 把文档示例里的 `...这里粘贴 ...` 原样带进了真实 env 文件
2. 复制私钥时混入了额外说明文字、缩进、点号或其它可见字符
3. `-----BEGIN RSA PRIVATE KEY-----` 和 `-----END RSA PRIVATE KEY-----` 之间并不是完整原始私钥正文

先检查 Controller 上原始私钥文件头尾是否正确：

```bash
head -n 1 ~/.ssh/jenkins_agent_rsa
tail -n 1 ~/.ssh/jenkins_agent_rsa
```

输出应该是：

```text
-----BEGIN RSA PRIVATE KEY-----
-----END RSA PRIVATE KEY-----
```

再检查真实 env 文件里有没有明显污染内容：

```bash
grep -n "T813_AGENT_SSH_PRIVATE_KEY\|这里粘贴\|\.\.\." /etc/default/jenkins-jcasc
```

如果 grep 结果里还能看到 `这里粘贴` 或 `...`，说明当前 Jenkins 读到的不是实际私钥，而是示例占位内容。

修正后执行：

```bash
sudo systemctl restart jenkins
```

然后到 Jenkins 页面确认 `t813-agent-ssh` credential 已经刷新成最新值，再重新测试节点连接。

### 8.5 如果 job checkout 失败但 agent 已经 online

这通常说明 `t813-agent-ssh` 正常，但 agent 本机 GitLab key 路径不可读、路径写错，或者 key 本身不正确。

到 `t813-agent` 上检查：

```bash
test -r /home/jenkins/.ssh/jenkins_gitlab_rsa
ssh-keygen -y -f /home/jenkins/.ssh/jenkins_gitlab_rsa >/dev/null
GIT_SSH_COMMAND='ssh -i /home/jenkins/.ssh/jenkins_gitlab_rsa -o IdentitiesOnly=yes' git ls-remote git@wrgitlab.ext.net.nokia.com:RAN/robotws.git
GIT_SSH_COMMAND='ssh -i /home/jenkins/.ssh/jenkins_gitlab_rsa -o IdentitiesOnly=yes' git ls-remote git@wrgitlab.ext.net.nokia.com:RAN/configuration-management/testline_configuration.git
```

如果这里失败，先修 agent 本机 key 和权限，不要回头查 controller credential。

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