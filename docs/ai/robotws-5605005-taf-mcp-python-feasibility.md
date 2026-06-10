# RobotWS 5605005 Testcase TAF MCP Analysis

## 1. 分析目标

本文分析 Robot Framework testcase:

`C:\TA\robotws\testsuite\Hangzhou\RRM\RAN_PZ_HAZ_34\None_Feature_SG6\TMO_E2E_Reproduction_CRT.robot`

目标 testcase:

`5605005_E2E_Rep_005_Concurrent PS-BWP swtich and scell addtion`

分析目标：

- 读懂 testcase 的执行步骤和资源调用链。
- 结合 TAF MCP Server 查询结果，标出每一步背后涉及的 UTE TAF library。
- 判断是否可以用纯 Python 结合 TAF API 重写这个 Robot case。
- 记录后续如果要改写 Python 版本，需要补齐哪些信息。

## 2. Robot Testcase 本体

目标 testcase 在原始 Robot 文件中的主流程很短，核心步骤如下：

```robot
5605005_E2E_Rep_005_Concurrent PS-BWP swtich and scell addtion
    [Documentation]    Author:stella.lin@nokia-sbell.com
    ...       EXECUTION TESTLINE: TL073,TL284,TL282
    [Tags]     T080    T073   T813
    [Setup]    SetUp.TMO Case Common SetUp    ue_index=${REPCASE_5605005_CHOOSED_UE['${tl_prefix}']}
    ...     is_commission_for_first_gnb=${True}
    #####-----testline precondition----####
    Reproduce_5605005.PA Value Setting
    Connect to gnb coam via ssl    connection=GNB_OAM    gnb_index=0
    Change status for parameter cellBarred on GNB    exp_status=notBarred    list_cell_ids=${PCELL_INDEX}
    ...    connection=GNB_OAM    timeout=300
    ${test_model_description}    Set Variable If    '${tl_prefix}'=='T073'    8UE_DL_SFTP
    ...                                             '${tl_prefix}'=='T080'    7UE_DL_SFTP
    ...                                             '${tl_prefix}'=='T813'    7UE_DL_Burst
    #####-----generate kpi report----####
    ${report_timestamps}    Run Keyword If   '${tl_prefix}'=='T073' or '${tl_prefix}'=='T080'
    ...    T080.KPI Test With DL SFTP
    ...    ELSE IF    '${tl_prefix}'=='T813'    T813.KPI Test With DL Burst Traffic
    Should Be True    ${report_timestamps}!=${None}    msg=Get Report Timestamps Failed.
    ${kpi_report_file}    Compass.KPI Generate And Upload To Remote Server
    ...    report_timestamps_list=${report_timestamps}    report_parsed_duration=30    test_comments=${test_model_description}
    Should End With    ${kpi_report_file}    xlsx    msg=Get KPI Merged Results Failed.
    [Teardown]    Run Keywords    Run Keyword And Continue On Failure
    ...    TMO_Common_Case_Teardown    ue_index=${REPCASE_5605005_CHOOSED_UE['${tl_prefix}']}
    ...    AND    csn.reset_cache
```

主流程可以理解为：

1. 做 TMO case setup，并按测试线选择 UE index。
2. 按测试线和 UE index 设置 PA/attenuator，使 PCell/SCell 的射频条件符合 testcase。
3. 连接 gNB COAM，并把目标 PCell 的 `cellBarred` 设置为 `notBarred`。
4. 根据 `tl_prefix` 选择压测模型：
   - `T073` / `T080`: 多 UE DL SFTP。
   - `T813`: 7 UE DL burst traffic。
5. 从压测步骤返回 KPI 统计时间窗。
6. 用 Compass 生成并上传 KPI xlsx 报告。
7. 做 case teardown，并清理 CSN cache。

## 3. Resource 和 Library 入口

目标 Robot 文件直接引用：

- `testsuite/Hangzhou/resources/RAN_PZ_HAZ_34/lines/SG6/TMO/TMO_common_keywords.robot`
- `taf/rfrl/procedures/SISO/test_models/etsi/resources/Test_Model.robot`
- `taf/rfrl/procedures/resources/robot/common_setups_and_teardowns.robot`
- `testsuite/Hangzhou/resources/RAN_PZ_HAZ_34/robot/siso_common_case/cases/5G/5G_Setup_And_Teardown.robot`

其中 `TMO_common_keywords.robot` 又继续引入：

- `lines/SG6/Resources.robot`
- `TMO_Common_Setup_And_Teardown.robot`
- `TMO_common_keywords_part_one.robot` 到 `part_five.robot`
- `TMO_Reproduce_Case_Common.robot`
- `TMO_KPI_Report_Case_Common.robot`
- `lines/SG6/PM_counter/PM_common_keywords_via_pandas.robot`
- 多个 UE、CA、Logs、PM counter、Alarm 和 local Python helper。

