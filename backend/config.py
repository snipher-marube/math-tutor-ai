from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:1.5b"
    GRADE_LEVEL: int = 2

    class Config:
        env_file = '.env'

settings = Settings()