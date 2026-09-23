import json
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DATABASE_URL: str = "sqlite:///./shiftguard.db"
    EDGE_DATABASE_URL: str = "sqlite:///./shiftguard.db"
    CLOUD_DATABASE_URL: str = "sqlite:///./shiftguard_cloud.db"
    CLOUD_SYNC_URL: str = "http://127.0.0.1:8000/api/sync/events"
    SYNC_BATCH_SIZE: int = 25
    SYNC_INTERVAL_SECONDS: float = 3.0
    SYNC_RETRY_LIMIT: int = 5
    SYNC_BACKOFF_BASE: float = 2.0
    CLOUD_ENABLED: bool = True
    ANOMALY_ARTIFACT_PATH: str = "backend/app/ml/anomaly/artifacts/shiftguard_anomaly_v1.joblib"
    ANOMALY_METADATA_PATH: str = "backend/app/ml/anomaly/artifacts/shiftguard_anomaly_v1.metadata.json"
    ANOMALY_MIN_OPERATOR_WINDOWS: int = 6
    ETA_ARTIFACT_PATH: str = "backend/app/ml/eta/artifacts/shiftguard_eta_v1.joblib"
    ETA_METADATA_PATH: str = "backend/app/ml/eta/artifacts/shiftguard_eta_v1.metadata.json"
    COPILOT_PROVIDER: str = "local"
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4.1-mini"
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]
    SERVICE_NAME: str = "shiftguard-edge"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
