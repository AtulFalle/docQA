"""Helpers for integration tests against a database migrated by Prisma."""

import os
import uuid
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Connection, Engine, text

TEST_URL = os.environ.get("DOCQA_TEST_DATABASE_URL")


class TenantFactory:
    """Creates tenants as the superuser and removes everything they own afterwards."""

    def __init__(self, engine: Engine) -> None:
        """Bind to a superuser engine."""
        self.engine = engine
        self.created: list[uuid.UUID] = []

    def make(self) -> uuid.UUID:
        """Insert a tenant (tenants has no RLS) and return its id."""
        with self.engine.begin() as conn:
            tid = conn.execute(
                text("INSERT INTO tenants (slug, name) VALUES (:s, :s) RETURNING id"),
                {"s": f"test-{uuid.uuid4()}"},
            ).scalar_one()
        self.created.append(tid)
        return tid

    def cleanup(self) -> None:
        """Delete the tenants; FKs cascade to all their rows (superuser bypasses RLS)."""
        with self.engine.begin() as conn:
            for tid in self.created:
                conn.execute(text("DELETE FROM jobs WHERE tenant_id = :t"), {"t": tid})
                conn.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": tid})


@contextmanager
def as_role(
    engine: Engine, role: str, tenant: uuid.UUID | None, *, commit: bool = True
) -> Iterator[Connection]:
    """Open a transaction as an application role with the RLS tenant set.

    Both settings are transaction-local, so nothing leaks into the pooled connection.
    """
    with engine.connect() as conn:
        conn.execute(text(f"SET LOCAL ROLE {role}"))  # role names are fixed in tests
        if tenant is not None:
            conn.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tenant)})
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise
        if commit:
            conn.commit()
        else:
            conn.rollback()
