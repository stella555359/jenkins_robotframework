# Nginx 反向代理通俗解释

## 日期
2026-04-16

## 背景

在推进 Jenkins 外部 HTTPS 访问配置时，文档中已经写到了 Nginx 反向代理，但如果第一次接触这个概念，容易只会照着配，却不知道它到底在整个链路里扮演什么角色。

## 问题

什么是 Nginx 反向代理？为什么当前项目里 Jenkins 不直接对外暴露 `8080`，而是建议通过 Nginx 提供 `https://10.71.210.104/jenkins/` 这样的访问入口？

## 通俗解释

可以把 Nginx 理解成“前台接待”，把 Jenkins、reporting-portal、kpi-portal 理解成“后面的实际办事窗口”。

用户不会直接去敲后面的每个真实服务，而是统一先访问 Nginx 暴露出来的入口；然后由 Nginx 根据访问路径，把请求转发给真正处理请求的后端程序。

在当前项目里，可以这样理解：

1. 你在 Windows 浏览器里访问的是：`https://10.71.210.104/jenkins/`
2. 这个地址先到 Nginx
3. Nginx 再把请求转给 Jenkins 实际监听的地址：`http://127.0.0.1:8080/jenkins/`
4. Jenkins 返回页面
5. Nginx 再把页面返回给浏览器

所以外部看到的是 Nginx，真正干活的是后面的 Jenkins。

## 为什么叫“反向代理”

你可以先简单记成：

- 正常直连：客户端自己直接访问后端服务
- 反向代理：客户端先访问代理服务器，再由代理服务器替客户端去找真正的后端服务

也就是说，不是浏览器自己直接找 Jenkins，而是先找 Nginx，再由 Nginx 把请求“反过来”转发给 Jenkins。

## 放到当前项目里有什么好处

### 1. 统一入口

外部不需要记 `8080`、`8000`、`8001` 这些端口，只需要记一个统一入口。

例如：

- `/jenkins/` -> Jenkins
- `/reports/` -> reporting-portal
- `/kpi/` -> kpi-portal

### 2. 统一 HTTPS

证书只需要先配置在 Nginx 这一层，后面的 Jenkins 和 FastAPI 服务仍然可以继续监听本机 HTTP 端口。

这样做的好处是：

- HTTPS 配置集中
- 证书更容易统一管理
- 后端服务本身不用分别重复处理外部 TLS 入口

### 3. 更安全

Jenkins 不一定要直接暴露给外网，只需要让 Nginx 暴露出去即可。

后端服务可以继续只监听本机地址，例如：

- Jenkins: `127.0.0.1:8080`
- reporting-portal: `127.0.0.1:8000`
- kpi-portal: `127.0.0.1:8001`

这样外部用户不能直接绕过 Nginx 去访问这些内部服务端口。

### 4. 访问结构更稳定

当前文档把 Jenkins 的外部地址设计成：

`https://10.71.210.104/jenkins/`

后面如果再挂上 reporting-portal 和 kpi-portal，也还是同一套路：

- `https://10.71.210.104/reports/`
- `https://10.71.210.104/kpi/`

这比把不同服务分别暴露在不同端口上更容易维护，也更适合后续扩展。

## 一个生活化比喻

- Nginx 是前台服务员
- Jenkins 是后厨
- 用户不会自己冲进后厨点菜
- 用户先告诉前台“我要 `/jenkins/`”
- 前台再把请求送到 Jenkins

所以 Nginx 反向代理的核心作用，就是统一对外接待，再把请求分发给真正干活的后端服务。

## 对当前项目最重要的理解

当前项目里，Nginx 反向代理不是“可有可无的附加项”，而是后续整个访问入口设计的基础层。它解决的是：

1. Jenkins 为什么不直接长期暴露 `8080`
2. 为什么 Jenkins 要先配 `JENKINS_PREFIX=/jenkins`
3. 为什么 Windows 最终访问的是 `https://10.71.210.104/jenkins/`
4. 为什么后面 reporting-portal 和 kpi-portal 也可以继续复用同一套 Nginx 入口

## 结论

一句话记忆：

Nginx 反向代理就是“由 Nginx 统一接收外部请求，再把请求转发给后面的 Jenkins 或其他服务”，这样可以统一入口、统一 HTTPS、减少端口暴露，并让整个项目后续扩展更顺。

## 补充问题：如果 Windows 不通 8001，但能通 443，还能不能通过 Nginx 访问后端服务

### 结论

可以，不妨碍。

只要满足下面两个条件，就仍然可以通过 Nginx 访问后面的 `8001` 服务：

1. Windows 到服务器的 `443` 是通的
2. 服务器本机上的 Nginx 能访问到后端的 `127.0.0.1:8001`

外部浏览器并不是直接访问 `8001`，而是访问 Nginx 的 `443`，再由 Nginx 在服务器内部把请求转给真正监听 `8001` 的后端程序。

## 最简链路图

### 单看 KPI 这一条链路

```text
Windows 浏览器
	|
	| HTTPS 443
	v
Nginx
	|
	| HTTP 127.0.0.1:8001
	v
kpi-portal
```

### 三条路径放在一起看

```text
Windows 浏览器
	|
	| HTTPS 443
	v
Nginx
	|
	|-- /jenkins/  ->  http://127.0.0.1:8080/jenkins/   -> Jenkins
	|-- /reports/  ->  http://127.0.0.1:8000/           -> reporting-portal
	`-- /kpi/      ->  http://127.0.0.1:8001/           -> kpi-portal
