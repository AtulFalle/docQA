"""Typed runtime configuration for all docQA services.

Sources, highest priority first:

1. Arguments passed to ``Settings(...)`` (tests).
2. Environment variables with the ``DOCQA_`` prefix. Nested fields use ``__``, for example
   ``DOCQA_PROVIDERS__LLM__NAME=fake``. Flat variables such as ``DOCQA_DATABASE_URL`` work as
   before.
3. The ``.env`` file.
4. The YAML file named by ``DOCQA_CONFIG_FILE``, if set, with ``${ENV}`` interpolation
   (see ``yaml_file.py``).
5. The defaults below.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, SecretStr, ValidationError
from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict

from docqa_core.config.yaml_file import load_yaml_config
from docqa_core.domain.errors import ConfigError

CONFIG_FILE_ENV = "DOCQA_CONFIG_FILE"


class ProviderSettings(BaseModel):
    """Which implementation backs one interface, and the parameters it is built with."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(default="fake", min_length=1)
    params: dict[str, JsonValue] = Field(default_factory=dict)


class ProvidersSettings(BaseModel):
    """Provider choice per interface. Every interface defaults to its fake implementation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    llm: ProviderSettings = Field(default_factory=ProviderSettings)
    embedder: ProviderSettings = Field(default_factory=ProviderSettings)
    vector_store: ProviderSettings = Field(default_factory=ProviderSettings)
    reranker: ProviderSettings = Field(default_factory=ProviderSettings)
    parser: ProviderSettings = Field(default_factory=ProviderSettings)
    chunker: ProviderSettings = Field(default_factory=ProviderSettings)


class Settings(BaseSettings):
    """Typed runtime configuration for all docQA services."""

    model_config = SettingsConfigDict(
        env_prefix="DOCQA_", env_file=".env", env_nested_delimiter="__", extra="ignore"
    )

    env: Literal["local", "dev", "staging", "prod"] = "local"
    service_name: str = "docqa"
    log_level: str = "INFO"
    log_json: bool = True
    database_url: str = "postgresql+psycopg://docqa:docqa@localhost:5432/docqa"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "rustfsadmin"
    s3_secret_key: SecretStr = SecretStr("rustfsadmin")
    s3_bucket_raw: str = "docqa-raw"
    temporal_address: str = "localhost:7233"
    temporal_namespace: str = "default"
    temporal_task_queue: str = "ingestion"
    otel_enabled: bool = False
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    plugins: list[str] = Field(default_factory=list)
    providers: ProvidersSettings = Field(default_factory=ProvidersSettings)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Add the YAML file below the environment and ``.env``, above the defaults."""
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            YamlConfigSource(settings_cls),
            file_secret_settings,
        )


class YamlConfigSource(PydanticBaseSettingsSource):
    """Settings from the YAML file named by ``DOCQA_CONFIG_FILE``, if that variable is set."""

    def __init__(self, settings_cls: type[BaseSettings], path: Path | None = None) -> None:
        """Read from ``path``, or from ``DOCQA_CONFIG_FILE`` when no path is given."""
        super().__init__(settings_cls)
        configured = os.environ.get(CONFIG_FILE_ENV)
        self._path = path if path is not None else (Path(configured) if configured else None)

    def get_field_value(
        self,
        field: FieldInfo,  # noqa: ARG002  # required by the base class signature
        field_name: str,
    ) -> tuple[Any, str, bool]:
        """Unused: the whole file is returned at once by ``__call__``."""
        return None, field_name, False

    def __call__(self) -> dict[str, Any]:
        """Return the file's settings, rejecting top-level keys that are not settings.

        Raises:
            ConfigError: If the file cannot be loaded or has an unknown top-level key.
        """
        if self._path is None:
            return {}
        data = load_yaml_config(self._path, os.environ)
        fields = set(self.settings_cls.model_fields)
        unknown = sorted(set(data) - fields)
        if unknown:
            raise ConfigError(
                f"config file {self._path} has unknown setting(s): {', '.join(unknown)}"
            )
        return data


def describe_validation_error(error: ValidationError) -> str:
    """Return one readable line per invalid field. Input values are left out (secrets)."""
    lines = [
        f"  {'.'.join(str(part) for part in item['loc']) or '(root)'}: {item['msg']}"
        for item in error.errors()
    ]
    return "invalid configuration:\n" + "\n".join(lines)


@lru_cache
def get_settings() -> Settings:
    """Return the cached process-wide settings.

    Raises:
        ConfigError: If any source holds an invalid value. The message lists every problem.
    """
    try:
        return Settings()
    except ValidationError as exc:
        raise ConfigError(describe_validation_error(exc)) from exc
