"""Application configuration for the Fair-AI Guardian backend."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    app_name: str = "Fair-AI Guardian Platform"
    app_version: str = "1.0.0"
    api_prefix: str = "/api/v1"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    mongo_uri: str = Field(..., alias="MONGO_URI")
    mongo_database: str = Field("fair_ai_guardian", alias="MONGO_DATABASE")
    redis_url: str | None = Field(None, alias="REDIS_URL")

    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    model_artifacts_dir: Path = Field(
        default=BASE_DIR / "backend" / "artifacts" / "models",
        alias="MODEL_ARTIFACTS_DIR",
    )
    dataset_artifacts_dir: Path = Field(
        default=BASE_DIR / "backend" / "artifacts" / "datasets",
        alias="DATASET_ARTIFACTS_DIR",
    )
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    fairness_monitor_window: int = Field(200, alias="FAIRNESS_MONITOR_WINDOW")
    prediction_bias_threshold: float = Field(0.20, alias="PREDICTION_BIAS_THRESHOLD")

    mongo_max_pool_size: int = Field(50, alias="MONGO_MAX_POOL_SIZE")
    mongo_min_pool_size: int = Field(5, alias="MONGO_MIN_POOL_SIZE")
    mongo_server_selection_timeout_ms: int = Field(5000, alias="MONGO_SERVER_SELECTION_TIMEOUT_MS")
    mongo_connect_timeout_ms: int = Field(10000, alias="MONGO_CONNECT_TIMEOUT_MS")
    mongo_socket_timeout_ms: int = Field(30000, alias="MONGO_SOCKET_TIMEOUT_MS")

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret_key(cls, value: str) -> str:
        """Reject weak or placeholder JWT secrets."""

        placeholders = {"change_this_to_a_long_random_secret_in_production", "replace_with_secure_jwt_secret", ""}
        if value in placeholders or len(value) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters and not a placeholder.")
        return value

    @field_validator("mongo_max_pool_size", "mongo_min_pool_size", "mongo_server_selection_timeout_ms", "mongo_connect_timeout_ms", "mongo_socket_timeout_ms")
    @classmethod
    def validate_positive_ints(cls, value: int) -> int:
        """Ensure connection tuning values are positive."""

        if value <= 0:
            raise ValueError("Connection settings must be positive integers.")
        return value

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings instance."""

    settings = Settings()
    settings.model_artifacts_dir.mkdir(parents=True, exist_ok=True)
    settings.dataset_artifacts_dir.mkdir(parents=True, exist_ok=True)
    return settings
