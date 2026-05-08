# Step 15：Robot run trigger contract

## 目标

打通 B1 方案的后端边界：`POST /api/runs` 只负责创建 run，`POST /api/runs/{run_id}/trigger` 才负责触发 Jenkins。Portal 可以继续提供一个 **Run** 按钮，但后端保留清晰的 created / triggered / trigger_failed 状态。

## 本步新增

- `platform-api/app/core/config.py` 增加 Jenkins 触发配置：`JENKINS_BASE_URL`、`JENKINS_ROBOT_JOB_PATH`、`JENKINS_USERNAME`、`JENKINS_API_TOKEN`、`JENKINS_TRIGGER_TOKEN`、`PUBLIC_BASE_URL`。
- `platform-api/app/services/jenkins_service.py` 负责把 run detail 映射成 Jenkins `robot-execution` 的 `buildWithParameters` 参数。
- `platform-api/app/services/run_service.py` 增加 `trigger_run()`，只允许 `executor_type == "robot"` 且状态为 `created` 或 `trigger_failed` 的 run 触发。
- `platform-api/app/api/v1/router.py` 暴露 `POST /api/runs/{run_id}/trigger`。
- `platform-api/tests/test_runs.py` 使用 monkeypatch 覆盖 Jenkins 调用，验证成功触发和失败落库。

## 状态语义

```text
created         POST /api/runs 创建
triggered       /trigger 成功把任务送到 Jenkins queue
trigger_failed  /trigger 调 Jenkins 失败，可从 Portal 重试
running         Jenkins callback 可回写
passed/failed   Jenkins callback 最终回写
```

## Robot 参数契约

后端会传给 Jenkins：

```text
RUN_ID
TESTLINE
ROBOTCASE_PATH
CASE_NAME
ROBOT_SELECTED_TESTS
ROBOT_VARIABLES_JSON
PLATFORM_API_BASE_URL
PYTHON_ENV_ROOT
ROBOTWS_ROOT
TESTLINE_VARIABLES_PATH
ROBOTWS_REPO_URL_OVERRIDE
ROBOTWS_GIT_REF
ROBOTWS_CREDENTIALS_ID_OVERRIDE
TESTLINE_CONFIGURATION_REPO_URL_OVERRIDE
TESTLINE_CONFIGURATION_GIT_REF
TESTLINE_CONFIGURATION_CREDENTIALS_ID_OVERRIDE
ARTIFACT_LABEL
RETRY_INDEX
ROBOT_LOG_LEVEL
```

这些字段与 `jenkins-integration/pipelines/robot-execution.Jenkinsfile` 的参数保持一致。`build` 会写入 `ROBOT_VARIABLES_JSON.BUILD`，便于 Robot 侧按变量使用。

## 验证命令

```powershell
cd C:\TA\jenkins_robotframework\platform-api
python -m pytest tests\test_runs.py
```

手工 smoke：

```powershell
$body = @{
  testline = "T813"
  robotcase_path = "testsuite/Hangzhou/RRM/example.robot"
  executor_type = "robot"
  metadata = @{
    case_name = "Attach Smoke"
    selected_tests = @("Attach UE")
    robot_variables = @{ AF_PATH = "C:\TA\af" }
  }
} | ConvertTo-Json -Depth 8

$created = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/runs -Body $body -ContentType "application/json"
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/runs/$($created.run_id)/trigger"
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/api/runs/$($created.run_id)"
```
