"""Database functions and rules from ADR 0006. Needs DOCQA_TEST_DATABASE_URL (superuser DSN)."""

import uuid

import pytest
from db_testing import TEST_URL, TenantFactory, as_role
from sqlalchemy import Connection, Engine, text
from sqlalchemy.exc import IntegrityError

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not TEST_URL, reason="DOCQA_TEST_DATABASE_URL not set"),
]

HASH = "a" * 64


def _doc(conn: Connection, tenant: uuid.UUID) -> uuid.UUID:
    return conn.execute(
        text("INSERT INTO documents (tenant_id, title) VALUES (:t, 'd') RETURNING id"),
        {"t": tenant},
    ).scalar_one()


def _version(conn: Connection, tenant: uuid.UUID, doc: uuid.UUID, version: int) -> uuid.UUID:
    return conn.execute(
        text(
            "INSERT INTO document_versions "
            "(tenant_id, document_id, version, size_bytes, original_filename, content_hash) "
            "VALUES (:t, :d, :v, 1, 'f.pdf', :h) RETURNING id"
        ),
        {"t": tenant, "d": doc, "v": version, "h": HASH},
    ).scalar_one()


def test_uuidv7_is_version_7_and_time_ordered(engine: Engine) -> None:
    with engine.connect() as conn:
        ids = conn.execute(text("SELECT uuidv7() FROM generate_series(1, 50)")).scalars().all()
    assert all(u.version == 7 for u in ids)
    assert [str(u)[:13] for u in ids] == sorted(str(u)[:13] for u in ids)


def test_duplicate_live_content_is_rejected(engine: Engine, tenants: TenantFactory) -> None:
    a = tenants.make()
    with as_role(engine, "docqa_backend", a) as conn:
        _version(conn, a, _doc(conn, a), 1)
    with (
        pytest.raises(IntegrityError, match="uq_document_versions_tenant_id_content_hash"),
        as_role(engine, "docqa_backend", a) as conn,
    ):
        _version(conn, a, _doc(conn, a), 1)


def test_superseded_content_can_be_uploaded_again(engine: Engine, tenants: TenantFactory) -> None:
    a = tenants.make()
    with as_role(engine, "docqa_backend", a) as conn:
        doc = _doc(conn, a)
        first = _version(conn, a, doc, 1)
        conn.execute(
            text("UPDATE document_versions SET superseded_at = now() WHERE id = :v"), {"v": first}
        )
        _version(conn, a, doc, 2)  # same hash, allowed because v1 is superseded


def test_admit_jobs_shares_slots_fairly_between_tenants(
    engine: Engine, tenants: TenantFactory
) -> None:
    a, b = tenants.make(), tenants.make()
    for tenant, count in ((a, 5), (b, 2)):
        with as_role(engine, "docqa_worker", tenant) as conn:
            conn.execute(
                text(
                    "INSERT INTO jobs (tenant_id, kind) "
                    "SELECT :t, 'ingest' FROM generate_series(1, :n)"
                ),
                {"t": tenant, "n": count},
            )
    with as_role(engine, "docqa_worker", None) as conn:
        admitted = conn.execute(text("SELECT job_tenant_id FROM admit_jobs(3, 1000)")).all()
    per_tenant = {t: sum(1 for (x,) in admitted if x == t) for t in (a, b)}
    assert per_tenant == {a: 3, b: 2}


def test_only_the_worker_may_admit_jobs(engine: Engine) -> None:
    with (
        pytest.raises(Exception, match="permission denied"),
        as_role(engine, "docqa_backend", None) as conn,
    ):
        conn.execute(text("SELECT * FROM admit_jobs(1, 1)"))


def _user(conn: Connection, tenant: uuid.UUID, role: str = "member") -> uuid.UUID:
    return conn.execute(
        text(
            "INSERT INTO users (tenant_id, idp_issuer, external_subject, role) "
            "VALUES (:t, 'iss', :s, :r) RETURNING id"
        ),
        {"t": tenant, "s": str(uuid.uuid4()), "r": role},
    ).scalar_one()


def test_accessible_document_ids_follows_grants(engine: Engine, tenants: TenantFactory) -> None:
    a = tenants.make()
    with as_role(engine, "docqa_backend", a) as conn:
        member, admin = _user(conn, a), _user(conn, a, "admin")
        group = conn.execute(
            text("INSERT INTO groups (tenant_id, name) VALUES (:t, 'g') RETURNING id"), {"t": a}
        ).scalar_one()
        conn.execute(
            text(
                "INSERT INTO group_memberships (tenant_id, group_id, user_id) VALUES (:t, :g, :u)"
            ),
            {"t": a, "g": group, "u": member},
        )
        via_group, private = _doc(conn, a), _doc(conn, a)
        conn.execute(
            text(
                "INSERT INTO document_acls (tenant_id, document_id, principal_type, group_id, "
                "permission) VALUES (:t, :d, 'group', :g, 'read')"
            ),
            {"t": a, "d": via_group, "g": group},
        )
    with as_role(engine, "docqa_ai", a, commit=False) as conn:

        def ids(user: uuid.UUID, need: str = "read") -> set[uuid.UUID]:
            rows = conn.execute(
                text("SELECT accessible_document_ids(:u, :p)"), {"u": user, "p": need}
            )
            return set(rows.scalars().all())

        assert ids(member) == {via_group}
        assert ids(member, "write") == set()
        assert ids(admin) == {via_group, private}