所以这个 testcase 不是一个单层 Robot case，它是一个以 Robot 为入口、由很多本地 resource keyword 和 TAF library 共同组成的场景编排。

## 4. 步骤详情和底层 TAF 库

### 4.1 Case Setup

Robot step:

```robot
[Setup]    SetUp.TMO Case Common SetUp
...    ue_index=${REPCASE_5605005_CHOOSED_UE['${tl_prefix}']}
...    is_commission_for_first_gnb=${True}
```

作用：

- 根据 `tl_prefix` 选择本 testcase 使用的 UE index。
- 准备 TMO case 环境。
- 按参数对 first gNB 做 commission / precondition。
- 创建 case log path、准备连接、清理环境、保证 gNB/cell/UE 处于可测状态。

涉及资源：

- `TMO_Common_Setup_And_Teardown.robot`
- `5G_Setup_And_Teardown.robot`
- `common_setups_and_teardowns.robot`
- `TMO_Data.py`

底层 TAF/UTE 方向：

- `taf.sbts.oam.coam.admin`: gNB COAM 连接和状态读取。
- `taf.gnb.oam.commissioning`: gNB commissioning。
- `taf.config.testline`: 读取 `${tl}` 测试线对象。
- `taf.transport.ssh`: 连接 test PC / gNB common unit 执行清理或准备命令。
- `taf.ue.*` 或本地 `power_ue` resource: UE 准备。

纯 Python 转换难点：

- `SetUp.TMO Case Common SetUp` 是本地 Robot orchestration，不是单个 TAF library API。
- 纯 Python 需要先展开这个 keyword，再决定哪些步骤必须保留，哪些可以复用已有 Python helper。

### 4.2 PA Value Setting

Robot step:

```robot
Reproduce_5605005.PA Value Setting
```

关键定义在：

`C:\TA\robotws\testsuite\Hangzhou\resources\RAN_PZ_HAZ_34\lines\SG6\TMO\TMO_Reproduce_Case_Common.robot`

逻辑：

- `T080`: 调用 `Modify PA Value Setting For Required RU`，修改 RU `0`, `3`, `6`。
- `T284`: 修改 RU `0`, `1`, `2`。
- `T073`: 调用 `Reproduce_5605005_TL073.PA Value Setting`。
- `T813`: 修改 RU `0`, `3`, `6`，其中 RU `0` 使用 `pa_off_value=50`。

`Modify PA Value Setting For Required RU` 的底层流程：

1. 根据 `modify_ru_id` 和 `ue_index` 从 `${tl_prefix}_PA_VALUE_MAPPING` 中找到对应 attenuator id、PA port 和目标 value。
2. 调用 `Modify Attenuation Vaule`。
3. `Modify Attenuation Vaule` 调用：
   - `attenuator.setup_attenuator`
   - `attenuator.set_ports_attenuation`
   - `attenuator.read_ports_attenuation`
4. 读取后的 attenuation values 必须与设置值一致，否则 fail。

`T073` 的特殊逻辑：

- `Set Maritix PA Port` 使用 matrix PA port，如 `A1B5`, `A2B6` 等。
- 调用：
  - `attenuator.setup_attenuator    attenuator=${tl.attenuators[${attenuator_index}]}    alias=tp`
  - `attenuator.set_attenuation    port=${port}    value=${value}    attenuator_device=tp`
- 另外对 RU `7` 调用 `Modify PA Value Setting For Required RU`。

TAF MCP 查询确认：

- Library: `taf.hw.rf_attenuator`
- `setup_attenuator`: 准备指定 attenuator，可使用 testline attenuator object，或用 `ip_addr`, `port`, `attenuation_port_numbers`, `vendor`, `model` 等参数创建连接。
- `set_ports_attenuation`: 多端口设置 attenuation，参数包括 `ports`, `values`, `confirm`, `attenuator_device`。
- `read_ports_attenuation`: 读取多个 port 当前 attenuation，用于确认设置成功。
- `set_attenuation`: 单端口设置 attenuation，`port` 可为整数，也可为 testline attenuation port 对象；value 支持 int/float 或类似 `20dB` 的字符串。

纯 Python 可行性：

- 可行。
- Python 可以直接 import `taf.hw.rf_attenuator`，按 Robot 中的 `${tl_prefix}_PA_VALUE_MAPPING` 生成 `ports` / `values`。
- 关键不是 TAF API，而是要能在 Python 中加载同一份 testline config 和同一份 PA mapping 数据。

### 4.3 连接 gNB COAM

Robot step:

```robot
Connect to gnb coam via ssl    connection=GNB_OAM    gnb_index=0
```

关键定义在：

`C:\TA\robotws\testsuite\Hangzhou\resources\RAN_PZ_HAZ_34\robot\coam_gnb_classical.robot`

流程：

