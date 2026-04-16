# Jenkins KPI Platform 实施指南
## 本地 IDE 开发 + GitHub 同步 + Debian 服务器部署

**文档版本**：v2.0  
**更新日期**：2026-04-16  
**适用环境**：Windows 本地开发机 + Debian 13 / Ubuntu 22.04+ 服务器  
**GitHub 仓库**：https://github.com/stella555359/jenkins_robotframework

**当前环境参数**：

- 本地 Windows 用户：`stlin`
- 本地仓库路径：`C:\TA\jenkins_robotframework`
- Master 服务器：`10.71.210.104`
- Agent 服务器：`10.57.159.149`
- Debian SSH 用户：`ute`

---

## 目录

- [实施原则](#实施原则)
- [总体架构](#总体架构)
- [第一步：前置准备](#第一步前置准备)
- [第二步：GitHub 仓库与本地开发模式](#第二步github-仓库与本地开发模式)
- [第三步：服务器基础环境准备](#第三步服务器基础环境准备)
- [第四步：Jenkins Master 部署](#第四步jenkins-master-部署)
- [第五步：三块代码的开发与部署方式](#第五步三块代码的开发与部署方式)
- [第六步：Jenkins Agent 配置](#第六步jenkins-agent-配置)
- [第七步：Pipeline 与代码同步流程](#第七步pipeline-与代码同步流程)
- [第八步：Nginx 与 HTTPS 配置](#第八步nginx-与-https-配置)
- [第九步：验证与日常运维](#第九步验证与日常运维)
- [故障排查](#故障排查)

---

## 实施原则

这份文档采用以下固定原则，后续所有步骤都以此为准：

1. **`jenkins-kpi-platform`、`kpi-portal`、`reporting-portal` 这三块代码不在 Debian 服务器上直接编写。**
2. **所有代码统一在本地 IDE 中开发、调试、提交。**
3. **唯一的版本管理与同步入口是 GitHub 仓库**：`https://github.com/stella555359/jenkins_robotframework`
4. **服务器只负责部署和运行**，即执行 `git pull`、安装依赖、迁移配置、重启服务。
5. **以后任何代码修改都通过 Git 提交记录版本**，而不是直接在服务器上手改文件。

这意味着：

- 本地电脑是开发环境
- GitHub 是代码真源（source of truth）
- Debian 服务器是运行环境

---

## 总体架构

推荐把三块代码统一维护在同一个 GitHub 仓库中，采用 monorepo 方式管理。

### 推荐目录结构

```text
jenkins_robotframework/
├── jenkins-kpi-platform/
│   ├── jcasc/
│   ├── jobs/
│   ├── pipelines/
│   ├── scripts/
│   └── README.md
├── kpi-portal/
│   ├── app/
│   ├── requirements.txt
│   └── README.md
├── reporting-portal/
│   ├── app/
│   ├── requirements.txt
│   └── README.md
├── deploy/
│   ├── systemd/
│   ├── nginx/
│   ├── env/
│   └── scripts/
└── docs/
```

### 三块代码的职责

- **jenkins-kpi-platform**：Jenkins 配置、JCasC、Pipeline、部署脚本、自动化编排逻辑
- **kpi-portal**：KPI 分析和报告生成入口服务
- **reporting-portal**：测试结果查询、汇总、展示 API 或页面服务

**补充说明**：

- 当前两个 FastAPI 服务的实际入口文件都是 `app/main.py`
- 也就是说，启动方式是 `uvicorn app.main:app`
- 当前仓库没有额外创建根目录 `main.py`，这是刻意简化后的结构，不影响运行
- 如果后续你想增加一个根目录 `main.py` 作为启动包装器，也可以再补，但不是必须项

### 推荐发布路径

服务器上统一克隆仓库到：

```bash
/opt/jenkins_robotframework
```

三个服务从该仓库的子目录运行：

- `/opt/jenkins_robotframework/jenkins-kpi-platform`
- `/opt/jenkins_robotframework/kpi-portal`
- `/opt/jenkins_robotframework/reporting-portal`

这样做的好处是：

- 代码版本统一
- 发布动作统一
- 回滚方便
- 不会出现服务器文件和 Git 仓库脱节

---

## 第一步：前置准备

### 1.1 资源清单

**硬件资源**：

- [ ] Master 服务器：10.71.210.104
- [ ] Agent 服务器：10.57.159.149
- [ ] 两台服务器网络互通

**账号与权限**：

- [ ] GitHub 账号可正常使用
- [ ] GitHub 仓库可访问：`https://github.com/stella555359/jenkins_robotframework`
- [ ] 服务器具备 sudo 权限
- [ ] GitLab 可读取 `robotws`、`testline_configuration` 等现有仓库

**本地开发环境**：

- [ ] Windows 本地已安装 Git
- [ ] 本地 IDE 可正常使用（VS Code / PyCharm 均可）
- [ ] 本地已安装 Python
- [ ] 本地可通过 SSH 连接 Debian 服务器

### 1.2 开发与部署边界

从现在开始，职责边界固定如下：

**本地 IDE 负责**：

- 新功能开发
- Bug 修复
- 单元测试
- 配置文件维护
- 提交 Git 版本

**GitHub 仓库负责**：

- 保存代码主线
- 管理历史版本
- 作为服务器同步源

**Debian 服务器负责**：

- 拉取最新代码
- 安装依赖
- 配置 systemd
- 启动/重启服务
- 供 Jenkins 和业务服务运行

---

## 第二步：GitHub 仓库与本地开发模式

这一章是整个方案的核心。以后 `jenkins-kpi-platform`、`kpi-portal`、`reporting-portal` 的任何改动都走这里。

### 2.1 本地克隆 GitHub 仓库

在本地 Windows 机器上执行：

```powershell
cd C:\TA
git clone https://github.com/stella555359/jenkins_robotframework.git
cd C:\TA\jenkins_robotframework
```

如果你已经像当前环境一样先在本地创建好了目录结构，但还没有初始化 Git 仓库，则按下面这组命令做第一次提交：

```powershell
cd C:\TA\jenkins_robotframework
git init
git branch -M main
git add .
git status
git commit -m "chore: initialize jenkins robotframework project scaffold"
git remote add origin https://github.com/stella555359/jenkins_robotframework.git
git push -u origin main
```

如果 `git remote add origin` 报错提示远程已存在，则改用：

```powershell
git remote set-url origin https://github.com/stella555359/jenkins_robotframework.git
git push -u origin main
```

如果远端仓库已经有初始化提交，第一次 push 被拒绝，则执行：

```powershell
git fetch origin
git pull origin main --allow-unrelated-histories
git push -u origin main
```

### 2.2 本地开发分支建议

推荐最少使用以下分支策略：

- `main`：稳定发布分支
- `dev`：日常集成分支
- `feature/*`：功能开发分支
- `fix/*`：缺陷修复分支

例如：

```powershell
git checkout -b feature/reporting-portal-api
```

### 2.3 代码修改的标准流程

以后修改任意一个模块，统一按这个顺序执行：

1. 在本地 IDE 修改代码
2. 在本地完成自测
3. 提交 Git
4. push 到 GitHub
5. 服务器执行 `git pull`
6. 重装依赖或执行部署脚本
7. 重启对应服务

### 2.4 标准 Git 命令流程

```powershell
cd C:\TA\jenkins_robotframework
git status
git add .
git commit -m "feat: update kpi portal workflow"
git push origin feature/reporting-portal-api
```

如果直接同步到主线：

```powershell
git checkout main
git pull origin main
git merge feature/reporting-portal-api
git push origin main
```

### 2.5 服务器同步代码的标准方式

服务器第一次部署：

```bash
cd /opt
sudo git clone https://github.com/stella555359/jenkins_robotframework.git
sudo chown -R $USER:$USER /opt/jenkins_robotframework
```

后续每次发布：

```bash
cd /opt/jenkins_robotframework
git fetch origin
git checkout main
git pull --ff-only origin main
```

**重点说明**：

- 服务器上不手工修改代码
- 如果服务器工作区有脏文件，先查明原因，不要直接覆盖
- 所有改动都应先回到本地仓库再提交

### 2.6 当前仓库骨架基线

当前仓库应至少包含以下三块模块骨架，第一次 push 前建议确认都已存在：

```text
jenkins-kpi-platform/
    jcasc/ jobs/ pipelines/ scripts/ vars/ resources/ templates/ docs/

kpi-portal/
    app/api/v1/ app/core/ app/models/ app/schemas/ app/services/ app/utils/
    tests/ data/uploads/ data/jobs/ data/reports/ logs/ scripts/ docs/

reporting-portal/
    app/api/v1/ app/core/ app/models/ app/schemas/ app/services/ app/utils/
    tests/ data/uploads/ data/results/ data/exports/ logs/ scripts/ docs/
```

空目录建议保留 `.gitkeep`，Python 包目录建议至少保留 `__init__.py`，这样第一次提交时 Git 能完整跟踪项目框架。

---

## 第三步：服务器基础环境准备

### 3.1 Master 服务器基础初始化

在 10.71.210.104 上执行：

```bash
sudo apt update
sudo apt upgrade -y
sudo apt autoremove -y

sudo apt install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    tree \
    unzip \
    net-tools \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    openjdk-21-jdk \
    nginx
```

### 3.2 创建统一部署目录

```bash
sudo mkdir -p /opt/jenkins_robotframework
sudo mkdir -p /var/lib/jenkins-kpi-platform/{logs,backups,data}
sudo chown -R $USER:$USER /opt/jenkins_robotframework
sudo chown -R $USER:$USER /var/lib/jenkins-kpi-platform
```

### 3.3 Agent 服务器基础配置

在 10.57.159.149 上执行：

```bash
sudo apt update
sudo apt upgrade -y

sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    openjdk-21-jre \
    git \
    openssh-server \
    curl \
    vim

sudo useradd -m -s /bin/bash jenkins || true
echo "jenkins ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/jenkins

sudo mkdir -p /automation/{workspace,venv,logs,downloads}
sudo chown -R jenkins:jenkins /automation
```

### 3.4 SSH 免密配置

Master 上生成密钥：

```bash
ssh-keygen -t rsa -b 4096 -C "jenkins-master" -f ~/.ssh/jenkins_agent_rsa -N ""
```

将公钥加入 Agent 的 `authorized_keys` 后验证：

```bash
ssh -i ~/.ssh/jenkins_agent_rsa jenkins@10.57.159.149 "echo 'SSH OK'"
```

---

## 第四步：Jenkins Master 部署

### 4.1 安装 Jenkins

```bash
sudo wget -O /usr/share/keyrings/jenkins-keyring.asc \
  https://pkg.jenkins.io/debian-stable/jenkins.io.key

echo "deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/" | \
  sudo tee /etc/apt/sources.list.d/jenkins.list > /dev/null

sudo apt update
sudo apt install -y jenkins
```

### 4.2 启动 Jenkins

```bash
sudo systemctl enable jenkins
sudo systemctl start jenkins
sudo systemctl status jenkins
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

### 4.3 初始化 Jenkins Web

建议通过 SSH 隧道访问，不直接暴露 8080：

```powershell
ssh -L 8080:localhost:8080 ute@10.71.210.104
```

然后本地浏览器访问：

```text
http://localhost:8080
```

### 4.4 配置 Jenkins 子路径和外部访问地址

因为后续会通过 Nginx 以 `/jenkins/` 路径反向代理，所以要先把 Jenkins 自身配置为带前缀运行，避免静态资源和跳转链接错误。

在 Master 服务器执行：

```bash
sudo systemctl edit jenkins
```

写入以下内容：

```ini
[Service]
Environment="JENKINS_PREFIX=/jenkins"
```

保存后执行：

```bash
sudo systemctl daemon-reload
sudo systemctl restart jenkins
sudo systemctl status jenkins
```

然后在 Jenkins Web 中设置：

- `Manage Jenkins` -> `System`
- `Jenkins URL` 改为 `https://10.71.210.104/jenkins/`

如果后面申请到了正式域名，则改为：

- `https://jenkins.company.com/jenkins/`

### 4.5 Jenkins 必装插件

- Pipeline
- Git
- Credentials Binding
- SSH Build Agents
- Configuration as Code
- Timestamper
- AnsiColor
- HTML Publisher
- JUnit

### 4.6 Jenkins 的定位

Jenkins 在这个方案中的职责不是“让你在服务器写代码”，而是：

- 从 GitHub 拉取代码
- 执行部署脚本
- 同步 `robotws` / `testline_configuration` 等依赖仓库
- 触发测试和报告生成流程

---

## 第五步：三块代码的开发与部署方式

这一章是本次修订的重点。

### 5.1 总原则

对于 `jenkins-kpi-platform`、`kpi-portal`、`reporting-portal`：

- **代码编写地点**：本地 IDE
- **版本管理地点**：GitHub 仓库 `jenkins_robotframework`
- **服务器动作**：只做 `git pull`、安装依赖、重启服务

**不允许的方式**：

- 直接 SSH 到 Debian 服务器后用 `vim` 或 `nano` 长期维护业务代码
- 服务器和 GitHub 分别维护两套不同版本
- 在服务器改了代码却不提交 Git

---

### 5.2 jenkins-kpi-platform 的开发与部署

`jenkins-kpi-platform` 建议放置 Jenkins 相关的配置和自动化资产，例如：

- `JCasC` 配置
- `Jenkinsfile`
- Job DSL
- 部署脚本
- 与 `robotws`、`testline_configuration` 集成的调度逻辑

#### 本地开发流程

```powershell
cd C:\TA\jenkins_robotframework
git checkout -b feature/jenkins-kpi-platform-update
```

在本地 IDE 修改：

- `jenkins-kpi-platform/jcasc/`
- `jenkins-kpi-platform/pipelines/`
- `jenkins-kpi-platform/scripts/`

提交并推送：

```powershell
git add .
git commit -m "feat: update jenkins kpi platform config"
git push origin feature/jenkins-kpi-platform-update
```

合并到 `main` 后，服务器同步：

```bash
cd /opt/jenkins_robotframework
git fetch origin
git checkout main
git pull --ff-only origin main
```

如果包含 Jenkins 配置更新，可执行：

```bash
sudo systemctl restart jenkins
```

但这类重启只建议在以下场景执行：

- 手工发布窗口
- 修改了 JCasC、插件、Jenkins Prefix 等 Jenkins 自身配置

如果是 Jenkins 自己触发的自动部署任务，不要在同一条流水线里重启 Jenkins 本体。

#### 推荐做法

- Jenkins 的配置尽量代码化，存放在仓库中
- 部署脚本也放在仓库中，不要散落在服务器各目录
- 所有 Jenkins 变更都有 commit 历史

#### 建议的初始文件骨架

第一次建仓时，`jenkins-kpi-platform` 建议至少包含：

```text
jenkins-kpi-platform/
├── jcasc/jenkins.yaml
├── jobs/README.md
├── pipelines/deploy_portals.groovy
├── scripts/deploy_jenkins_config.sh
├── vars/.gitkeep
├── resources/.gitkeep
├── templates/.gitkeep
└── docs/.gitkeep
```

---

### 5.3 reporting-portal 的开发与部署

`reporting-portal` 是业务应用代码，开发流程应完全在本地完成。

#### 本地开发

```powershell
cd C:\TA\jenkins_robotframework
git checkout -b feature/reporting-portal
cd reporting-portal
```

在本地 IDE 中：

- 编写 FastAPI 代码
- 修改 `requirements.txt`
- 编写或更新测试
- 本地运行验证接口

建议先从以下骨架开始：

```text
reporting-portal/
├── app/main.py
├── app/core/config.py
├── app/api/v1/router.py
├── app/services/health_service.py
├── app/schemas/health.py
├── tests/test_health.py
├── .env.example
└── requirements.txt
```

完成后提交：

```powershell
cd C:\TA\jenkins_robotframework
git add .
git commit -m "feat: update reporting portal"
git push origin feature/reporting-portal
```

#### 服务器部署

服务器不再手工创建每个源码文件，而是直接同步仓库代码：

```bash
cd /opt/jenkins_robotframework
git fetch origin
git checkout main
git pull --ff-only origin main
```

为 `reporting-portal` 单独创建虚拟环境：

```bash
cd /opt/jenkins_robotframework/reporting-portal
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
```

创建 systemd 服务：

```bash
sudo tee /etc/systemd/system/reporting-portal.service > /dev/null << 'EOF'
[Unit]
Description=Reporting Portal Service
After=network.target

[Service]
Type=simple
User=ute
WorkingDirectory=/opt/jenkins_robotframework/reporting-portal
Environment="PATH=/opt/jenkins_robotframework/reporting-portal/venv/bin"
ExecStart=/opt/jenkins_robotframework/reporting-portal/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable reporting-portal
sudo systemctl restart reporting-portal
sudo systemctl status reporting-portal
```

发布新版本时通常只需要：

```bash
cd /opt/jenkins_robotframework
git pull --ff-only origin main
cd reporting-portal
source venv/bin/activate
pip install -r requirements.txt
deactivate
sudo systemctl restart reporting-portal
```

---

### 5.4 kpi-portal 的开发与部署

`kpi-portal` 同样采用本地开发、GitHub 管理、服务器拉取的模式。

#### 本地开发

```powershell
cd C:\TA\jenkins_robotframework
git checkout -b feature/kpi-portal
cd kpi-portal
```

本地完成以下工作：

- API 代码开发
- 与 `kpi-anomaly-detector`、`kpi-generator` 的集成代码编写
- 参数校验、任务管理、接口测试
- 依赖文件维护

建议先从以下骨架开始：

```text
kpi-portal/
├── app/main.py
├── app/core/config.py
├── app/api/v1/router.py
├── app/services/health_service.py
├── app/schemas/health.py
├── tests/test_health.py
├── .env.example
└── requirements.txt
```

提交并推送：

```powershell
cd C:\TA\jenkins_robotframework
git add .
git commit -m "feat: update kpi portal"
git push origin feature/kpi-portal
```

#### 服务器部署

```bash
cd /opt/jenkins_robotframework
git fetch origin
git checkout main
git pull --ff-only origin main
```

安装依赖：

```bash
cd /opt/jenkins_robotframework/kpi-portal
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
```

创建 systemd 服务：

```bash
sudo tee /etc/systemd/system/kpi-portal.service > /dev/null << 'EOF'
[Unit]
Description=KPI Portal Service
After=network.target

[Service]
Type=simple
User=ute
WorkingDirectory=/opt/jenkins_robotframework/kpi-portal
Environment="PATH=/opt/jenkins_robotframework/kpi-portal/venv/bin"
ExecStart=/opt/jenkins_robotframework/kpi-portal/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable kpi-portal
sudo systemctl restart kpi-portal
sudo systemctl status kpi-portal
```

后续版本发布：

```bash
cd /opt/jenkins_robotframework
git pull --ff-only origin main
cd kpi-portal
source venv/bin/activate
pip install -r requirements.txt
deactivate
sudo systemctl restart kpi-portal
```

---

### 5.5 三块代码的统一发布原则

推荐把发布动作固化成脚本，例如：

```bash
#!/usr/bin/env bash
set -e

cd /opt/jenkins_robotframework
git fetch origin
git checkout main
git pull --ff-only origin main

cd /opt/jenkins_robotframework/reporting-portal
source venv/bin/activate
pip install -r requirements.txt
deactivate

cd /opt/jenkins_robotframework/kpi-portal
source venv/bin/activate
pip install -r requirements.txt
deactivate

sudo systemctl restart reporting-portal
sudo systemctl restart kpi-portal
```

这个脚本也应纳入 GitHub 仓库管理，例如放在：

```text
deploy/scripts/deploy_all.sh
```

这样以后任何部署逻辑变更也有版本记录。

**重要说明**：

- `deploy_all.sh` 默认只重启 `reporting-portal` 和 `kpi-portal`
- 不要在 Jenkins 触发自己的部署任务时顺便重启 Jenkins
- 如果确实需要更新 Jenkins 自身配置，建议单独准备 `deploy_jenkins_config.sh`，并在维护窗口手工执行

---

## 第六步：Jenkins Agent 配置

### 6.1 Agent 节点用途

Agent 节点主要负责：

- 拉取测试相关仓库
- 执行 `robotws` 自动化任务
- 调用测试线资源
- 生成测试结果
- 将结果推送给 `reporting-portal` 或 `kpi-portal`

### 6.2 在 Jenkins 中添加 Agent

在 Jenkins Web 中：

1. Manage Jenkins
2. Nodes
3. New Node
4. 选择 Permanent Agent

建议配置：

- Name: `t813-agent`
- Remote root directory: `/automation/workspace`
- Labels: `t813 robot`
- Launch method: `Launch agents via SSH`
- Host: `10.57.159.149`
- Credentials: Jenkins 中配置的 SSH 凭据

### 6.3 Agent 侧代码同步原则

Agent 上运行的测试仓库，例如 `robotws`、`testline_configuration`，仍然可以由 Jenkins Job 在构建时拉取。

但 `jenkins-kpi-platform`、`kpi-portal`、`reporting-portal` 的业务代码主线仍以 GitHub 仓库为准，不在 Agent 上手工维护。

---

## 第七步：Pipeline 与代码同步流程

### 7.1 推荐的发布链路

以后建议采用下面这条标准链路：

1. 本地 IDE 修改代码
2. push 到 GitHub `jenkins_robotframework`
3. Jenkins 监听 GitHub 变更或手工触发
4. Jenkins 在 Master 上执行部署脚本
5. 服务器 `git pull` 最新代码
6. 重装依赖
7. 重启服务
8. 执行健康检查

### 7.2 最小可用部署 Pipeline

```groovy
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/stella555359/jenkins_robotframework.git'
            }
        }

        stage('Deploy To Master') {
            steps {
                sh '''
                ssh ute@10.71.210.104 '
                    set -e
                    cd /opt/jenkins_robotframework
                    git fetch origin
                    git checkout main
                    git pull --ff-only origin main

                    cd /opt/jenkins_robotframework/reporting-portal
                    . venv/bin/activate
                    pip install -r requirements.txt
                    deactivate

                    cd /opt/jenkins_robotframework/kpi-portal
                    . venv/bin/activate
                    pip install -r requirements.txt
                    deactivate

                    sudo systemctl restart reporting-portal
                    sudo systemctl restart kpi-portal
                '
                '''
            }
        }

        stage('Health Check') {
            steps {
                sh '''
                ssh ute@10.71.210.104 '
                    curl --noproxy localhost http://localhost:8000/health
                    curl --noproxy localhost http://localhost:8001/health
                '
                '''
            }
        }
    }
}
```

### 7.3 手工发布与自动发布的关系

初期可以先手工发布：

- 本地 push 到 GitHub
- 手工 SSH 到服务器执行 `git pull`

稳定后再切到 Jenkins 自动发布。

这两种方式的代码源都必须保持一致，都是 GitHub 仓库。

---

## 第八步：Nginx 与 HTTPS 配置

建议由 Nginx 统一反向代理：

- Jenkins -> 8080
- Reporting Portal -> 8000
- KPI Portal -> 8001

### 8.1 证书准备

如果你当前还没有正式域名，不能直接用 Let's Encrypt 给 IP 地址签发证书。此时建议先用以下两种方式之一：

- 公司内部 CA 证书
- 临时自签名证书（仅内网测试）

先生成一份可测试的自签名证书：

```bash
sudo openssl req -x509 -nodes -days 365 -newkey rsa:4096 \
  -keyout /etc/ssl/private/jenkins-kpi-platform.key \
  -out /etc/ssl/certs/jenkins-kpi-platform.crt \
  -subj "/CN=10.71.210.104"
```

如果后续拿到了正式域名，再切换到公司签发证书或 Let's Encrypt。

### 8.2 示例 Nginx 配置
```nginx
server {
    listen 80;
    server_name 10.71.210.104;

    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name 10.71.210.104;

    ssl_certificate /etc/ssl/certs/jenkins-kpi-platform.crt;
    ssl_certificate_key /etc/ssl/private/jenkins-kpi-platform.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    location /jenkins/ {
        proxy_pass http://127.0.0.1:8080/jenkins/;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
    }

    location /reports/ {
        proxy_pass http://127.0.0.1:8000/;
    }

    location /kpi/ {
        proxy_pass http://127.0.0.1:8001/;
    }
}
```

启用配置：

```bash
sudo cp /opt/jenkins_robotframework/deploy/nginx/jenkins-kpi-platform.conf /etc/nginx/sites-available/jenkins-kpi-platform.conf
sudo ln -sf /etc/nginx/sites-available/jenkins-kpi-platform.conf /etc/nginx/sites-enabled/jenkins-kpi-platform.conf
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

---

验证：

```bash
curl -k -I https://10.71.210.104/jenkins/
curl -k -I https://10.71.210.104/reports/health
curl -k -I https://10.71.210.104/kpi/health
```

## 第九步：验证与日常运维

### 9.1 每次发布后的检查项

- [ ] GitHub 上目标分支代码已更新
- [ ] 服务器 `git pull` 成功
- [ ] `reporting-portal` 依赖安装成功
- [ ] `kpi-portal` 依赖安装成功
- [ ] Jenkins / KPI Portal / Reporting Portal 服务状态正常
- [ ] `/health` 接口正常

### 9.2 常用检查命令

```bash
cd /opt/jenkins_robotframework
git log -1 --oneline
git status

sudo systemctl status jenkins
sudo systemctl status reporting-portal
sudo systemctl status kpi-portal

curl --noproxy localhost http://localhost:8000/health
curl --noproxy localhost http://localhost:8001/health
```

### 9.3 回滚方式

如果新版本有问题，不要在服务器直接改代码，应该回滚 Git 版本。

**推荐回滚方式**：在本地仓库生成回滚提交，再同步到服务器。

例如在本地执行：

```powershell
cd C:\TA\jenkins_robotframework
git log --oneline
git revert <problem_commit>
git push origin main
```

然后在服务器执行：

```bash
cd /opt/jenkins_robotframework
git fetch origin
git checkout main
git pull --ff-only origin main
sudo systemctl restart reporting-portal
sudo systemctl restart kpi-portal
```

**推荐发布标签**：

每次稳定发布后，在本地打标签：

```powershell
git tag -a release-2026-04-16 -m "stable release"
git push origin release-2026-04-16
```

**紧急临时回退**：

如果线上必须临时验证旧版本，可在服务器上临时切换到某个 tag 或 commit，但这不应作为标准长期流程，因为下次 `git pull` 会再次回到主线。

更规范的方式仍然是：

1. 在本地仓库回退或创建修复提交
2. push 到 GitHub
3. 服务器重新同步

---

## 故障排查

### 问题 1：服务器上的代码和 GitHub 不一致

**原因**：有人直接在服务器修改了代码。  
**处理**：

1. 先备份服务器当前改动
2. 对比与 GitHub 的差异
3. 把有效改动回收到本地仓库
4. 重新提交 Git
5. 服务器恢复为仓库同步模式

### 问题 2：`git pull` 失败，提示本地有修改

**原因**：服务器工作区被手工改脏了。  
**处理原则**：

- 不要直接粗暴覆盖
- 先 `git status`
- 先确认这些变更是否应该进入 GitHub

### 问题 3：服务重启失败

检查：

```bash
sudo journalctl -u reporting-portal -n 100
sudo journalctl -u kpi-portal -n 100
sudo journalctl -u jenkins -n 100
```

### 问题 4：依赖安装后仍然报模块缺失

通常是以下原因之一：

- 没有进入对应虚拟环境
- `requirements.txt` 未提交到 GitHub
- 服务器 `git pull` 后没有重新执行 `pip install -r requirements.txt`

### 问题 5：发布后访问到的仍是旧页面

检查顺序：

1. 服务器代码是否已经 `git pull` 到最新 commit
2. 服务是否已重启
3. Nginx 是否需要 reload
4. 浏览器是否缓存旧页面

---

## 最终结论

从本版本文档开始，`jenkins-kpi-platform`、`kpi-portal`、`reporting-portal` 的标准工作方式明确如下：

- **代码在本地 IDE 中开发**
- **代码统一 push 到 GitHub 仓库**：`https://github.com/stella555359/jenkins_robotframework`
- **服务器通过 GitHub 拉取代码实现同步**
- **版本控制、发布、回滚都以 Git 为准**

也就是说，Debian 服务器以后是部署目标机，不是日常写代码的地方。

这套方式更适合后续长期维护，因为它同时解决了：

- 版本可追踪
- 多次修改可回滚
- 本地开发效率高
- 服务器环境干净
- Jenkins 自动化发布可持续扩展