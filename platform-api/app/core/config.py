from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Platform API"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    runs_db_path: str = "data/results/automation_platform.db"
    public_base_url: str = "http://127.0.0.1:8000"
    jenkins_base_url: str = ""
    jenkins_robot_job_path: str = "job/robot/job/robot-execution"
    jenkins_python_orchestrator_job_path: str = "job/CIT/job/KPI_Testing/job/SBTS26R1/job/7_5_UTE5G402T813"
    jenkins_username: str = ""
    jenkins_api_token: str = ""
    jenkins_trigger_token: str = ""
    jenkins_timeout_seconds: int = 30
    jenkins_insecure_tls: bool = False
    jenkins_callback_insecure_tls: bool = True
    ai_analysis_enabled: bool = True
    ai_analysis_model: str = "auto"
    ai_analysis_workspace: str = "."
    ai_analysis_max_evidence_bytes: int = 20000
    ai_analysis_worker_poll_seconds: int = 5
    cursor_api_base_url: str = "https://api.cursor.com"
    cursor_api_timeout_seconds: int = 60
    cursor_api_run_timeout_seconds: int = 600
    cursor_api_poll_seconds: int = 5
    cursor_api_use_proxy: bool = True
    cursor_api_insecure_tls: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
