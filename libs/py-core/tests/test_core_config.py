from pathlib import Path

import pytest

from docqa_core.config import (
    CONFIG_FILE_ENV,
    ProviderSettings,
    Settings,
    YamlConfigSource,
    get_settings,
)
from docqa_core.domain import ConfigError


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()
    monkeypatch.delenv(CONFIG_FILE_ENV, raising=False)
    monkeypatch.delenv("DOCQA_PROVIDERS__LLM__NAME", raising=False)


def write_config(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "docqa.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ("DOCQA_ENV", "DOCQA_DATABASE_URL"):
        monkeypatch.delenv(key, raising=False)
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    assert s.env == "local"
    assert s.service_name == "docqa"
    assert s.log_json is True
    assert s.otel_enabled is False
    assert s.database_url.startswith("postgresql+psycopg://")
    assert s.s3_secret_key.get_secret_value() == "rustfsadmin"
    assert "rustfsadmin" not in repr(s.s3_secret_key)


def test_providers_default_to_fakes_and_no_plugins() -> None:
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    assert s.plugins == []
    assert s.providers.llm == ProviderSettings(name="fake", params={})
    assert s.providers.vector_store.name == "fake"


def test_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOCQA_ENV", "prod")
    monkeypatch.setenv("DOCQA_DATABASE_URL", "postgresql+psycopg://u:p@db:5432/x")
    s = get_settings()
    assert s.env == "prod"
    assert s.database_url == "postgresql+psycopg://u:p@db:5432/x"


def test_nested_env_variable_selects_a_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOCQA_PROVIDERS__LLM__NAME", "openai_compat")
    assert get_settings().providers.llm.name == "openai_compat"


def test_yaml_file_sets_providers_and_plugins(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = write_config(
        tmp_path,
        "plugins: [my_company.providers]\n"
        'providers:\n  llm:\n    name: fake\n    params: {latency_ms: "${LATENCY:-5}"}\n',
    )
    monkeypatch.setenv(CONFIG_FILE_ENV, str(path))

    s = get_settings()

    assert s.plugins == ["my_company.providers"]
    assert s.providers.llm.params == {"latency_ms": "5"}


def test_environment_overrides_the_yaml_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = write_config(tmp_path, "env: dev\nproviders:\n  llm:\n    name: fake\n")
    monkeypatch.setenv(CONFIG_FILE_ENV, str(path))
    monkeypatch.setenv("DOCQA_ENV", "staging")
    monkeypatch.setenv("DOCQA_PROVIDERS__LLM__NAME", "openai_compat")

    s = get_settings()

    assert s.env == "staging"
    assert s.providers.llm.name == "openai_compat"


def test_yaml_source_reads_an_explicit_path(tmp_path: Path) -> None:
    path = write_config(tmp_path, "service_name: from-yaml\n")

    assert YamlConfigSource(Settings, path)() == {"service_name": "from-yaml"}


def test_yaml_source_without_a_file_returns_nothing() -> None:
    assert YamlConfigSource(Settings)() == {}


def test_unknown_top_level_yaml_key_is_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv(CONFIG_FILE_ENV, str(write_config(tmp_path, "provders: {}\n")))
    with pytest.raises(ConfigError, match="unknown setting\\(s\\): provders"):
        get_settings()


def test_unknown_provider_section_is_reported_with_its_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = write_config(tmp_path, "providers:\n  lm:\n    name: fake\n")
    monkeypatch.setenv(CONFIG_FILE_ENV, str(path))
    with pytest.raises(ConfigError, match=r"invalid configuration:\n  providers\.lm: "):
        get_settings()


def test_missing_config_file_fails_at_startup(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv(CONFIG_FILE_ENV, str(tmp_path / "missing.yaml"))
    with pytest.raises(ConfigError, match="could not be read"):
        get_settings()


def test_get_settings_cached() -> None:
    assert get_settings() is get_settings()


def test_invalid_env_rejected_with_a_readable_message(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOCQA_ENV", "nope")
    with pytest.raises(ConfigError, match=r"invalid configuration:\n  env: ") as info:
        get_settings()
    assert "nope" not in str(info.value)


def test_blank_provider_name_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOCQA_PROVIDERS__LLM__NAME", "")
    with pytest.raises(ConfigError, match=r"providers\.llm\.name: "):
        get_settings()


def test_example_config_file_is_valid(monkeypatch: pytest.MonkeyPatch) -> None:
    example = Path(__file__).resolve().parents[3] / "config" / "docqa.example.yaml"
    monkeypatch.setenv(CONFIG_FILE_ENV, str(example))

    s = get_settings()

    assert s.plugins == []
    assert s.providers.llm.name == "fake"
