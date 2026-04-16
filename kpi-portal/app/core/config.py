from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "KPI Portal"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8001

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
