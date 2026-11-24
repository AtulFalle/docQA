from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from docqa_ai_api.main import create_app
from docqa_core import __version__
from docqa_core.config import Settings


@pytest.fixture
def client() -> Iterator[TestClient]:
    settings = Settings(
        database_url="postgresql+psycopg://x:x@127.0.0.1:1/x", log_json=False, _env_file=None
    )
    with TestClient(create_app(settings)) as c:
        yield c


def test_healthz(client: TestClient) -> None:
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_readyz_unavailable_when_db_down(client: TestClient) -> None:
    r = client.get("/readyz")
    assert r.status_code == 503
    assert r.json() == {"status": "unavailable", "checks": {"database": "error"}}


def test_request_id_echoed(client: TestClient) -> None:
    r = client.get("/healthz", headers={"X-Request-ID": "abc-123"})
    assert r.headers["X-Request-ID"] == "abc-123"


def test_request_id_generated(client: TestClient) -> None:
    r = client.get("/healthz")
    assert len(r.headers["X-Request-ID"]) == 32


def test_info(client: TestClient) -> None:
    r = client.get("/v1/info")
    assert r.status_code == 200
    body = r.json()
    assert body["version"] == __version__
    assert set(body) == {"service", "version", "env"}
