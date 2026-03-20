from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "lab-notebook-api"
    app_env: str = "dev"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api"

    secret_key: str = "change_me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/lab_notebook"

    storage_type: str = "local"
    upload_dir: str = "./uploads"

    llm_provider: str = "local"
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    llm_timeout_seconds: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
