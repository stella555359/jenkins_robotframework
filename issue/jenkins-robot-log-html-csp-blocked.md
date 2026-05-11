# Jenkins archived Robot Framework log.html 打开报错 "Opening Robot Framework log failed"

## 日期
2025-05-11

## 背景
在 Portal Run Detail 页面点击 Robot Log 链接，直接打开 Jenkins archived artifact 中的 `log.html`。页面弹出错误提示：

```
Opening Robot Framework log failed
```

log.html 文件本身存在且已被 Jenkins 正确归档，但页面内容无法渲染。

## 问题
Robot Framework 生成的 `log.html` 依赖内联 JavaScript 来渲染测试结果。当通过 Jenkins archived artifact URL 访问时（例如 `https://10.71.210.104/jenkins/job/robot/job/robot-execution/42/artifact/artifacts/...log.html`），Jenkins 默认在 HTTP 响应头中添加了严格的 Content-Security-Policy（CSP）：

```
Content-Security-Policy: sandbox; default-src 'none'; img-src 'self'; style-src 'self';
```

这个策略禁止了所有 JavaScript 执行（`script-src 'none'`），导致 log.html 内的内联脚本被浏览器拦截，页面无法正常工作。

## 原因
Jenkins 从 1.641 / 1.625.3 起默认对 `DirectoryBrowserSupport`（即 archived artifacts 的访问路径）设置了非常严格的 CSP 头。这是 Jenkins 的安全加固措施，防止恶意 artifact 执行 XSS 攻击。但副作用是所有需要 JavaScript 的 artifact（Robot Framework log.html、Allure report 等）都无法正常显示。

对应的 Jenkins 系统属性：

```
hudson.model.DirectoryBrowserSupport.CSP
```

默认值：

```
sandbox; default-src 'none'; img-src 'self'; style-src 'self';
```

## 解决方法

### 方案 1：Nginx 层剥离 CSP 头（推荐，已落实）

在 Nginx 反向代理配置中，对 Jenkins artifact URL 路径单独处理，用 `proxy_hide_header` 移除 Jenkins 返回的 CSP 头。只影响 artifact 页面，不影响 Jenkins 主 UI 的安全策略。

修改文件：`deploy/nginx/jenkins-kpi-platform.conf`

在 `location /jenkins/` 之前增加：

```nginx
# Serve Jenkins archived artifacts (log.html etc.) without CSP restriction.
# Jenkins default CSP blocks inline JavaScript, which breaks Robot Framework log.html.
# This block MUST appear before the general /jenkins/ prefix location.
location ~ ^/jenkins/job/.+/artifact/ {
    proxy_pass http://127.0.0.1:8080;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    proxy_hide_header Content-Security-Policy;
}
```

部署步骤：

```bash
sudo cp /opt/jenkins_robotframework/deploy/nginx/jenkins-kpi-platform.conf \
        /etc/nginx/sites-available/jenkins-kpi-platform.conf
sudo nginx -t
sudo systemctl reload nginx
```

### 方案 2：Jenkins 全局关闭 artifact CSP（备选）

如果不走 Nginx，也可以直接在 Jenkins 侧关闭 artifact 的 CSP 限制。

**临时生效**（重启后失效）— 通过 Jenkins Script Console（`Manage Jenkins -> Script Console`）执行：

```groovy
System.setProperty("hudson.model.DirectoryBrowserSupport.CSP", "")
```

**永久生效** — 在 Jenkins 启动参数中加入 JVM 系统属性：

```
-Dhudson.model.DirectoryBrowserSupport.CSP=""
```

典型位置：

- systemd：`/etc/default/jenkins` 或 `/etc/systemd/system/jenkins.service.d/override.conf` 中的 `JAVA_OPTS`
- Docker：`docker run` 或 compose 中的 `JAVA_OPTS` 环境变量

注意：方案 2 会对所有 archived artifact 全局生效，降低了 Jenkins artifact 页面的 XSS 防护。如果 Jenkins 只在内网使用且 artifact 来源可信，风险可接受。

## 后续注意
1. 如果后续更换 Nginx 配置或重新生成配置文件，需要保留 artifact 路径的 CSP 剥离 location 块。
2. 该 location 块必须出现在通用 `location /jenkins/` 之前，否则不会被匹配到。
3. 如果 Jenkins 升级后改变了 artifact URL 路径格式，需要相应调整正则 `^/jenkins/job/.+/artifact/`。
4. Allure report 等其他需要 JavaScript 的 artifact 同样受益于此修复。
