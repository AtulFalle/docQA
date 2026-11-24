import pytest

from docqa_core.config import Settings, get_settings


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    get_settings.cache_clear()


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


def test_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOCQA_ENV", "prod")
    monkeypatch.setenv("DOCQA_DATABASE_URL", "postgresql+psycopg://u:p@db:5432/x")
    s = get_settings()
    assert s.env == "prod"
    assert s.database_url == "postgresql+psycopg://u:p@db:5432/x"


def test_get_settings_cached() -> None:
    assert get_settings() is get_settings()


def test_invalid_env_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOCQA_ENV", "nope")
    with pytest.raises(ValueError):  # noqa: PT011
        get_settings()
