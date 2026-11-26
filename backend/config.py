from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App settings. Override any value with an environment variable or a `.env` file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:1.5b"
    GRADE_LEVEL: int = 2
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]


settings = Settings()
