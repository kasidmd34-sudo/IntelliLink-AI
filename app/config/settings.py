from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # App Settings
    APP_NAME: str = "IntelliLink AI Engine"
    APP_ENV: str = "development"
    APP_PORT: int = 8000
    APP_HOST: str = "0.0.0.0"
    DEBUG: bool = True

    # Google GenAI / Gemini
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Directory Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "data" / "raw"
    PROCESSED_DIR: Path = BASE_DIR / "data" / "processed"
    SCHEDULE_DATA_PATH: Path = BASE_DIR / "data" / "schedules" / "sample_schedule.csv"
    MAX_UPLOAD_SIZE_MB: int = 25

    # Hybrid Matcher Weights
    WEIGHT_SEMANTIC: float = 0.50
    WEIGHT_FUZZY: float = 0.20
    WEIGHT_LOCATION: float = 0.15
    WEIGHT_DATE: float = 0.10
    WEIGHT_PROJECT: float = 0.05

    # Confidence Thresholds
    CONFIDENCE_HIGH_THRESHOLD: float = 0.90
    CONFIDENCE_MEDIUM_THRESHOLD: float = 0.70


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    settings.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    settings.SCHEDULE_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    return settings