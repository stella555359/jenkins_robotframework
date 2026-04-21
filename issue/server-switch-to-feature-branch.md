# 本地新建 feature 分支后，服务器如何切到这个分支

## 1. 场景

常见场景是这样的：

- 你在本地仓库基于最新 `main` 新建了一个功能分支，例如：`feature/platform-api`
- 你已经在本地开始开发
- 服务器上的仓库是更早之前从 `main` clone 下来的
- 现在你想让服务器也切到这个新的功能分支

这时要先明确一点：

- 服务器看不到你“本地电脑里还没有推送出去的分支”
- 服务器只能看到远端仓库里已经存在的分支

所以正确顺序一定是：

1. 本地先把新分支 push 到远端
2. 服务器再 fetch 远端最新分支信息
3. 服务器再 checkout 到这个分支

## 2. 第一步：本地先把新分支推到远端

先在本地执行：

```powershell
cd C:\TA\jenkins_robotframework
git checkout feature/platform-api
git push -u origin feature/platform-api
```

这里的作用是：

- 把本地 `feature/platform-api` 推到远端
- 让远端仓库出现同名分支
- 顺手建立本地分支和远端分支的跟踪关系

如果这一步没做，服务器后面即使执行 `git fetch origin`，也看不到这个新分支。

## 3. 第二步：服务器刷新远端分支信息

在服务器上执行：

```bash
cd /opt/jenkins_robotframework
git fetch origin
```

如果服务器访问 GitHub 需要代理，则用：

```bash
cd /opt/jenkins_robotframework
git -c http.proxy=http://10.144.1.10:8080 -c https.proxy=http://10.144.1.10:8080 fetch origin
```

这一步的作用是：

- 更新服务器本地对远端仓库的认知
- 把新的 `origin/feature/platform-api` 拉到服务器这边的远端跟踪信息里
- 但不会自动切分支，也不会改工作区文件

## 4. 第三步：服务器切到这个新分支

如果服务器之前从来没有创建过这个本地分支，执行：

```bash
cd /opt/jenkins_robotframework
git checkout -b feature/platform-api origin/feature/platform-api
```

这句的作用是：

- 在服务器本地新建分支 `feature/platform-api`
- 让它从 `origin/feature/platform-api` 开始
- 同时切换到这个分支上

## 5. 如果服务器之前已经切过这个分支

如果服务器本地已经有这个分支了，后面再次同步就不需要 `-b` 重新创建，只要：

```bash
cd /opt/jenkins_robotframework
git checkout feature/platform-api
git pull --ff-only origin feature/platform-api
```

如果需要代理，就写成：

```bash
cd /opt/jenkins_robotframework
git checkout feature/platform-api
git -c http.proxy=http://10.144.1.10:8080 -c https.proxy=http://10.144.1.10:8080 pull --ff-only origin feature/platform-api
```

## 6. 怎么先确认服务器已经能看到这个远端分支

可以先执行：

```bash
cd /opt/jenkins_robotframework
git fetch origin
git branch -a
```

如果输出里已经出现：

```text
remotes/origin/feature/platform-api
```

就说明：

- 远端这个分支已经存在
- 服务器也已经拿到这个远端分支信息
- 接下来就可以 checkout 了

## 7. 最常用的一套命令

### 本地

```powershell
cd C:\TA\jenkins_robotframework
git checkout feature/platform-api
git push -u origin feature/platform-api
```

### 服务器

```bash
cd /opt/jenkins_robotframework
git fetch origin
git checkout -b feature/platform-api origin/feature/platform-api
```

## 8. 一句话记忆

- 本地新建分支，不等于服务器自动能看到
- 必须先 `push` 到远端
- 服务器再 `fetch`
- 然后 `checkout -b 本地分支 远端分支`