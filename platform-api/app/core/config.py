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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
