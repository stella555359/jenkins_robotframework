# scripts

这里放被 Jenkins Pipeline 调用的 helper 脚本骨架。

建议后续逐步收口的脚本包括：

- `prepare_workspace.*`
- `checkout_sources.*`
- `materialize_workflow_request.*`
- `build_robot_command.*`
- `post_run_callback.*`

当前已落地：

- `build_robot_command.py`
	- 从 `testline + robotcase_path + workspace` 构建 `python -m robot ...` 命令计划
- `materialize_run_request.py`
	- 把 `platform-api` run detail 或 ad-hoc 输入物化成稳定的 internal robot request
- `checkout_sources.py`
	- 为 `robotws` 和 `testline_configuration` 生成 checkout plan，并承接 repo URL / branch / credentials 约定
- `prepare_taf_environment.py`
	- 生成 `TAF install / reuse` 所需的 Python 环境准备计划
- `post_run_callback.py`
	- 生成并可选回传 Jenkins callback payload，支持 retry 与 fallback 文件落地

这层是最适合承接下面这类转换的地方：

```text
workflow_spec -> request.json
robotcase_path -> robot command
result/artifacts -> callback payload
```

这一层应该保持可测试，不把关键 JSON 拼装逻辑全埋进 Jenkinsfile / Groovy 里。