```

## 应该怎么理解

这里要把两段网络路径分开看：

1. 外部访问路径：Windows -> 服务器 `443`
2. 服务器内部转发路径：Nginx -> `127.0.0.1:8080/8000/8001`

所以：

- Windows 不需要直接打通 `8000`、`8001`、`8080`
- 外部只需要能访问 `443`
- 后端端口只需要服务器本机上的 Nginx 能访问到即可

## 为什么这反而是更合理的设计

这通常不是缺点，而是更标准、更安全的部署方式：

1. 外部只暴露一个统一入口 `443`
2. 后端端口不直接暴露给外部
3. HTTPS、证书、访问路径统一由 Nginx 管理
4. 后续新增服务时，只要继续挂路径，不需要额外暴露新端口

## 什么情况下会失败

真正会出问题的不是“Windows 不通 8001”，而是下面这些情况：

1. Windows 到服务器的 `443` 不通
2. Nginx 没有正确把 `/kpi/` 代理到 `127.0.0.1:8001`
3. `kpi-portal` 服务没有启动，或者没有正确监听
4. 服务器本机自己都访问不到 `127.0.0.1:8001`

## 最实用的检查顺序

### 1. 先在服务器上检查后端服务是否正常

```bash
curl http://127.0.0.1:8001/health
```

### 2. 再在服务器上检查 Nginx 转发是否正常

```bash
curl -k https://127.0.0.1/kpi/health
```

### 3. 最后在 Windows 上检查外部入口

```text
https://10.71.210.104/kpi/health
```

## 一句话总结这个补充问题

外部不需要直通 `8001`；只要外部能到 `443`，并且 Nginx 在服务器内部能转发到 `8001`，就可以通过 Nginx 正常访问后端服务。

## 补充问题：`/etc/nginx/sites-available` 不存在时怎么办

### 现象

在服务器执行：

```bash
sudo cp /opt/jenkins_robotframework/deploy/nginx/jenkins-kpi-platform.conf /etc/nginx/sites-available/jenkins-kpi-platform.conf
```

报错：

```text
cp: cannot create regular file '/etc/nginx/sites-available/jenkins-kpi-platform.conf': No such file or directory
```

### 这说明什么

这通常不是 `cp` 命令写错了，也不是 `jenkins-kpi-platform.conf` 文件内容有问题，而是说明这台服务器上的 Nginx 目录布局和常见 Debian 默认布局不一致。

也就是说，至少当前不存在这个目录：

`/etc/nginx/sites-available`

### 正确的第一步

先不要急着反复重试 `cp`，先看服务器上 Nginx 实际采用的目录结构：

```bash
sudo nginx -v
sudo systemctl status nginx
sudo ls -l /etc/nginx
```

必要时继续看：

```bash
sudo cat /etc/nginx/nginx.conf
```

重点是看 `nginx.conf` 里到底 `include` 了什么：

- 是 `sites-enabled/*`
- 还是 `conf.d/*.conf`

### 常见两种处理方式

#### 方式 1：目录只是没建，但仍准备按 Debian 结构使用

如果你确认这台机器就是标准 Debian 风格，只是目录没建齐，可以手工补目录：

```bash
sudo mkdir -p /etc/nginx/sites-available
sudo mkdir -p /etc/nginx/sites-enabled
```

然后继续：

```bash
sudo cp /opt/jenkins_robotframework/deploy/nginx/jenkins-kpi-platform.conf /etc/nginx/sites-available/jenkins-kpi-platform.conf
sudo ln -sf /etc/nginx/sites-available/jenkins-kpi-platform.conf /etc/nginx/sites-enabled/jenkins-kpi-platform.conf
sudo nginx -t
sudo systemctl restart nginx
```

#### 方式 2：这台机器实际走 `conf.d`

如果 `nginx.conf` 里加载的是 `/etc/nginx/conf.d/*.conf`，那就不应该硬套 `sites-available` 这套路径，而应该直接把配置文件放到：

```text
/etc/nginx/conf.d/jenkins-kpi-platform.conf
```

对应命令：

```bash
sudo cp /opt/jenkins_robotframework/deploy/nginx/jenkins-kpi-platform.conf /etc/nginx/conf.d/jenkins-kpi-platform.conf
sudo nginx -t
sudo systemctl restart nginx
```

### 一句话判断

不是所有机器都有 `sites-available`；先看 Nginx 实际加载哪个目录，再决定配置文件该落到哪里。

## 补充问题：`sudo ls -l /etc/nginx` 结果是 `total 0`

### 现象

执行：

```bash
sudo ls -l /etc/nginx
```

输出：

```text
total 0
```

### 这说明什么

这已经不是“缺一个 `sites-available` 目录”的问题了，而是整个 Nginx 配置目录基本是空的。

通常意味着下面几种情况之一：

- Nginx 没有正常安装完成
- Nginx 默认配置文件被删掉或清空了
- 当前系统里的 `nginx` 服务处于异常或半安装状态

### 为什么这时不能只补 `sites-available`

因为正常可用的 Nginx 至少还应当有主配置文件：

```text
/etc/nginx/nginx.conf
```

如果整个 `/etc/nginx` 都是空的，那说明连“主入口”都没有，这时就不应该直接跳到“复制业务代理配置文件”这一步。

### 正确处理顺序

先验证 Nginx 是否真的装好了：

```bash
sudo nginx -v
sudo systemctl status nginx
dpkg -l | grep nginx
```

如果确认环境异常，建议直接重装 Nginx 默认配置：

```bash
sudo apt install --reinstall -y nginx
sudo ls -l /etc/nginx
```

### 预期恢复结果

至少应看到这些基础内容中的大部分：

- `/etc/nginx/nginx.conf`
- `/etc/nginx/conf.d/`
- `/etc/nginx/sites-available/`
- `/etc/nginx/sites-enabled/`

然后再继续放置：

```text
jenkins-kpi-platform.conf
```

并执行：

```bash
sudo nginx -t
sudo systemctl restart nginx
```

### 一句话总结

`total 0` 说明当前问题还停留在 “Nginx 基础环境不正常”，还没有进入“Jenkins 反向代理配置细节”这一步。

## 补充问题：`nginx: command not found` 且 `nginx.service could not be found`

### 现象

执行：

```bash
sudo nginx -v
sudo systemctl status nginx
```

输出：

```text
sudo: nginx: command not found
Unit nginx.service could not be found.
```

### 结论

这说明当前机器不是“目录结构不对”，而是 **Nginx 根本还没有安装好**。

也就是说，问题顺序应该这样理解：

1. 先确认 Nginx 已安装
2. 再确认 `/etc/nginx` 基础目录和 `nginx.conf` 存在
3. 最后才谈 `sites-available`、`conf.d` 和 `jenkins-kpi-platform.conf`

### 为什么这时不用继续纠结 `sites-available`

因为连 `nginx` 命令本身都不存在，`nginx.service` systemd 单元也不存在，说明还没进入“配置反向代理”这一步。

这就像你还没把软件装上，就先在讨论它的配置文件应该放哪个目录。

### 正确处理顺序

先安装 Nginx：

```bash
sudo apt update
sudo apt install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx
sudo systemctl status nginx
sudo ls -l /etc/nginx
```

如果安装过程中提示 dpkg 中断或依赖异常，则补执行：

```bash
sudo dpkg --configure -a
sudo apt -f install
sudo apt install -y nginx
```

### 什么时候才算进入下一步

至少满足以下条件：

- `sudo nginx -v` 能看到版本号
- `sudo systemctl status nginx` 能看到服务状态
- `/etc/nginx/nginx.conf` 已存在

这时才继续复制：

```bash
jenkins-kpi-platform.conf
```

到 `sites-available/` 或 `conf.d/`。

### 一句话总结

`command not found` + `nginx.service could not be found` 的根因不是“配置目录选错”，而是 “Nginx 还没装好”。

## 本次真实排查记录

### 现场命令与输出

用户在服务器上实际执行并看到：

```bash
sudo cp /opt/jenkins_robotframework/deploy/nginx/jenkins-kpi-platform.conf /etc/nginx/sites-available/jenkins-kpi-platform.conf
```

输出：

```text
cp: cannot create regular file '/etc/nginx/sites-available/jenkins-kpi-platform.conf': No such file or directory
```

继续排查：

```bash
sudo ls -l /etc/nginx
```

输出：

```text
total 0
```

再继续排查：

```bash
sudo nginx -v
sudo systemctl status nginx
```

输出：

```text
sudo: nginx: command not found
Unit nginx.service could not be found.
```

### 这次排查最终确认的根因

这次问题的根因已经可以明确归类为：

- 不是 `jenkins-kpi-platform.conf` 文件内容问题
- 不是 `cp` 命令写法问题
- 也不是单纯少了 `sites-available` 目录
- 而是服务器当前根本没有安装好 Nginx

### 这次问题给出的最终处理顺序

先安装 Nginx：

```bash
sudo apt update
sudo apt install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx
sudo systemctl status nginx
sudo nginx -v
sudo ls -l /etc/nginx
```

如果安装过程中遇到 dpkg 或依赖异常，再补：

```bash
sudo dpkg --configure -a
sudo apt -f install
sudo apt install -y nginx
```

### 后续注意

以后如果一开始就看到下面两类信号：

- `sudo: nginx: command not found`
- `Unit nginx.service could not be found`

就不要先花时间讨论 `sites-available`、`conf.d`、`nginx.conf` 目录细节，而应先回到“是否已安装 Nginx”这个更前置的问题。

## 本次继续排查：`curl -k -I https://10.71.210.104/jenkins/` 直连 443 失败

### 现场命令与输出

执行：

```bash
curl -k -I https://10.71.210.104/jenkins/
```

输出：

```text
curl: (7) Failed to connect to 10.71.210.104 port 443 after 0 ms: Could not connect to server
```

### 这说明什么

这说明当前故障点已经不在 `/jenkins/` 路径本身，而在更底层的 HTTPS 入口：服务器当前没有成功对外提供 `443`。

也就是说，此时还不能得出“Jenkins 反向代理规则错了”的结论，因为请求甚至还没真正到达 Nginx 的 `location /jenkins/` 这一层。

### 常见根因

最常见就是下面三类：

1. Nginx 没启动
2. Nginx 启动了，但没有监听 `443`
3. 服务器本机监听正常，但 `443` 被防火墙或网络策略拦住了

### 最短排查顺序

```bash
sudo systemctl status nginx
sudo ss -lntp | grep :443
sudo nginx -t
sudo journalctl -u nginx -n 100
curl -k -I https://127.0.0.1/jenkins/
```

### 如何解读结果

- 如果 `systemctl status nginx` 失败：先解决 Nginx 服务本身
- 如果 `ss -lntp | grep :443` 没结果：当前机器没有进程监听 `443`
- 如果 `curl -k -I https://127.0.0.1/jenkins/` 也失败：问题仍在 Nginx 配置、证书或监听阶段
- 如果 `127.0.0.1` 能通但 `10.71.210.104` 不通：优先怀疑防火墙、云安全组或内网访问策略

### 一句话总结

`curl: (7) Failed to connect ... port 443` 说明当前问题首先要检查“443 有没有成功监听和放通”，而不是先检查 Jenkins 页面路径细节。

## 本次继续排查：Nginx 已启动，但没有监听 443

### 现场命令与输出

执行：

```bash
sudo systemctl status nginx
sudo ss -lntp | grep :443
sudo nginx -t
sudo journalctl -u nginx -n 100
curl -k -I https://127.0.0.1/jenkins/
```

关键结果：

- `nginx.service` 显示 `active (running)`
- `sudo ss -lntp | grep :443` 没有任何输出
- `sudo nginx -t` 显示语法检查成功
- `curl -k -I https://127.0.0.1/jenkins/` 仍然连接失败

### 这组结果说明什么

这组证据已经把问题进一步收敛了：

1. Nginx 已经安装并且服务已启动
2. Nginx 主配置语法没有报错
3. 但当前没有任何进程监听 `443`
4. 连服务器本机访问 `https://127.0.0.1/jenkins/` 都失败

所以当前根因不再优先是“外部网络不通”，而是：

**提供 HTTPS 的 `listen 443 ssl` 配置块没有真正被 Nginx 加载生效。**

### 当前最可能的几种原因

最可能就是下面几类：

1. `jenkins-kpi-platform.conf` 还没有被复制到 Nginx 实际加载的目录
2. 文件已经复制了，但没有被 `sites-enabled` 或 `conf.d` include 进去
3. 当前生效的配置里只有 `listen 80`，没有真正启用 `listen 443 ssl`

### 这一阶段的正确排查方向

接下来不要优先查 Jenkins 本体，而应直接查 Nginx 当前到底加载了哪些配置文件。最有效的是看：

```bash
sudo ls -l /etc/nginx
sudo cat /etc/nginx/nginx.conf
sudo ls -l /etc/nginx/sites-available
sudo ls -l /etc/nginx/sites-enabled
sudo ls -l /etc/nginx/conf.d
sudo grep -R "listen 443" /etc/nginx
```

### 一句话总结

`nginx` 现在是“服务活着，但 HTTPS 配置没生效”，不是“服务没起”。

## 本次最终定位：配置文件已在 `sites-available`，但没有启用到 `sites-enabled`

### 现场证据

用户实际查到：

- `/etc/nginx/sites-available/jenkins-kpi-platform.conf` 已存在
- `/etc/nginx/sites-enabled/` 里仍然只有 `default`
- `/etc/nginx/conf.d/` 是空的
- `grep -R "listen 443" /etc/nginx` 能看到 `jenkins-kpi-platform.conf` 里有 `listen 443 ssl;`
- 但 `ss -lntp | grep :443` 没有任何监听结果

### 最终根因

这说明当前问题不是：

- Nginx 没安装
- Nginx 没启动
- `jenkins-kpi-platform.conf` 文件内容缺少 `listen 443 ssl;`

而是：

**配置文件虽然已经放到了 `/etc/nginx/sites-available/jenkins-kpi-platform.conf`，但没有被链接到 `/etc/nginx/sites-enabled/`，所以 Nginx 根本没有真正加载这份站点配置。**

### 为什么会出现这种现象

因为 Debian 风格 Nginx 的工作方式通常是：

1. `sites-available/` 只是“配置文件存放处”
2. `sites-enabled/` 才是“当前真正启用的站点入口”

所以文件仅仅存在于 `sites-available/`，并不代表它已经生效。

### 这次问题的直接修复命令

```bash
sudo ln -sf /etc/nginx/sites-available/jenkins-kpi-platform.conf /etc/nginx/sites-enabled/jenkins-kpi-platform.conf
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

### 修复后应立即验证

```bash
sudo ss -lntp | grep :443
curl -k -I https://127.0.0.1/jenkins/
curl -k -I https://10.71.210.104/jenkins/
```

### 一句话总结

这次 443 不监听的真正原因，不是 HTTPS 配置内容没写，而是 **站点文件没有从 `sites-available` 正式启用到 `sites-enabled`**。

## 本次修复后的验证结果

### 现场命令与输出

执行：

```bash
sudo ss -lntp | grep :443
curl -k -I https://127.0.0.1/jenkins/
```

结果：

- `ss -lntp | grep :443` 已能看到 `nginx` 正在监听 `0.0.0.0:443`
- `curl -k -I https://127.0.0.1/jenkins/` 已返回 HTTP 响应头，不再是连接失败
- 返回状态码是 `HTTP/1.1 403 Forbidden`
- 响应头中已经能看到 `X-Jenkins: 2.541.3`

### 这说明什么

这说明链路已经前进了一大步：

1. Nginx 的 `443` HTTPS 入口已经真正启用
2. Nginx 已经能够把 `/jenkins/` 请求转发到 Jenkins
3. 当前请求已经真正到达 Jenkins，而不是卡在 Nginx 监听层

### 为什么这里的 403 不是当前最关键的问题

因为这次排查的目标是确认：

- `443` 有没有监听成功
- Nginx 反代有没有真正把请求送到 Jenkins

从返回头里的 `X-Jenkins`、`X-Hudson`、`JSESSIONID` 可以确认，这两个目标已经达成。

也就是说，当前 `403 Forbidden` 说明的已经不是“反向代理没打通”，而是更靠后的 Jenkins 访问策略、来源校验、路径细节或会话逻辑问题。

### 这一阶段的一句话结论

**Nginx HTTPS 入口和 `/jenkins/` 反向代理已经基本打通；当前问题如果还存在，已经从“端口/站点启用问题”进入“Jenkins 应用层响应问题”。**

## 本次继续验证：`curl -L` 已经拿到 Jenkins 登录跳转页

### 现场命令与输出

执行：

```bash
curl -k -I -H "Host: 10.71.210.104" https://127.0.0.1/jenkins/
curl -k -L https://127.0.0.1/jenkins/
curl -k -I https://10.71.210.104/jenkins/
```

关键结果：

- `curl -I` 仍返回 `HTTP/1.1 403 Forbidden`
- 但 `curl -L https://127.0.0.1/jenkins/` 已经返回 Jenkins 的跳转页面内容：
	- `Authentication required`
	- `url=/login?from=%2Fjenkins%2F`
- 响应头里仍然稳定出现：
	- `X-Jenkins: 2.541.3`
	- `X-Hudson: 1.395`

### 这说明什么

这说明当前链路已经可以认为是通的：

1. `https://127.0.0.1/jenkins/` 已经能真正返回 Jenkins 页面内容
2. `/jenkins/` 子路径已经生效
3. Nginx 到 Jenkins 的反向代理已经工作

也就是说，现在已经不能再把问题归类为“443 没通”或“反向代理没配置好”。

### 如何理解这里的 403

在这次现场里，`curl -I` 的 `403 Forbidden` 已经不是主故障信号，因为：

- 同一路径使用 `curl -L` 已经能拿到 Jenkins 的登录跳转内容
- 这证明 Jenkins 实际已经在响应请求

因此，这里的 `403` 更适合看作 Jenkins 对当前请求方法、匿名访问、会话或安全策略的应用层响应，而不是 Nginx 配置失败。

### 这一步之后更合理的动作

1. 直接在 Windows 浏览器访问 `https://10.71.210.104/jenkins/`
2. 如果能看到 Jenkins 登录页，就进入 Jenkins Web
3. 在 `Manage Jenkins -> System` 中把 `Jenkins URL` 设置为：

```text
https://10.71.210.104/jenkins/
```

### 一句话总结

`curl -L` 已经拿到 Jenkins 登录跳转页，说明这次 Nginx HTTPS + `/jenkins/` 反向代理链路已经基本打通；剩下如果还有现象，优先按 Jenkins 应用层配置继续收口。

## 本次继续验证：Windows 浏览器访问 `/jenkins/` 显示 404 Not Found

### 现象

服务器侧验证时：

- `curl -k -L https://127.0.0.1/jenkins/` 已能拿到 Jenkins 登录跳转页内容

但 Windows 浏览器直接访问：

```text
https://10.71.210.104/jenkins/
```

最终看到的是：

```text
404 Not Found
```

### 这说明什么

这类组合现象通常说明：

1. Nginx 到 Jenkins 的反向代理其实已经通了
2. 但 Jenkins 返回的页面内容里，仍然把自己当成挂在根路径 `/` 下
3. 浏览器继续请求 `/login`、`/static/...` 等根路径
4. 而 Nginx 当前只配置了 `/jenkins/`，没有把根路径 `/` 也代理给 Jenkins
5. 所以浏览器最后看到 `404 Not Found`

### 为什么会这样

从前面的响应内容可以看到，Jenkins 页面里出现的是：

- `/login?from=%2Fjenkins%2F`
- `/static/...`
- 以及 `http://10.71.210.104:8080/...`

这说明 Jenkins 的 **`JENKINS_PREFIX=/jenkins` 很可能还没有真正生效**，或者 Jenkins 仍然保留着旧的外部 URL 认知。

### 当前最优先检查项

先检查 systemd 里的 Jenkins 环境变量是否真的带上了 prefix：

```bash
sudo systemctl cat jenkins
sudo systemctl show jenkins --property=Environment
```

目标是确认能看到：

```text
JENKINS_PREFIX=/jenkins
```

### 如果没看到该怎么办

说明 Jenkins 的 drop-in 配置没有真正生效，应回到：

```bash
sudo systemctl edit jenkins
```

确认内容为：

```ini
[Service]
Environment="JENKINS_PREFIX=/jenkins"
```

然后执行：

```bash
sudo systemctl daemon-reload
sudo systemctl restart jenkins
sudo systemctl status jenkins
```

### 一句话总结

浏览器里的 `404 Not Found` 在这个阶段通常不是 Nginx 又坏了，而是 **Jenkins 还没有真正按 `/jenkins` 子路径返回页面和跳转**。

## 本次最终确认：`JENKINS_PREFIX=/jenkins` 根本没有进入 Jenkins 运行环境

### 现场证据

用户实际执行后看到：

- `sudo systemctl show jenkins --property=Environment` 里没有 `JENKINS_PREFIX=/jenkins`
- `curl -I http://127.0.0.1:8080/jenkins/` 返回 `403 Forbidden`
- `curl -I http://127.0.0.1:8080/login` 返回 `200 OK`

### 这组结果说明什么

这已经不是“怀疑 Prefix 没生效”，而是可以直接确认：

**Jenkins 当前仍在根路径 `/` 下运行。**

因为如果 `JENKINS_PREFIX=/jenkins` 真的进入了 Jenkins 的 systemd 运行环境，那么 `systemctl show jenkins --property=Environment` 里应当明确能看到这个环境变量。

现在既然没有看到，就说明前面通过 `systemctl edit jenkins` 写入的 drop-in 配置并没有真正生效到当前 Jenkins 进程。

### 这也解释了为什么浏览器会看到 404

链路其实已经变成这样：

1. Nginx 把 `/jenkins/` 请求转发给 Jenkins
2. Jenkins 自己却仍然认为自己挂在根路径 `/`
3. 页面继续跳转到 `/login`、`/static/...`
4. 浏览器请求这些根路径时，Nginx 没有对应代理规则
5. 所以最终显示 `404 Not Found`

### 这次问题的最稳妥修复方式

直接写死 systemd override 文件，不再依赖交互式编辑器：

```bash
sudo mkdir -p /etc/systemd/system/jenkins.service.d
sudo tee /etc/systemd/system/jenkins.service.d/override.conf > /dev/null << 'EOF'
[Service]
Environment="JENKINS_PREFIX=/jenkins"
EOF
sudo systemctl daemon-reload
sudo systemctl restart jenkins
sudo systemctl show jenkins --property=Environment
```

### 修复后的检查目标

必须明确看到：

```text
JENKINS_PREFIX=/jenkins
```

然后再继续验证浏览器访问：

```text
https://10.71.210.104/jenkins/
```

### 一句话总结

这次浏览器 `404` 的真正根因已经确认，不是 Nginx，不是证书，而是 **`JENKINS_PREFIX=/jenkins` 没有真正进入 Jenkins 的 systemd 环境**。

## 补充说明：`daemon-reload`、`reload`、`restart`、`enable` 到底分别干什么

这几个命令名字很像，但作用层次完全不一样。混用之后，最常见的结果就是：

- 文件明明改了，但服务没吃到新配置
- 服务已经在跑，但人误以为“重启过就一定生效了”
- 把“开机自启”和“立即生效”混成一件事

下面按最实用的方式区分。

### 1. `sudo systemctl daemon-reload`

#### 它做什么

让 `systemd` 重新读取 service 定义文件。

这里说的定义文件包括：

- `/etc/systemd/system/*.service`
- `/etc/systemd/system/<service>.service.d/*.conf`
- 发行版自带的 `/lib/systemd/system/*.service` 或 `/usr/lib/systemd/system/*.service`

#### 它不做什么

- 不会自动重启服务
- 不会让当前进程立刻换成新配置
- 不等于服务已经生效

#### 最典型使用场景

你刚改了：

- `jenkins.service`
- `reporting-portal.service`
- `kpi-portal.service`
- `jenkins.service.d/override.conf`

这时必须先执行一次 `daemon-reload`，告诉 systemd：“服务定义文件变了，重新读一遍。”

#### 在这次 Jenkins 问题里的实际作用

你写入了：

```ini
[Service]
Environment="JENKINS_PREFIX=/jenkins"
```

到：

```text
/etc/systemd/system/jenkins.service.d/override.conf
```

如果不执行 `sudo systemctl daemon-reload`，systemd 可能还在拿旧的 Jenkins service 定义工作，后面的 `restart jenkins` 也就不一定真的吃到 `JENKINS_PREFIX=/jenkins`。

#### 一句话记忆

**`daemon-reload` = 重新读“服务定义文件”，不是重启服务本身。**

### 2. `sudo systemctl reload <service>`

#### 它做什么

让“这个服务进程自己”重新加载它支持热加载的运行配置，而不完全停掉再启动。

#### 它的前提

不是所有服务都支持 `reload`。

只有服务本身实现了 reload 动作，或者它的 unit 文件里定义了 `ExecReload=...`，这个命令才真正有意义。

#### 常见例子

`nginx` 很适合 `reload`：

```bash
sudo nginx -t
sudo systemctl reload nginx
```

这表示：

1. 先确认新 Nginx 配置语法没问题
2. 让正在运行的 Nginx 进程平滑加载新配置
3. 尽量不打断现有连接

#### 它不适合这次 Jenkins Prefix 问题

因为你这次改的不是 Jenkins 自己运行时热加载的某个网页配置，而是 **systemd 层的环境变量定义**。

这种变化不是 `reload jenkins` 能解决的。它需要：

1. `daemon-reload`
2. `restart jenkins`

#### 一句话记忆

**`reload` = 让服务进程尝试热加载配置；前提是这个服务自己支持。**

### 3. `sudo systemctl restart <service>`

#### 它做什么

先停掉服务，再重新启动服务。

#### 它的意义

让新的进程按“当前 systemd 已加载的定义”重新跑起来。

#### 典型使用场景

- 改了 Jenkins 的 systemd 环境变量
- 改了 Python 服务的 `ExecStart`
- 改了 WorkingDirectory
- 改了 PATH
- 服务本身不支持热加载

#### 在这次 Jenkins 问题里的实际作用

`daemon-reload` 只是让 systemd 知道定义变了；
真正让 Jenkins 带着 `JENKINS_PREFIX=/jenkins` 重新启动起来的，是：

```bash
sudo systemctl restart jenkins
```

#### 常见误区

很多人以为：

- “我已经改了 override.conf”
- “我也 restart 了”
- “那就一定生效了”

这不一定成立。

如果改完 service 定义文件后 **没有先做 `daemon-reload`**，那么 `restart` 仍可能基于旧定义启动服务。

#### 一句话记忆

**`restart` = 按当前已加载的定义，把服务进程重新启动一遍。**

### 4. `sudo systemctl enable <service>`

#### 它做什么

把服务加入开机启动。

#### 它不做什么

- 不等于立刻启动服务
- 不等于重启服务
- 不等于应用新配置

#### 典型例子

```bash
sudo systemctl enable jenkins
```

这条命令的意思只是：

“以后机器重启时，systemd 会自动拉起 Jenkins。”

如果你想“现在就立刻启动”，还要执行：

```bash
sudo systemctl start jenkins
```

如果你想“现在就按新配置重新跑”，则通常是：

```bash
sudo systemctl daemon-reload
sudo systemctl restart jenkins
```

#### 一句话记忆

**`enable` = 影响下次开机时是否自动拉起，不负责当前进程生效。**

### 最实用的对照表

| 命令 | 作用对象 | 立即改当前进程吗 | 常见用途 |
|---|---|---|---|
| `daemon-reload` | systemd 的服务定义缓存 | 否 | 改了 `.service` / `override.conf` 后重新读定义 |
| `reload` | 服务进程自身 | 视服务而定 | Nginx 这类支持热加载的服务平滑重载配置 |
| `restart` | 服务进程自身 | 是 | 停掉再启动，使新进程按当前定义运行 |
| `enable` | 开机启动策略 | 否 | 设置服务在系统启动时自动拉起 |

### 这次 Jenkins / Nginx 场景里该怎么用

#### 改 Jenkins 的 systemd override 时

正确顺序是：

```bash
sudo systemctl daemon-reload
sudo systemctl restart jenkins
```

原因：改的是 systemd 定义，不是 Jenkins 自己支持热加载的网页配置。

#### 改 Nginx 站点配置时

更推荐：

```bash
sudo nginx -t
sudo systemctl reload nginx
```

原因：Nginx 支持平滑重载，通常不需要粗暴中断服务。

#### 想让 Jenkins 或 Nginx 开机自动起来时

用：

```bash
sudo systemctl enable jenkins
sudo systemctl enable nginx
```

但这和“当前这一刻配置是否已经生效”是两回事。

### 一句话总记忆

- `daemon-reload`：重新读服务定义文件
- `reload`：让服务尝试热加载配置
- `restart`：把服务进程重启一遍
- `enable`：设置开机自启

## 补充说明：Jenkins / Nginx / Portal 三类服务的标准排障顺序

下面这套顺序的目标很简单：

- 先判断问题在哪一层
- 再决定该看服务、配置、端口还是反向代理
- 避免一上来就盲目重启，把问题越搅越乱

最核心原则只有一条：

**永远先从“当前服务活没活、监听没监听、日志有没有报错”开始，再往上看代理和浏览器现象。**

### 一. Jenkins 本体排障顺序

适用场景：

- Jenkins 页面打不开
- Jenkins 登录跳转异常
- Jenkins 重启后行为不对
- 改了 Prefix、Java 参数、systemd override 后怀疑没生效

#### 第一步：先看 Jenkins 服务是否真的在跑

```bash
sudo systemctl status jenkins
systemctl is-active jenkins
```

判断：

- `active`：说明 Jenkins 进程当前活着，继续看端口和行为
- `inactive` / `failed`：先看日志，不要直接猜 Web 问题

#### 第二步：看 Jenkins 最近日志

```bash
sudo journalctl -u jenkins -n 100
```

重点看：

- Java 启动失败
- 端口占用
- 配置文件报错
- 权限问题
- 插件或 war 解包异常

#### 第三步：确认 Jenkins 是否真的监听在 8080

```bash
sudo ss -lntp | grep :8080
```

判断：

- 能看到 `:8080`：说明 Jenkins 至少把本地 HTTP 端口拉起来了
- 看不到：说明问题还在 Jenkins 本体启动层，先别排 Nginx

#### 第四步：直接从服务器本机访问 Jenkins

```bash
curl -I http://127.0.0.1:8080/
curl -I http://127.0.0.1:8080/login
curl -I http://127.0.0.1:8080/jenkins/
```

这一步的意义是把问题和 Nginx 剥离开。

判断：

- 本机 `127.0.0.1:8080` 都不通：问题就在 Jenkins 本体
- `/login` 能通，但 `/jenkins/` 行为不对：优先怀疑 Prefix 没生效

#### 第五步：如果改过 systemd 配置，检查环境变量是否真正生效

```bash
sudo systemctl show jenkins --property=Environment
sudo systemctl cat jenkins
```

重点看：

- `JENKINS_PREFIX=/jenkins` 是否真的在 Environment 里
- override 文件是否真的被 systemd 读到

#### 第六步：只有确认改的是 systemd 定义时，才执行这组命令

```bash
sudo systemctl daemon-reload
sudo systemctl restart jenkins
sudo systemctl status jenkins
```

#### Jenkins 排障的一句话顺序

**先看服务活没活，再看日志，再看 8080 监听，再看本机 curl，再看 systemd 环境变量。**

### 二. Nginx 反向代理排障顺序

适用场景：

- `https://10.71.210.104/jenkins/` 打不开
- 浏览器报 `502`、`404`、连不上 `443`
- Jenkins 本机能通，但外部 HTTPS 不通

#### 第一步：先看 Nginx 服务状态

```bash
sudo systemctl status nginx
systemctl is-active nginx
```

#### 第二步：看 Nginx 配置语法

```bash
sudo nginx -t
```

如果这里不过，后面所有代理现象都不用再猜，先修配置语法。

#### 第三步：确认 Nginx 是否真的监听了 80 / 443

```bash
sudo ss -lntp | grep :80
sudo ss -lntp | grep :443
```

判断：

- 看不到 `:443`：HTTPS server block 没真正生效，先别怀疑 Jenkins
- `:443` 在监听：再继续看转发行为

#### 第四步：从服务器本机直接打 Nginx HTTPS 入口

```bash
curl -k -I https://127.0.0.1/jenkins/
curl -k -L https://127.0.0.1/jenkins/
```

判断：

- 本机都不通：问题在 Nginx/证书/站点启用层
- 本机能通，外部 IP 不通：优先怀疑防火墙或网络路径

#### 第五步：确认站点配置是否真的被加载

```bash
sudo ls -l /etc/nginx/sites-available
sudo ls -l /etc/nginx/sites-enabled
sudo cat /etc/nginx/nginx.conf
```

重点看：

- 配置文件是不是只放进了 `sites-available`
- 有没有真正链接到 `sites-enabled`
- `nginx.conf` 是否 include 了对应目录

#### 第六步：看 Nginx 日志

```bash
sudo journalctl -u nginx -n 100
```

如果需要更细，再看站点 access/error log。

#### 第七步：改完 Nginx 配置后的标准动作

```bash
sudo nginx -t
sudo systemctl reload nginx
```

除非 Nginx 自身状态已经异常，否则优先 `reload`，不优先 `restart`。

#### Nginx 排障的一句话顺序

**先看服务状态，再看配置语法，再看 80/443 监听，再看本机 HTTPS，再看站点是否真的启用。**

### 三. Portal 服务排障顺序

这里的 Portal 指：

- `reporting-portal`
- `kpi-portal`

适用场景：

- `/reports/health` 不通
- `/kpi/health` 不通
- Jenkins 已经正常，但 Portal 页面或 API 异常

#### 第一步：先看服务状态

```bash
sudo systemctl status reporting-portal
sudo systemctl status kpi-portal
systemctl is-active reporting-portal
systemctl is-active kpi-portal
```

#### 第二步：看服务日志

```bash
sudo journalctl -u reporting-portal -n 100
sudo journalctl -u kpi-portal -n 100
```

重点看：

- Python 模块缺失
- venv 路径错
- `ExecStart` 错
- 端口占用
- 环境变量缺失

#### 第三步：确认端口监听

```bash
sudo ss -lntp | grep :8000
sudo ss -lntp | grep :8001
```

判断：

- 看不到端口：问题先在 Portal 服务本体，不在 Nginx

#### 第四步：从服务器本机直接打健康接口

```bash
curl --noproxy localhost http://127.0.0.1:8000/health
curl --noproxy localhost http://127.0.0.1:8001/health
```

如果本机直连都失败，就先不要排反向代理。

#### 第五步：检查 service 定义是否指向正确目录和 venv

重点核对：

- `WorkingDirectory`
- `Environment="PATH=.../venv/bin"`
- `ExecStart`

这类问题最常见的根因是：

- 代码已经更新，但 venv 没装新依赖
- service 还指向旧目录
- `uvicorn app.main:app` 路径不对

#### 第六步：如果你刚改过 `.service` 文件

```bash
sudo systemctl daemon-reload
sudo systemctl restart reporting-portal
sudo systemctl restart kpi-portal
```

#### Portal 排障的一句话顺序

**先看服务状态，再看日志，再看 8000/8001 监听，再看本机健康接口，再检查 service 的 WorkingDirectory、PATH、ExecStart。**

### 四. 三类服务联合排障时的推荐顺序

如果你面对的是“浏览器打不开页面”，不要一上来就所有服务一起乱重启。推荐固定顺序：

1. 先确认后端服务本体是否正常
2. 再确认 Nginx 是否把请求转发到了后端
3. 最后再看浏览器层现象

按这套顺序落地就是：

#### Jenkins 入口异常时

1. `systemctl status jenkins`
2. `ss -lntp | grep :8080`
3. `curl -I http://127.0.0.1:8080/login`
4. `systemctl status nginx`
5. `nginx -t`
6. `ss -lntp | grep :443`
7. `curl -k -L https://127.0.0.1/jenkins/`
8. 最后再看 Windows 浏览器

#### Portal 入口异常时

1. `systemctl status reporting-portal` / `kpi-portal`
2. `ss -lntp | grep :8000` / `:8001`
3. `curl http://127.0.0.1:8000/health` / `:8001/health`
4. `systemctl status nginx`
5. `curl -k -I https://127.0.0.1/reports/health`
6. `curl -k -I https://127.0.0.1/kpi/health`
7. 最后再看外部浏览器

### 五. 最后给自己的一条纪律

排障时优先做这三类动作：

- `status`
- `ss -lntp`
- `curl`

谨慎做这两类动作：

- `restart`
- 改配置文件

原因很简单：

**先观察，再判断，再修改。不要把“确认问题”与“破坏现场”混在同一步里。**

## 补充说明：现场快速用的 5 条速查卡

下面这两份是把前面的排障顺序再压缩后的“值班版”。

特点是：

- 条数少
- 顺序固定
- 适合现场直接复制执行

### 一. Jenkins 专用 5 条速查卡

适用场景：

- Jenkins 页面打不开
- Jenkins 登录异常
- 改了 Prefix / override / Java 参数后怀疑没生效

#### 第 1 条：先看 Jenkins 服务状态

```bash
sudo systemctl status jenkins
systemctl is-active jenkins
```

#### 第 2 条：再看 Jenkins 最近日志

```bash
sudo journalctl -u jenkins -n 100
```

#### 第 3 条：确认 8080 是否监听

```bash
sudo ss -lntp | grep :8080
```

#### 第 4 条：从本机直打 Jenkins

```bash
curl -I http://127.0.0.1:8080/
curl -I http://127.0.0.1:8080/login
curl -I http://127.0.0.1:8080/jenkins/
```

#### 第 5 条：如果改过 systemd 配置，再查环境变量和 override

```bash
sudo systemctl show jenkins --property=Environment
sudo systemctl cat jenkins
```

如果确认改的是 `.service` 或 `override.conf`，最后再执行：

```bash
sudo systemctl daemon-reload
sudo systemctl restart jenkins
```

#### Jenkins 版一句话记忆

**先看服务，再看日志，再看 8080，再看本机 curl，最后才查 Prefix / override。**

### 二. Portal 专用 5 条速查卡

适用场景：

- `/reports/health` 不通
- `/kpi/health` 不通
- Portal 页面或 API 异常

#### 第 1 条：先看服务状态

```bash
sudo systemctl status reporting-portal
sudo systemctl status kpi-portal
systemctl is-active reporting-portal
systemctl is-active kpi-portal
```

#### 第 2 条：再看最近日志

```bash
sudo journalctl -u reporting-portal -n 100
sudo journalctl -u kpi-portal -n 100
```

#### 第 3 条：确认 8000 / 8001 是否监听

```bash
sudo ss -lntp | grep :8000
sudo ss -lntp | grep :8001
```

#### 第 4 条：从本机直打健康接口

```bash
curl --noproxy localhost http://127.0.0.1:8000/health
curl --noproxy localhost http://127.0.0.1:8001/health
```

#### 第 5 条：如果改过 service 文件，再检查 service 定义并做生效动作

重点看：

- `WorkingDirectory`
- `Environment="PATH=.../venv/bin"`
- `ExecStart`

如果确认改过 `.service` 文件，再执行：

```bash
sudo systemctl daemon-reload
sudo systemctl restart reporting-portal
sudo systemctl restart kpi-portal
```

#### Portal 版一句话记忆

**先看服务，再看日志，再看端口，再看本机健康接口，最后才查 service 定义。**

## 补充说明：可直接复制执行的一屏版纯命令清单

下面这两组不带解释，目标就是现场快速粘贴执行。

### Jenkins 一屏版

```bash
sudo systemctl status jenkins
systemctl is-active jenkins
sudo journalctl -u jenkins -n 100
sudo ss -lntp | grep :8080
curl -I http://127.0.0.1:8080/
curl -I http://127.0.0.1:8080/login
curl -I http://127.0.0.1:8080/jenkins/
sudo systemctl show jenkins --property=Environment
sudo systemctl cat jenkins
```

如果你刚改过 Jenkins 的 `.service` 或 `override.conf`，再补执行：

```bash
sudo systemctl daemon-reload
sudo systemctl restart jenkins
sudo systemctl status jenkins
```

### Portal 一屏版

```bash
sudo systemctl status reporting-portal
sudo systemctl status kpi-portal
systemctl is-active reporting-portal
systemctl is-active kpi-portal
sudo journalctl -u reporting-portal -n 100
sudo journalctl -u kpi-portal -n 100
sudo ss -lntp | grep :8000
sudo ss -lntp | grep :8001
curl --noproxy localhost http://127.0.0.1:8000/health
curl --noproxy localhost http://127.0.0.1:8001/health
```

如果你刚改过 Portal 的 `.service` 文件，再补执行：

```bash
sudo systemctl daemon-reload
sudo systemctl restart reporting-portal
sudo systemctl restart kpi-portal
sudo systemctl status reporting-portal
sudo systemctl status kpi-portal
```

### Nginx 一屏版

```bash
sudo systemctl status nginx
systemctl is-active nginx
sudo nginx -t
sudo ss -lntp | grep :80
sudo ss -lntp | grep :443
curl -k -I https://127.0.0.1/jenkins/
curl -k -L https://127.0.0.1/jenkins/
sudo ls -l /etc/nginx/sites-available
sudo ls -l /etc/nginx/sites-enabled
sudo journalctl -u nginx -n 100
```

如果你刚改过 Nginx 配置文件，再补执行：

```bash
sudo nginx -t
sudo systemctl reload nginx
sudo systemctl status nginx
```

## 补充说明：按现象选择排障入口的总判断表

下面这张表的目标不是一次性解释所有根因，而是先帮你决定：

- 当前应该先跑 Jenkins 清单
- 还是先跑 Nginx 清单
- 还是先跑 Portal 清单

### 一. 最常见现象对应的第一排查入口

| 浏览器或 curl 现象 | 优先排查入口 | 原因判断 |
|---|---|---|
| 页面完全打不开，提示连接失败、超时、`Failed to connect` | Nginx 一屏版 | 先判断 80/443 是否监听，问题通常还在入口层 |
| `https://IP/jenkins/` 返回 `404 Not Found` | 先 Nginx 一屏版，再 Jenkins 一屏版 | 先确认代理入口是否真的在转发；如果 HTTPS 本机已通，再查 Jenkins Prefix |
| `502 Bad Gateway` | 先 Jenkins 一屏版或 Portal 一屏版，再看 Nginx 一屏版 | 502 通常表示 Nginx 活着，但后端服务没起来或端口不通 |
| `403 Forbidden` 且响应头里有 `X-Jenkins` | Jenkins 一屏版 | 说明请求已经到 Jenkins，本体行为比代理更值得先查 |
| Jenkins 登录页能打开，但跳转路径异常、资源路径异常 | Jenkins 一屏版 | 高概率是 Prefix、Jenkins URL 或 systemd 环境变量问题 |
| `/reports/health` 不通 | Portal 一屏版 | 先看 reporting-portal 服务、8000 端口和本机健康检查 |
| `/kpi/health` 不通 | Portal 一屏版 | 先看 kpi-portal 服务、8001 端口和本机健康检查 |
| Jenkins 本机 `127.0.0.1:8080` 能通，但外部 HTTPS 不通 | Nginx 一屏版 | 说明 Jenkins 本体大概率没问题，优先看 Nginx / 443 / 证书 / 网络 |
| Portal 本机健康检查能通，但外部路径不通 | Nginx 一屏版 | 说明后端进程在跑，问题更可能在反向代理路径或入口层 |

### 二. 现场最实用的判断顺序

#### 情况 1：浏览器提示“连不上”

先跑：

```text
Nginx 一屏版
```

因为这类问题最常见的根因是：

- Nginx 没启动
- 443 没监听
- 证书或站点配置没真正生效
- 网络或防火墙挡住入口

#### 情况 2：浏览器能打开入口，但返回 404

先这样判断：

1. 如果是 `https://IP/jenkins/` 返回 404：
先跑 `Nginx 一屏版`，确认入口是否真的转发；
如果本机 `curl -k -L https://127.0.0.1/jenkins/` 已经能拿到 Jenkins 内容，再转 `Jenkins 一屏版` 查 Prefix。

2. 如果是 `https://IP/reports/...` 或 `https://IP/kpi/...` 返回 404：
先跑 `Portal 一屏版`，确认服务和健康接口；
本机后端能通但外部仍 404，再转 `Nginx 一屏版`。

#### 情况 3：浏览器返回 502

优先顺序：

1. 先查后端服务本体
2. 再查 Nginx

具体就是：

- Jenkins 相关页面报 502：先 `Jenkins 一屏版`
- `/reports/` 报 502：先 `Portal 一屏版`
- `/kpi/` 报 502：先 `Portal 一屏版`

原因是 502 往往说明：

- 入口代理在
- 但代理后面的服务端口没起来，或者后端拒绝连接

#### 情况 4：登录页能开，但跳转不对、资源 404、URL 很怪

先跑：

```text
Jenkins 一屏版
```

这类问题优先怀疑：

- `JENKINS_PREFIX=/jenkins` 没生效
- Jenkins URL 没设对
- Jenkins 仍把自己当根路径 `/`

#### 情况 5：健康检查路径不通

直接按服务归属走：

- `/reports/health` -> `Portal 一屏版`
- `/kpi/health` -> `Portal 一屏版`
- `/jenkins/` -> Jenkins 入口先看 `Nginx 一屏版`，确认已进 Jenkins 后再看 `Jenkins 一屏版`

### 三. 一句话版总决策

- 连不上：先 Nginx
- 502：先后端服务，再 Nginx
- Jenkins 登录跳转异常：先 Jenkins
- Portal 健康检查异常：先 Portal
- 本机后端能通、外部不通：回头查 Nginx

## 极简版：故障现象 -> 先跑哪套命令

| 现象 | 先跑哪套命令 |
|---|---|
| 浏览器连不上 / 超时 / `Failed to connect` | Nginx 一屏版 |
| `https://IP/jenkins/` 返回 `404` | 先 Nginx 一屏版，再 Jenkins 一屏版 |
| Jenkins 页面返回 `502` | Jenkins 一屏版 |
| `/reports/` 或 `/kpi/` 返回 `502` | Portal 一屏版 |
| Jenkins 登录跳转异常 / 资源 404 / URL 很怪 | Jenkins 一屏版 |
| `/reports/health` 不通 | Portal 一屏版 |
| `/kpi/health` 不通 | Portal 一屏版 |
| Jenkins 本机能通、外部 HTTPS 不通 | Nginx 一屏版 |
| Portal 本机健康检查能通、外部路径不通 | Nginx 一屏版 |