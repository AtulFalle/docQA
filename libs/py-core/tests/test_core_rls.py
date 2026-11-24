"""Cross-tenant leak test (blocking CI gate). Needs DOCQA_TEST_DATABASE_URL (superuser DSN).

Prisma owns the schema and the RLS policies (apps/backend/prisma). This test does NOT run
migrations: it assumes the database at DOCQA_TEST_DATABASE_URL is already migrated (CI applies
the Prisma migrations first). It creates a non-superuser role, grants it table access, and
asserts that RLS isolates tenants. Rows it inserts are deleted at teardown as superuser.
"""

import os
import uuid
from collections.abc import Iterator

import pytest
from sqlalchemy import Engine, create_engine, text

TEST_URL = os.environ.get("DOCQA_TEST_DATABASE_URL")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not TEST_URL, reason="DOCQA_TEST_DATABASE_URL not set"),
]

_created_tenants: list[uuid.UUID] = []


@pytest.fixture
def engine() -> Iterator[Engine]:
    assert TEST_URL
    eng = create_engine(TEST_URL)
    with eng.begin() as conn:
        conn.execute(
            text(
                "DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='docqa_app_test') "
                "THEN CREATE ROLE docqa_app_test LOGIN PASSWORD 'x'; END IF; END $$"
            )
        )
        conn.execute(text("GRANT ALL ON ALL TABLES IN SCHEMA public TO docqa_app_test"))
    _created_tenants.clear()
    yield eng
    with eng.begin() as conn:  # superuser bypasses RLS: remove everything this test inserted
        for tid in _created_tenants:
            conn.execute(text("DELETE FROM documents WHERE tenant_id = :t"), {"t": tid})
            conn.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": tid})
    eng.dispose()


def _make_tenants(engine: Engine) -> tuple[uuid.UUID, uuid.UUID]:
    a, b = uuid.uuid4(), uuid.uuid4()
    with engine.begin() as conn:  # tenants has no RLS
        for tid, slug in ((a, f"tenant-a-{a}"), (b, f"tenant-b-{b}")):
            conn.execute(
                text("INSERT INTO tenants (id, slug, name) VALUES (:id, :s, :s)"),
                {"id": tid, "s": slug},
            )
            _created_tenants.append(tid)
    return a, b


def _insert_doc(engine: Engine, tenant: uuid.UUID, title: str) -> None:
    with engine.begin() as conn:
        conn.execute(text("SET LOCAL ROLE docqa_app_test"))
        conn.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tenant)})
        conn.execute(
            text(
                "INSERT INTO documents (id, tenant_id, title, content_hash) "
                "VALUES (:id, :t, :title, :h)"
            ),
            {"id": uuid.uuid4(), "t": tenant, "title": title, "h": title},
        )


def _visible_titles(engine: Engine, tenant: uuid.UUID | None) -> list[str]:
    with engine.begin() as conn:
        conn.execute(text("SET LOCAL ROLE docqa_app_test"))
        if tenant is not None:
            conn.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tenant)})
        return [r[0] for r in conn.execute(text("SELECT title FROM documents"))]


def test_cross_tenant_isolation(engine: Engine) -> None:
    a, b = _make_tenants(engine)
    _insert_doc(engine, a, "doc-a")
    _insert_doc(engine, b, "doc-b")

    assert _visible_titles(engine, a) == ["doc-a"]
    assert _visible_titles(engine, b) == ["doc-b"]
    assert _visible_titles(engine, None) == []


def test_cannot_write_other_tenant_row(engine: Engine) -> None:
    a, b = _make_tenants(engine)
    with engine.connect() as conn:  # autobegin; closed with rollback (txn is aborted)
        conn.execute(text("SET LOCAL ROLE docqa_app_test"))
        conn.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(a)})
        with pytest.raises(Exception, match="row-level security"):
            conn.execute(
                text(
                    "INSERT INTO documents (id, tenant_id, title, content_hash) "
                    "VALUES (:id, :t, 'x', 'x')"
                ),
                {"id": uuid.uuid4(), "t": b},
            )
