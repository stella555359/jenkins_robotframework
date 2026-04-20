# Git 相关问题汇总

## 问题 1：Git Push 提示 Repository Not Found

### 日期
2026-04-16

### 背景
本地已经在 `C:\TA\jenkins_robotframework` 完成了项目骨架初始化，开始第一次向 GitHub 推送代码。

### 问题
执行 `git push -u origin main` 后失败，报错如下：

```text
remote: Repository not found.
fatal: repository 'https://github.com/stella555359/jenkins_robotframework.git/' not found
```

### 原因
可能原因主要有以下几种：

1. GitHub 上还没有创建 `stella555359/jenkins_robotframework` 这个仓库。
2. 远程仓库名称或 owner 写错了。
3. 仓库存在但为私有仓库，当前 Git 客户端没有使用具备权限的账号认证。

当前已确认的实际情况是：

- GitHub 上这个仓库还没有创建。

### 解决方法
推荐处理步骤如下：

1. 浏览器打开 `https://github.com/stella555359/jenkins_robotframework` 并确认仓库是否存在。
2. 如果页面是 404，就在 `stella555359` 账号下创建一个同名空仓库：`jenkins_robotframework`。
3. 如果仓库已经存在但为私有仓库，则先确认当前 Windows Git 的认证账号是否具备访问权限。
4. 仓库创建完成后，再执行：

```bash
git remote -v
git push -u origin main
```

5. 如果仍然是认证问题，则需要通过 Git Credential Manager 或有效的 Personal Access Token 完成认证。

补充说明：

- 单靠 `git` 本身不能创建 GitHub 仓库。
- 可以通过 GitHub 网页创建。
- 也可以通过 GitHub CLI `gh repo create` 创建，但前提是本机安装了 `gh` 并完成登录。
- 也可以通过 GitHub REST API + PAT 创建，但对第一次建仓来说成本更高，不如网页方式直接。

### 后续注意
确认远程仓库创建完成后，继续重试第一次 push。

如果后续远程地址发生变化，还需要同步更新本地 `origin` 地址。

## 问题 2：服务器 Git Clone 无法直连 GitHub，需要通过代理

### 日期
2026-04-16

### 背景
在 Debian 服务器首次部署 `jenkins_robotframework` 时，需要从 GitHub 执行仓库克隆：

```bash
cd /opt
sudo git clone https://github.com/stella555359/jenkins_robotframework.git
```

### 问题
服务器执行 `git clone` 时无法直连 GitHub，连接失败，导致首次部署无法继续。

### 原因
当前服务器网络环境访问 GitHub 需要经过公司 HTTP 代理，不能直接对外建立连接。

公司代理地址为：

```text
http://10.144.1.10:8080
```

### 解决方法
不要直接把代理永久写入 Git 全局配置，优先使用一次性代理参数执行当前命令：

```bash
cd /opt
sudo git -c http.proxy=http://10.144.1.10:8080 -c https.proxy=http://10.144.1.10:8080 clone https://github.com/stella555359/jenkins_robotframework.git
sudo chown -R ute:ute /opt/jenkins_robotframework
```

这种写法只对当前这一次 `git clone` 生效。

如果后续同一台服务器上的 `git fetch`、`git pull` 也需要走代理，也应采用同样方式按命令附带 `-c http.proxy=... -c https.proxy=...`，而不是先默认改成长期全局代理，除非已经确认这台机器后续所有 GitHub 访问都必须长期经过该代理。

### 后续注意
后续实施文档中涉及服务器访问 GitHub 的步骤，应明确说明：

1. 默认先尝试直连。
2. 如果服务器网络受限，则使用公司代理的一次性 Git 参数。
3. 除非有长期统一运维要求，否则不要随意修改 `git config --global http.proxy`。

## 问题 3：服务器执行 git status 提示 dubious ownership

### 日期
2026-04-16

### 背景
在 Debian 服务器上首次克隆 `jenkins_robotframework` 后，以日常操作用户 `ute` 进入 `/opt/jenkins_robotframework` 执行 `git status`。

### 问题
Git 报错如下：

```text
fatal: detected dubious ownership in repository at '/opt/jenkins_robotframework'
To add an exception for this directory, call:

	git config --global --add safe.directory /opt/jenkins_robotframework
```

### 原因
仓库目录或 `.git` 目录的 ownership 与当前执行 Git 命令的用户不一致。常见触发场景是首次克隆时使用了 `sudo git clone`，但后续没有把整个仓库目录递归切回日常操作用户。

### 解决方法
优先修正 ownership，不要一上来就依赖 `safe.directory` 规避：

```bash
sudo chown -R ute:ute /opt/jenkins_robotframework
cd /opt/jenkins_robotframework
git status
```

只有在已经确认该目录必须保持为跨用户共享或特殊托管目录时，才额外执行：

```bash
git config --global --add safe.directory /opt/jenkins_robotframework
```

### 后续注意

1. 服务器上的仓库工作区应尽量由日常操作用户 `ute` 持有。
2. 首次使用 `sudo git clone` 后，应立即执行递归 `chown`。
3. `safe.directory` 更适合作为例外白名单，而不是日常默认方案。

## 问题 4：服务器标准发布时为什么写成 fetch + checkout + pull --ff-only

### 日期
2026-04-16

### 背景
在整理服务器发布文档时，标准同步命令写成了：

```bash
cd /opt/jenkins_robotframework
git fetch origin
git checkout main
git pull --ff-only origin main
```

随后出现一个典型疑问：如果服务器本来就一直在 `main` 分支，是否可以直接 `git pull`，以及 `fetch`、`--ff-only` 分别有什么作用。

### 问题
为什么不直接执行 `git pull`？`git fetch origin` 是做什么的？`--ff-only` 又限制了什么？

### 原因
这组命令并不是因为 Git 强制要求必须这样写，而是出于服务器发布的可控性和防误操作考虑：

1. `git fetch origin` 先只更新远端状态，不改本地工作区。
2. `git checkout main` 明确确保当前站在发布分支上。
3. `git pull --ff-only origin main` 只接受快进更新，不允许服务器上自动产生新的 merge commit。

如果直接裸执行 `git pull`，虽然在很多情况下也能成功，但前提是：

- 当前分支确实就是 `main`
- 上游跟踪关系配置正确
- 本地没有偏离远端的提交
- 不会触发自动 merge 或 rebase 带来的额外状态

### 解决方法
对于服务器这种部署场景，推荐保留显式写法：

```bash
cd /opt/jenkins_robotframework
git fetch origin
git checkout main
git pull --ff-only origin main
```

如果你已经明确确认以下条件都成立：

1. 当前就在 `main`
2. 工作区干净
3. 只是做一次临时手工同步

那么可以简化成：

```bash
git pull --ff-only origin main
```

### 后续注意

1. `git fetch` 只更新远端跟踪信息，不改当前工作区文件。
2. `git pull` 本质上等于先 `fetch`，再 merge 或 rebase。
3. `--ff-only` 用来阻止服务器上生成意外 merge commit，适合部署机使用。
4. 标准运维文档里仍建议使用显式的 `fetch + checkout + pull --ff-only`。
