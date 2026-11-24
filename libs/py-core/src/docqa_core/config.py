"""Application settings loaded from environment variables (prefix ``DOCQA_``)."""

from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed runtime configuration for all docQA services."""

    model_config = SettingsConfigDict(env_prefix="DOCQA_", env_file=".env", extra="ignore")

    env: Literal["local", "dev", "staging", "prod"] = "local"
    service_name: str = "docqa"
    log_level: str = "INFO"
    log_json: bool = True
    database_url: str = "postgresql+psycopg://docqa:docqa@localhost:5432/docqa"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: SecretStr = SecretStr("minioadmin")
    s3_bucket_raw: str = "docqa-raw"
    temporal_address: str = "localhost:7233"
    temporal_namespace: str = "default"
    temporal_task_queue: str = "ingestion"
    otel_enabled: bool = False
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"


@lru_cache
def get_settings() -> Settings:
    """Return the cached process-wide settings."""
    return Settings()
