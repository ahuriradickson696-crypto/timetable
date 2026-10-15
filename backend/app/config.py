"""Application configuration loaded from environment."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # App
    APP_NAME: str = "AVIU Timetable"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Database
    DATABASE_URL: str = "sqlite:///./aviu_timetable.db"

    # CORS (comma-separated string)
    BACKEND_CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # First admin
    FIRST_ADMIN_EMAIL: str = "admin@aviu.ac.ug"
    FIRST_ADMIN_PASSWORD: str = "admin123"
    FIRST_ADMIN_NAME: str = "System Administrator"

    # Solver
    SOLVER_TIME_LIMIT_SECONDS: int = 300
    SOLVER_NUM_WORKERS: int = 4
    SOLVER_RANDOM_SEED: int = 42

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.BACKEND_CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
