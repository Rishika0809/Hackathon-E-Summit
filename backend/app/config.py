from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Autonomous Pothole Intelligence System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql://pothole_user:pothole_pass@localhost:5432/pothole_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # ML Model
    MODEL_PATH: str = "ml/models/yolov8_pothole.pt"
    MODEL_CONFIDENCE: float = 0.5
    MODEL_IOU: float = 0.45

    # Storage
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB

    # Government Portal (mock)
    PG_PORTAL_URL: str = "https://pgportal.gov.in/api"
    PG_PORTAL_API_KEY: str = "mock_api_key"

    # Weather API
    WEATHER_API_KEY: str = "mock_weather_key"
    WEATHER_API_URL: str = "https://api.openweathermap.org/data/2.5"

    # Escalation Timeouts (days)
    FIRST_ESCALATION_DAYS: int = 7
    SECOND_ESCALATION_DAYS: int = 14
    PUBLIC_FLAG_DAYS: int = 30

    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8080"]

    model_config = {"env_file": ".env", "extra": "allow"}


settings = Settings()
