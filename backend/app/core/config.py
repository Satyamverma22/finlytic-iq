# app/core/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    database_url: str

    # Redis
    redis_url: str

    # Auth (used starting Phase 2, but declared now so .env stays the single source of truth)
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # AI / Storage (Phase 6+, optional for now)
    llm_provider: str = ""
    llm_api_key: str = ""
    embedding_provider: str = ""
    ocr_provider: str = ""
    storage_endpoint: str = ""
    storage_bucket: str = ""

    model_config = SettingsConfigDict(
    env_file="../.env",
    env_file_encoding="utf-8",
    case_sensitive=False,
    extra="ignore",
    )


settings = Settings()