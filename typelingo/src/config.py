from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "TypeLingo"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/typelingo"
    redis_url: str = "redis://localhost:6379/0"

    # Required — no default. App fails fast if SECRET_KEY is not set.
    secret_key: str

    access_token_expire_minutes: int = 1440  # 24 h — dev default
    refresh_token_expire_days: int = 7

    cors_origins: list[str] = ["http://localhost:3000"]

    # Optional — LLM features are disabled when not configured.
    groq_api_key: str | None = None
    groq_model_primary: str = "llama-3.3-70b-versatile"
    groq_model_fallback: str = "llama-3.1-8b-instant"


settings = Settings()
