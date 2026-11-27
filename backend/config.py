from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App settings. Override any value with an environment variable or a `.env` file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:1.5b"
    # Max seconds to wait for a full model reply before giving up (returns 504).
    OLLAMA_TIMEOUT: float = Field(default=120.0, gt=0)
    # Default grade when a request doesn't send one (Lower Primary: 1-3).
    GRADE_LEVEL: int = Field(default=2, ge=1, le=3)
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    # Local SQLite file for learners and progress. Never leaves the device.
    DATABASE_PATH: Path = Path(__file__).resolve().parent / "data" / "math_tutor.db"
    # The built web app (`npm run build`). When it exists, FastAPI serves it at `/`,
    # so the whole tutor runs as one process. See `make start`.
    FRONTEND_DIST: Path = Path(__file__).resolve().parent.parent / "frontend" / "dist"
    # Time zone for counting "different days" in the mastery rule.
    TIMEZONE: str = "Africa/Nairobi"

    @field_validator("TIMEZONE")
    @classmethod
    def _known_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError(f"Unknown time zone: {value!r} (example: Africa/Nairobi)") from None
        return value


settings = Settings()