1. 从 `${tl.gnbs[gnb_index].cu.oam_ssh_connection_details.addr}` 取 gNB host。
2. 从 `${tl.gnbs[gnb_index].cu.oam_http_connection_details}` 取 username/password。
3. 先调用 `coam.get_sw_release_name connection=${connection}` 判断连接是否已存在。
4. 如果连接不存在，再调用 `coam.connect_to`：
   - `bts_host`
   - `bts_port=443`
   - `username`
   - `password`
   - `name=${connection}`

TAF MCP 查询确认：

- Library: `taf.sbts.oam.coam.admin`
- `connect_to`: 连接 Node B / gNB Admin API，支持 `bts_host`, `bts_port`, `username`, `password`, `use_ssl`, `name`, `release`, `timeout` 等参数。
- `get_sw_release_name`: 从 M-plane/OAM 获取当前软件 release name，也可作为连接可用性的轻量检查。

纯 Python 可行性：

- 可行。
- Python 中可直接使用 `taf.sbts.oam.coam.admin.connect_to()` 建立连接。
- 需要注意 Robot 用的是 alias/name 模式；Python 可以保存返回的 `AdminConnection` 对象，或者继续使用连接 name。

### 4.4 设置 `cellBarred=notBarred`

Robot step:

```robot
Change status for parameter cellBarred on GNB
...    exp_status=notBarred
...    list_cell_ids=${PCELL_INDEX}
...    connection=GNB_OAM
...    timeout=300
```

关键定义在：

`C:\TA\robotws\testsuite\Hangzhou\resources\RAN_PZ_HAZ_34\robot\coam_gnb_classical.robot`

流程：

1. 判断是否为 cloud BTS。
2. 获取 cell index 与 gNB cell identity 的映射：
   - cloud: `cloud_gnb.get_relation_mapping_between_cell_and_others`
   - classical: `get_relation_mapping_between_cell_index_and_other_ids`
3. 如果 `list_cell_ids=all`，则操作所有 cells；本 case 只传入 `${PCELL_INDEX}`。
4. 构造参数更新列表：
   - 目标 cells: `MRBTS-.../NRBTS-.../NRCELL-${cell_index}` 的 `cellBarred=notBarred`
   - 其他 cells: 设置为相反状态 `barred`
5. classical gNB 场景下调用：
   - `COAM Update several parameters via rest api`

底层 TAF/UTE 方向：

- `taf.sbts.oam.coam.admin`: COAM 连接和 Admin API 操作。
- 本地 helper `coam_parameter.py` / `coam_gnb_classical.py`: distName 构造、mapping、参数更新封装。
- cloud 场景可能涉及 `taf.gnb.oam.coam.vdu`。

TAF MCP 查询结果补充：

- MCP 没有直接返回本地 keyword `COAM Update several parameters via rest api` 的完整文档，因为它是 robotws 本地 resource keyword，不是独立 TAF package API。
- 但 COAM 连接、release 检查、Admin API 基础能力来自 `taf.sbts.oam.coam.admin`。

纯 Python 可行性：

- 可行，但需要复用或重写 robotws 中的 mapping 和参数更新 helper。
- 如果只直接调用 TAF COAM API，仍然需要自己生成 `dist_name / parameter / value` 列表。

### 4.5 根据测试线选择业务流

Robot step:

```robot
${test_model_description}    Set Variable If
...    '${tl_prefix}'=='T073'    8UE_DL_SFTP
...    '${tl_prefix}'=='T080'    7UE_DL_SFTP
...    '${tl_prefix}'=='T813'    7UE_DL_Burst
```

作用：

- `T073`: 8 UE DL SFTP。
- `T080`: 7 UE DL SFTP。
- `T813`: 7 UE DL Burst。
- 这个 description 最终会写入 Compass KPI report。

纯 Python 可行性：

- 可行。
- 这只是分支选择逻辑。

### 4.6 T073 / T080: DL SFTP KPI Test

Robot step:

```robot
T080.KPI Test With DL SFTP
```

关键定义在：

`C:\TA\robotws\testsuite\Hangzhou\resources\RAN_PZ_HAZ_34\lines\SG6\TMO\TMO_Reproduce_Case_Common.robot`

流程：

1. 根据 `tl_prefix` 选择多 UE prepare index：
   - `T073`: UE `15` 到 `22`
   - `T080`: UE `19` 到 `26`
2. 调用 `Perform Mutli-UE Prepare`。
3. 设置总 sleep 时间：
   - `T073`: 10800 秒
   - `T080`: 12600 秒
4. 连接 gNB COAM，并再次将 NRCELL `301` 设置为 `notBarred`。
5. 关闭 COAM 连接。
6. 根据 `tl_prefix` 选择 attach UE index：
   - `T073`: UE `15` 到 `22`
   - `T080`: UE `19`, `20`, `22`, `23`, `24`, `25`, `26`
