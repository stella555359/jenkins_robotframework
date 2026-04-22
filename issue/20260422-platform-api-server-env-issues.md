# Platform API 服务器环境问题汇总

## 问题 1：服务器时间不准，systemd-timesyncd 已启用但无法同步

### 日期
2026-04-22

### 背景
在 Debian 服务器 `CZ23420CKK` 上执行 Platform API 相关操作时，发现服务器时间与本机时间相差约十几分钟，需要判断是时区问题、虚拟机时间源问题，还是 NTP 校时失败。

已确认的关键信息包括：

- `timedatectl` 显示 `Time zone: Asia/Shanghai (CST, +0800)`
- `System clock synchronized: no`
- `NTP service: active`
- `systemd-detect-virt` 输出 `none`
- `/sys/devices/system/clocksource/clocksource0/current_clocksource` 输出 `tsc`

### 问题
服务器本地时间不正确，且尝试手工设置时间时出现如下报错：

```text
Failed to set time: Automatic time synchronization is enabled
```

进一步排查 `systemd-timesyncd` 日志后，持续出现如下超时信息：

```text
Timed out waiting for reply from x.x.x.x:123
```

对应的时间源为：

```text
0.debian.pool.ntp.org
1.debian.pool.ntp.org
2.debian.pool.ntp.org
3.debian.pool.ntp.org
```

### 原因
已确认这不是时区配置错误，也不是 KVM 虚机依赖宿主机时间的场景，而是当前服务器无法通过 `systemd-timesyncd` 成功访问公网 NTP。

根因判断如下：

1. 时区已经正确设置为 `Asia/Shanghai`。
2. 该机器不是虚拟机兜底场景，`systemd-detect-virt` 为 `none`。
3. `systemd-timesyncd` 能解析到公网 NTP 地址，但发往 UDP 123 的请求持续超时。
4. 高概率是网络策略限制了公网 NTP，或者该环境本就要求使用公司内网 NTP 服务器。

### 解决方法
先采用“手工修正当前时间 + 暂不启用无效自动校时”的保底方案：

```bash
sudo timedatectl set-ntp false
sudo timedatectl set-time "2026-04-22 10:03:00"
sudo hwclock --systohc
date
```

处理结果：

1. 当前系统时间已修正到正确值。
2. RTC 已同步写回，机器重启后仍有较大概率保持接近正确时间。
3. 因公网 NTP 不通，当前不建议重新执行 `sudo timedatectl set-ntp true`，否则只会恢复到一个持续同步失败的状态。

### 后续注意
后续需要补齐真正可持续的时间同步方案，优先级如下：

1. 向运维或网络侧确认是否有可访问的公司内网 NTP 服务器。
2. 如果有内网 NTP，则修改 `/etc/systemd/timesyncd.conf` 中的 `NTP=` 配置并重启 `systemd-timesyncd`。
3. 如果没有内网 NTP，则至少在关键任务执行前人工核对一次 `date` 输出，发现偏差时再手工校时。
4. 当前不要把“`System clock synchronized: no`”简单等同于“时间一定错误”，应结合当前实际时间值和同步机制一起判断。

## 问题 2：pytest 已生成 allure-results，但服务器缺少 Allure CLI

### 日期
2026-04-22

### 背景
在 Platform API 目录下执行 Step 9 自动化测试，希望同时生成 Allure 结果并在服务器上直接查看报告。

在此之前，还需要先把 Python 测试工具装进当前虚拟环境，包括：

- `pytest`
- `allure-pytest`

实际执行命令：

```bash
python -m pytest tests/test_health.py tests/test_runs.py --alluredir=allure-results
```

执行结果：

```text
9 passed in 0.08s
```

随后执行：

```bash
allure serve allure-results
```

### 问题
服务器报错如下：

```text
-bash: allure: command not found
```

此外，在安装阶段还出现过一个容易混淆的问题：

```text
ERROR: Could not find a version that satisfies the requirement allure (from versions: none)
ERROR: No matching distribution found for allure
```

### 原因
这里混淆了两类组件：

1. `allure-pytest` 是 Python 侧 pytest 插件，用于生成 `allure-results`。
2. `allure` 命令来自 Allure CLI，用于把 `allure-results` 渲染成可查看的报告页面。

当前服务器上已经安装了 `allure-pytest`，因此 `pytest --alluredir=allure-results` 能正常生成结果；但系统没有安装 Allure CLI，所以 `allure serve` 命令不存在。

### 解决方法
当前阶段不在服务器上补装 Allure CLI，而是采用更贴近后续 Jenkins 集成的做法：

先安装 Python 测试依赖：

```bash
pip install -U pytest allure-pytest
```

安装后可用下面的方式确认：

```bash
python -m pytest --version
```

如果输出中能看到 `pytest` 版本，并且插件列表里包含 `allure-pytest`，说明 Python 侧已经安装完成。

然后执行测试并生成 Allure 结果文件：

```bash
python -m pytest tests/test_health.py tests/test_runs.py --alluredir=allure-results
```

保留 `allure-results` 目录即可，不要求在这台服务器上执行：

```bash
allure serve allure-results
```

后续由 Jenkins 安装 Allure 插件并消费 `allure-results` 生成报告页面。

### 后续注意
1. 后续文档中应明确区分“生成 Allure 结果文件”和“本机直接打开 Allure 报告”是两步不同的能力。
2. 如果服务器仅承担测试执行职责，只需保证 `allure-pytest` 可用并产出 `allure-results`。
3. 只有在确实需要本机本地预览报告时，才考虑额外安装 Allure CLI。
4. `pip install allure` 不是 pytest 场景下的正确安装方式；Python 侧应安装的是 `allure-pytest`。
5. 如果当前虚拟环境里还没有 `pytest`，应优先执行 `pip install -U pytest allure-pytest`，而不是只安装 `allure-pytest`。
