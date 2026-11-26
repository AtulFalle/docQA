"""Tenant isolation (blocking CI gate). Needs DOCQA_TEST_DATABASE_URL (superuser DSN).

Prisma owns the schema, roles and RLS policies (apps/backend/prisma). These tests do NOT run
migrations: the database must already be migrated. They act as the real application roles
(docqa_backend, docqa_worker) and remove what they insert at teardown.
"""

import uuid

import pytest
from db_testing import TEST_URL, TenantFactory, as_role
from sqlalchemy import Connection, Engine, text
from sqlalchemy.exc import DBAPIError

from docqa_core.db import TENANT_SCOPED_TABLES

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not TEST_URL, reason="DOCQA_TEST_DATABASE_URL not set"),
]


def _insert_doc(conn: Connection, tenant: uuid.UUID, title: str) -> uuid.UUID:
    return conn.execute(
        text("INSERT INTO documents (tenant_id, title) VALUES (:t, :title) RETURNING id"),
        {"t": tenant, "title": title},
    ).scalar_one()


def test_backend_role_sees_only_its_tenant(engine: Engine, tenants: TenantFactory) -> None:
    a, b = tenants.make(), tenants.make()
    with as_role(engine, "docqa_backend", a) as conn:
        _insert_doc(conn, a, "doc-a")
    with as_role(engine, "docqa_backend", b) as conn:
        _insert_doc(conn, b, "doc-b")

    for tenant, expected in ((a, ["doc-a"]), (b, ["doc-b"]), (None, [])):
        with as_role(engine, "docqa_backend", tenant, commit=False) as conn:
            titles = conn.execute(text("SELECT title FROM documents")).scalars().all()
        assert titles == expected


def test_cannot_write_another_tenants_row(engine: Engine, tenants: TenantFactory) -> None:
    a, b = tenants.make(), tenants.make()
    with (
        pytest.raises(DBAPIError, match="row-level security"),
        as_role(engine, "docqa_backend", a, commit=False) as conn,
    ):
        _insert_doc(conn, b, "sneaky")


def test_composite_foreign_key_rejects_mixed_tenant_rows(
    engine: Engine, tenants: TenantFactory
) -> None:
    a, b = tenants.make(), tenants.make()
    with as_role(engine, "docqa_backend", a) as conn:
        doc_a = _insert_doc(conn, a, "doc-a")
    # As superuser (no RLS), a version of tenant B must still not point at tenant A's document.
    with pytest.raises(DBAPIError, match="foreign key"), engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO document_versions "
                "(tenant_id, document_id, version, size_bytes, original_filename) "
                "VALUES (:t, :d, 1, 1, 'x.pdf')"
            ),
            {"t": b, "d": doc_a},
        )


def test_every_tenant_table_has_forced_rls_and_a_policy(engine: Engine) -> None:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity, "
                "  (SELECT count(*) FROM pg_policy p WHERE p.polrelid = c.oid) "
                "FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
                "WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p') "
                "  AND EXISTS (SELECT 1 FROM pg_attribute a WHERE a.attrelid = c.oid "
                "              AND a.attname = 'tenant_id' AND NOT a.attisdropped)"
            )
        ).all()
    unprotected = {"tenant_settings"}  # global by design (ADR 0006): keyed by tenant_id, no RLS
    found = {name: (rls, forced, policies) for name, rls, forced, policies in rows}
    assert set(TENANT_SCOPED_TABLES) <= set(found)
    problems = [
        name
        for name, (rls, forced, policies) in found.items()
        if name not in unprotected and not (rls and forced and policies > 0)
    ]
    assert not problems, f"tables without forced RLS and a policy: {problems}"


def test_audit_log_is_append_only(engine: Engine, tenants: TenantFactory) -> None:
    a = tenants.make()
    with engine.connect() as conn:  # rolled back: audit rows can't be deleted afterwards
        conn.execute(
            text(
                "INSERT INTO audit_log (tenant_id, actor_type, action, resource_type) "
                "VALUES (:t, 'system', 'test.event', 'test')"
            ),
            {"t": a},
        )
        with pytest.raises(DBAPIError, match="append-only"):
            conn.execute(text("UPDATE audit_log SET action = 'x' WHERE tenant_id = :t"), {"t": a})
        conn.rollback()


def test_audit_log_rows_are_scoped_to_their_tenant(engine: Engine, tenants: TenantFactory) -> None:
    a, b = tenants.make(), tenants.make()
    with as_role(engine, "docqa_backend", a, commit=False) as conn:
        conn.execute(
            text(
                "INSERT INTO audit_log (tenant_id, actor_type, action, resource_type) "
                "VALUES (:t, 'user', 'test.event', 'test')"
            ),
            {"t": a},
        )
        conn.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(b)})
        visible = conn.execute(
            text("SELECT count(*) FROM audit_log WHERE action = 'test.event'")
        ).scalar_one()
    assert visible == 0