7. 开始 UE log。
8. 执行多 UE attach。
9. 导入 test plan。
10. 等待 10 分钟。
11. 记录 KPI 起始时间。
12. 采集第一段 30 分钟 syslog 并检查 ERR/WRN。
13. 根据总体 sleep 时间补齐等待时间。
14. 再采集第二段 30 分钟 syslog 并检查 ERR/WRN。
15. 记录 KPI 结束时间，返回 `report_timestamps`。
16. 停止 UE log，并断开多 UE。

涉及底层库：

- UE 操作：
  - 本地 Robot keywords: `Perform Mutli-UE Prepare`, `Perform Mutli-UE Attach`, `Perform Mutli-UE Start Log`, `Perform Mutli-UE Stop Log`, `Perform Mutli-UE Disconnect`
  - TAF/UTE 方向: `taf.ue.*`，例如 MCP 查询到 `taf.ue.android`, `taf.ue.at`, `taf.ue.iphone`, `taf.ue.fastmile` 均有 attach/detach 相关 API。
- COAM 操作：
  - `taf.sbts.oam.coam.admin`
- syslog:
  - 本地 keywords: `Get Syslog Formatted Time`, `Get syslog file with duration and Compress File`, `Check ERR Or WRN From Syslog`
  - TAF/UTE 方向: `taf.transport.ssh`, gNB log collector/local syslog parser。
- KPI 时间窗:
  - Robot `DateTime` library。

纯 Python 可行性：

- 中等可行。
- UE 多设备准备和 attach/disconnect 是最大难点，因为这里依赖 robotws 的多 UE resource、具体 UE 类型、UE index、Spark/DingLi/Power UE 的本地封装。
- 如果只用 TAF MCP 提供的 `taf.ue.*` API，需要重新映射这些本地 UE index 到 TAF UE aliases/capabilities。

### 4.7 T813: DL Burst Traffic KPI Test

Robot step:

```robot
T813.KPI Test With DL Burst Traffic
```

关键定义在：

`C:\TA\robotws\testsuite\Hangzhou\resources\RAN_PZ_HAZ_34\lines\SG6\TMO\TMO_Reproduce_Case_Common.robot`

流程：

1. 获取 UE0 类型：
   - `translate_power_ue_type_from_testline    ue_index=0`
2. 准备 UE0：
   - `power_ue.Prepare UE    ue_index=0    ue_type=${ue0_type}    get_spark_license=False`
3. 准备 DingLi UE group：
   - `DingLi_Client.UE Prepare    ue_index=4    ues_index=${0,1,2,3,4,5}`
4. 在 attach 前启动 DL burst UDP traffic：
   - `Reproduce_5605005.Start Brust DL UDP Traffic`
   - script path: `/home/vrf4_sg6/5605005/${tl_prefix}/7UE_DL_Burst/`
5. DingLi UE power off/on，不获取 UE IP。
6. UE0 attach：
   - `power_ue.UE Attach`
7. 等待 5 分钟。
8. 执行 `DL.Multi UE Burst Traffic`，返回 burst DL KPI 时间窗。
9. teardown:
   - UE0 detach。
   - DingLi UE group detach。

涉及底层库：

- `taf.ue.*`: UE attach/detach 能力。
- 本地 `power_ue` resource: 根据测试线 UE 类型选择具体 UE 操作。
- DingLi 客户端本地 resource: 批量 UE 准备、power cycle、detach。
- `taf.transport.ssh`: 执行 remote shell script 或控制 test PC。
- 本地 shell script: `/home/vrf4_sg6/5605005/${tl_prefix}/7UE_DL_Burst/`。

纯 Python 可行性：

- 可行但工作量较高。
- 需要把 DingLi client resource 和 burst traffic shell script orchestration 搬到 Python。
- TAF MCP 可以帮助查 `taf.ue.*` 和 SSH/API 能力，但不会自动知道 robotws 本地 DingLi resource 的业务语义。

### 4.8 Compass KPI Report 生成和上传

Robot step:

```robot
${kpi_report_file}    Compass.KPI Generate And Upload To Remote Server
...    report_timestamps_list=${report_timestamps}
...    report_parsed_duration=30
...    test_comments=${test_model_description}
Should End With    ${kpi_report_file}    xlsx
```

关键定义在：

`C:\TA\robotws\testsuite\Hangzhou\resources\RAN_PZ_HAZ_34\lines\SG6\PM_counter\PM_common_keywords_via_pandas.robot`

流程：

1. 如果 `report_parsed_duration` 不为 `None`，先把时间窗拆分成 30 秒粒度区间。
2. 等待 Compass/Scout KPI 数据完成入库。
3. 对每个时间窗调用 `Compass.Generate KPI Report`。
4. 收集所有 report id。
5. 调用 `Compass.Save Compare KPI Report` 合并/比较 KPI report。
6. 调用 `Compass.Append Result To Excel` 补充结果。
7. 调用 `Compass.Upload Result To Remote Server` 上传结果。
8. 返回 output xlsx path。

底层实现方向：

- `PM_common_keywords_via_pandas.robot`
- `PM_counter/KPI_report_with_pandas.py`
- Python `requests` 调用 Compass/Scout HTTP 接口。
- Python/pandas/openpyxl 处理 xlsx。

纯 Python 可行性：

- 高可行。
- 这一段本身已经大量由本地 Python helper 实现，纯 Python 重写时应优先复用 `KPI_report_with_pandas.py` 的函数，而不是重新造 report 逻辑。

### 4.9 Teardown

Robot step:

```robot
[Teardown]    Run Keywords    Run Keyword And Continue On Failure
...    TMO_Common_Case_Teardown    ue_index=${REPCASE_5605005_CHOOSED_UE['${tl_prefix}']}
...    AND    csn.reset_cache
```

作用：

- 停止 UE、traffic、log collector。
- 保存必要 snapshot/log。
- 断开 COAM/SSH/UE 连接。
- 清理 CSN cache。

涉及底层库：

- `taf.transport.ssh`: `csn.reset_cache`、远端命令、断连。
- `taf.sbts.oam.coam.admin`: snapshot/teardown。
- `taf.ue.*` / 本地 `power_ue` / DingLi resource: UE detach 和恢复。
- `taf.collectors.*`: 如果业务流中启动了 collector，需要 stop/collect/teardown。

纯 Python 可行性：

- 可行，但必须用 `try/finally` 明确表达清理顺序。
- Robot 的 `Run Keyword And Continue On Failure` 容错语义在 Python 中要显式捕获异常并记录。

## 5. MCP 查询到的关键 TAF API

### 5.1 PA / Attenuator

Library:

- `taf.hw.rf_attenuator`

Functions:

- `setup_attenuator`
  - 用 attenuator object 或 `ip_addr`, `port`, `attenuation_port_numbers`, `vendor`, `model` 等参数准备设备。
  - 返回 configured attenuator object。
- `set_ports_attenuation`
  - 多 port 设置 attenuation。
  - 参数包括 `ports`, `values`, `confirm`, `attenuator_device`。
  - `confirm=True` 时会读回并校验设置值。
- `read_ports_attenuation`
  - 读取多个 port 的 attenuation。
- `set_attenuation`
  - 单 port 设置 attenuation。
  - 适合 `Set Maritix PA Port` 这种 matrix port 场景。

### 5.2 gNB COAM

Library:

- `taf.sbts.oam.coam.admin`

Functions:

- `connect_to`
  - 连接 gNB Admin API。
  - 参数包括 `bts_host`, `bts_port`, `username`, `password`, `use_ssl`, `name`, `release`, `timeout`。
- `get_sw_release_name`
  - 从 M-plane/OAM 读取当前 software release name。
  - 当前 Robot keyword 用它判断连接 alias 是否已经可用。

### 5.3 SSH / Remote Command

Library:

- `taf.transport.ssh`

Functions from MCP:

- `Execute`
  - 在远端连接上执行命令并返回输出。
- `Await Execution End`
  - 等待上一个命令结束。
- `Execution Ended`
  - 判断上一个命令是否结束。

Robot 中对应使用：

- `csn.Execute`
- `csn.execute`
- `csn.send command`
- `ssh.connect_to`
- `ssh.disconnect`

### 5.4 gNB Wireshark / tcpdump Collector

Libraries:

- `taf.collectors.tcpdump`
- `taf.collectors.core`

Functions from MCP:

- `tcpdump.create_tcpdump_collector`
  - 创建 tcpdump collector。
  - 支持 `name`, `options`, `executor`, `container`, `target_file_name`, `start_timeout`, `stop_timeout` 等。
- `core.setup_collectors`
  - 设置 collector。
- `core.start_collectors`
  - 启动 collector。
- `core.stop_collectors`
  - 停止 collector。
- `core.collect_collectors`
  - 收集 collector 产生的文件到本地目录。

Robot 中对应：

- `Start Container Capture Wireshark Log`
- `Start CP-IF Log Collection`
- `Start CP-RT Log Collection`
- `Stop Container Wireshark Log Collection`
- `Stop tcpdump log collection`

### 5.5 Pcap / Wireshark 解析

Library:

- `taf.analyzer.pcap`

Functions from MCP:

- `setup`
  - 使用 tshark display filter 初始化 pcap parser。
- `get_packets`
  - 根据 Wireshark filter 获取 packet 列表。
- `get_field_value`
  - 从过滤后的 packet 中提取字段值。
- `load_pcap_file`
  - 将 pcap 转为 pdml 并载入，MCP 标注为 deprecated，但兼容 `taf.ul.parser.pcap`。
- `get_field_value_by_xpath`
  - 通过 xpath 获取 pdml 字段值，MCP 标注为 deprecated，但兼容 `taf.ul.parser.pcap`。

Robot 中对应：

- `Get Attach Cell Index From Wireshark`
  - 用 `ngap.procedureCode == 15` 或 `f1ap.procedureCode == 5` 过滤 attach cell。
- `HO.Check A5A3 Measurement Report`
  - 检查 measurement report 中 source/target PCI。
- `HO.Check RRC Reconfigure And RRC Reconfigure Complete For Inter-gnb`
  - 检查 RRC Reconfiguration 和 RRC Reconfiguration Complete。
- `HO.Check RRC Reestablishment`
  - 检查不应发生 RRC Reestablishment。

### 5.6 UE Attach / Detach

Libraries from MCP search:

- `taf.ue.android`
- `taf.ue.at`
- `taf.ue.iphone`
- `taf.ue.fastmile`

Functions:

- `attach_ue`
- `detach_ue`
- `require_ue`

注意：

- 目标 Robot case 不是直接调用 `taf.ue`，而是通过 `power_ue.*`、`DingLi_Client.*`、`Perform Mutli-UE *` 等本地 resource 间接控制 UE。
- MCP 可以告诉我们 TAF UE 底层 API 形态，但不能自动替代 robotws 本地 UE 编排逻辑。

## 6. 纯 Python 实现可行性判断

结论：

纯 Python 实现是可行的，但不建议直接“一次性自动转换整个 Robot case”。更现实的方式是做一个 Python orchestrator，逐步替换 Robot keyword，并复用已有 robotws Python helper。

### 6.1 可以直接用 TAF Python API 替换的部分

- PA / attenuator 设置：
  - `taf.hw.rf_attenuator.setup_attenuator`
  - `set_ports_attenuation`
  - `read_ports_attenuation`
  - `set_attenuation`
- gNB COAM 连接：
  - `taf.sbts.oam.coam.admin.connect_to`
  - `get_sw_release_name`
- SSH remote command：
  - `taf.transport.ssh`
- tcpdump collector：
  - `taf.collectors.tcpdump.create_tcpdump_collector`
  - `taf.collectors.core.setup_collectors/start_collectors/stop_collectors/collect_collectors`
- pcap 解析：
  - `taf.analyzer.pcap.setup`
  - `get_packets`
  - `get_field_value`
  - `load_pcap_file`
  - `get_field_value_by_xpath`
- Compass KPI:
  - 可复用 `PM_counter/KPI_report_with_pandas.py` 中已有 Python HTTP/report 函数。

### 6.2 不能只靠 TAF MCP 自动完成的部分

- `${tl_prefix}_PA_VALUE_MAPPING` 的业务含义。
- `${REPCASE_5605005_CHOOSED_UE}`、`${PCELL_INDEX}`、`${tl}` testline object 的加载方式。
- `SetUp.TMO Case Common SetUp` 和 `TMO_Common_Case_Teardown` 的完整副作用。
- `power_ue.*` 的 UE 类型分发逻辑。
- `DingLi_Client.*` 的多 UE 操作。
- `Perform Mutli-UE Prepare/Attach/Disconnect` 的业务封装。
- `/home/vrf4_sg6/5605005/${tl_prefix}/7UE_DL_Burst/` 下 shell script 的输入输出约定。
- Compass/Scout 的账号、URL、template、report id 合并规则。

### 6.3 推荐转换策略

第一阶段：Python wrapper 复用 Robot 关键资产

- 保留现有 Robot case 作为 baseline。
- Python 只实现 PA setting、COAM connection、cellBarred update 这类 TAF API 清晰的步骤。
- UE 和 KPI report 暂时继续调用现有 resource 或 helper。

第二阶段：替换 traffic 和 UE lifecycle

- 将 `Perform Mutli-UE Prepare/Attach/Disconnect` 拆成 Python class。
- 对不同 UE 类型建立 adapter：
  - Android / AT / iPhone / DingLi / Spark / Power UE。
- 对 SFTP 和 Burst traffic 建立独立 traffic controller。

第三阶段：替换 report 和 validation

- 复用或封装 `KPI_report_with_pandas.py`。
- Python 统一返回：
  - `report_timestamps`
  - `kpi_report_file`
  - `syslog_file`
  - `pcap_file`
  - `validation_result`

第四阶段：Python testcase 产品化

- 加 `argparse` 支持 `--tl-prefix`, `--ue-index`, `--pcell-index`, `--dry-run`。
- 加 `try/finally` 做 teardown。
- 将 TAF MCP 查询到的 API 作为代码注释和维护依据。

## 7. 纯 Python 代码轮廓

下面是建议的 Python 结构，不是可直接运行版本。真正实现前，需要先确认 robotws 的 testline config 加载方式和本地 helper import path。

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Case5605005Config:
    tl_prefix: str
    ue_index: int
    pcell_index: int
    report_parsed_duration: int = 30


class PaService:
    def set_reproduce_5605005_pa(self, config: Case5605005Config) -> None:
        """Apply the same RU/PA mapping as Reproduce_5605005.PA Value Setting."""
        # Load ${tl_prefix}_PA_VALUE_MAPPING and call taf.hw.rf_attenuator.
        raise NotImplementedError


class CoamService:
    def connect_gnb(self, gnb_index: int = 0) -> Any:
        """Call taf.sbts.oam.coam.admin.connect_to."""
        raise NotImplementedError

    def set_cell_barred(self, connection: Any, pcell_index: int, exp_status: str) -> None:
        """Build NRCELL distNames and update cellBarred through COAM."""
        raise NotImplementedError


class TrafficService:
    def run_dl_sftp(self, config: Case5605005Config) -> list[list[str]]:
        """Python replacement for T080.KPI Test With DL SFTP."""
        raise NotImplementedError

    def run_dl_burst(self, config: Case5605005Config) -> list[list[str]]:
        """Python replacement for T813.KPI Test With DL Burst Traffic."""
        raise NotImplementedError


class CompassReportService:
    def generate_and_upload(
        self,
        report_timestamps: list[list[str]],
        test_comments: str,
        report_parsed_duration: int,
    ) -> Path:
        """Reuse KPI_report_with_pandas.py or existing Compass helper."""
        raise NotImplementedError


def run_case_5605005(config: Case5605005Config) -> Path:
    pa = PaService()
    coam = CoamService()
    traffic = TrafficService()
    compass = CompassReportService()

    try:
        pa.set_reproduce_5605005_pa(config)
        connection = coam.connect_gnb(gnb_index=0)
        coam.set_cell_barred(
            connection=connection,
            pcell_index=config.pcell_index,
            exp_status="notBarred",
        )

        if config.tl_prefix in {"T073", "T080"}:
            report_timestamps = traffic.run_dl_sftp(config)
            test_comments = "8UE_DL_SFTP" if config.tl_prefix == "T073" else "7UE_DL_SFTP"
        elif config.tl_prefix == "T813":
            report_timestamps = traffic.run_dl_burst(config)
            test_comments = "7UE_DL_Burst"
        else:
            raise ValueError(f"Unsupported tl_prefix: {config.tl_prefix}")

        if not report_timestamps:
            raise RuntimeError("Get Report Timestamps Failed")

        output = compass.generate_and_upload(
            report_timestamps=report_timestamps,
            report_parsed_duration=config.report_parsed_duration,
            test_comments=test_comments,
        )
        if output.suffix.lower() != ".xlsx":
            raise RuntimeError(f"Get KPI Merged Results Failed: {output}")
        return output
    finally:
        # Python must explicitly preserve Robot teardown behavior:
        # stop traffic, detach UE, stop collectors, save logs/snapshot, reset SSH cache.
        pass
```

## 8. 风险和注意点

- TAF MCP Server 只提供 TAF package/documentation knowledge，不包含 robotws 仓库所有本地 resource 的业务含义。
- 目标 Robot case 的业务逻辑大量在 robotws 本地 resource 中，不在 TAF MCP 文档里。
- 纯 Python 改写时，最容易漏掉的是 setup/teardown 的隐式副作用，例如恢复 PA、detach UE、停止 traffic、保存 syslog、保存 snapshot、清理 collector。
- PA mapping 和 UE mapping 必须以测试线真实配置为准，不能凭 MCP 猜测。
- SFTP/Burst traffic 与 Compass KPI report 都依赖外部系统和时间窗，建议保留 dry-run 和 step-by-step validation。
- `taf.analyzer.pcap.load_pcap_file` 和 `get_field_value_by_xpath` 在 MCP 文档中标注为 deprecated，但当前 Robot 仍在使用兼容方式；新 Python 版本可以优先评估 `taf.ul.parser.pcap`。

## 9. 验证建议

本次只做阅读和文档分析，没有在目标服务器运行测试。

建议先由用户在目标 TAF/robotws 环境做只读验证：

```powershell
cd C:\TA\robotws
python -m robot.libdoc testsuite/Hangzhou/resources/RAN_PZ_HAZ_34/lines/SG6/TMO/TMO_Reproduce_Case_Common.robot C:\TA\taf_mcp_practise\TMO_Reproduce_Case_Common_libdoc.html
python -m robot.libdoc testsuite/Hangzhou/resources/RAN_PZ_HAZ_34/lines/SG6/TMO/TMO_common_keywords.robot C:\TA\taf_mcp_practise\TMO_common_keywords_libdoc.html
```

期望结果：

- 生成两个 libdoc HTML。
- 可以在 HTML 中搜索：
  - `Reproduce_5605005.PA Value Setting`
  - `T080.KPI Test With DL SFTP`
  - `T813.KPI Test With DL Burst Traffic`
  - `Modify PA Value Setting For Required RU`

常见失败模式：

- `Importing library failed`: 当前 Python 环境没有安装 TAF/robotws 依赖。
- `Variable file not found`: 没有在 robotws 根目录执行，或 `PYTHONPATH` 不完整。
- `No keyword found`: resource import 链没有加载完整，需要补充 Robot `--pythonpath` 或使用真实 TAF virtualenv。

后续如果要验证纯 Python 能否调用底层 TAF API，建议先做最小 smoke test：

```powershell
python - <<'PY'
from taf.hw import rf_attenuator
from taf.sbts.oam.coam import admin
from taf.collectors import core, tcpdump
from taf.analyzer import pcap
print("TAF imports OK")
PY
```

期望结果：

- 输出 `TAF imports OK`。

常见失败模式：

- `ModuleNotFoundError: No module named 'taf'`: 当前环境不是 TAF virtualenv，或 TAF package 未安装。
- `ImportError` 指向某个子包：需要按 MCP 文档/Artifactory 指南补装对应 TAF package。

## 10. 学习记录

本步骤解决的问题：

- 把 `5605005_E2E_Rep_005_Concurrent PS-BWP swtich and scell addtion` 从一个短 Robot testcase 展开成可理解的业务流程。
- 明确了 Robot 本地 keyword 与 TAF MCP 可查询 library 之间的边界。
- 判断了纯 Python 改写的可行性和主要风险。

本步骤阅读的关键文件：

- `C:\TA\robotws\testsuite\Hangzhou\RRM\RAN_PZ_HAZ_34\None_Feature_SG6\TMO_E2E_Reproduction_CRT.robot`
- `C:\TA\robotws\testsuite\Hangzhou\resources\RAN_PZ_HAZ_34\lines\SG6\TMO\TMO_common_keywords.robot`
- `C:\TA\robotws\testsuite\Hangzhou\resources\RAN_PZ_HAZ_34\lines\SG6\TMO\TMO_Reproduce_Case_Common.robot`
- `C:\TA\robotws\testsuite\Hangzhou\resources\RAN_PZ_HAZ_34\robot\coam_gnb_classical.robot`
- `C:\TA\robotws\testsuite\Hangzhou\resources\RAN_PZ_HAZ_34\lines\SG6\Logs.robot`
- `C:\TA\robotws\testsuite\Hangzhou\resources\RAN_PZ_HAZ_34\robot\check_android_ue_l3_call_process.robot`
- `C:\TA\robotws\testsuite\Hangzhou\resources\RAN_PZ_HAZ_34\lines\SG6\TMO\TMO_common_keywords_part_four.robot`
- `C:\TA\robotws\testsuite\Hangzhou\resources\RAN_PZ_HAZ_34\lines\SG6\PM_counter\PM_common_keywords_via_pandas.robot`

MCP 查询确认的核心库：

- `taf.hw.rf_attenuator`
- `taf.sbts.oam.coam.admin`
- `taf.transport.ssh`
- `taf.collectors.tcpdump`
- `taf.collectors.core`
- `taf.analyzer.pcap`
- `taf.ue.android`
- `taf.ue.at`
- `taf.ue.iphone`
- `taf.ue.fastmile`

核心调用流：

1. Robot testcase 入口。
2. TMO setup。
3. PA/attenuator setting。
4. COAM connect。
5. `cellBarred` 参数更新。
6. SFTP/Burst traffic branch。
7. KPI timestamp collection。
8. Compass report generation and upload。
9. Teardown and cache cleanup。

关键字段：

- `${tl_prefix}`: 决定测试线分支。
- `${REPCASE_5605005_CHOOSED_UE}`: 决定 case 使用的 UE index。
- `${PCELL_INDEX}`: 决定需要 unbar 的 primary cell。
- `${tl_prefix}_PA_VALUE_MAPPING`: 决定 PA/attenuator port/value。
- `${report_timestamps}`: KPI 报告生成输入。
- `${test_model_description}`: 写入 Compass report 的测试模型说明。
- `${kpi_report_file}`: 最终 xlsx report path。

给用户的复盘问题：

- 目标是否只需要 Python 版 PA + COAM + cellBarred 最小练习，还是要完整替换 SFTP/Burst/Compass？
- Python 版本是否必须兼容 `T073/T080/T813` 三条测试线？
- `power_ue` 和 `DingLi_Client` 是否已有可直接 import 的 Python API？
- Compass/Scout report 是否允许 Python 直接调用当前 `KPI_report_with_pandas.py`？
- 纯 Python 版本是否需要保留 Robot 当前的所有 syslog、pcap、snapshot 证据收集？
