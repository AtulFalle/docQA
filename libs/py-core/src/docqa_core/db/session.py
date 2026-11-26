"""Async engine / session factories and tenant context helper."""

import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def make_engine(url: str, *, echo: bool = False) -> AsyncEngine:
    """Create an async engine with pre-ping enabled."""
    return create_async_engine(url, echo=echo, pool_pre_ping=True)


def make_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create a session factory that keeps objects usable after commit."""
    return async_sessionmaker(engine, expire_on_commit=False)


async def set_tenant_context(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    user_id: uuid.UUID | None = None,
    request_id: str | None = None,
) -> None:
    """Set the RLS context for the current transaction.

    ``app.tenant_id`` is read by every tenant policy; ``app.user_id`` and ``app.request_id``
    feed defaults and the audit log. The settings end with the transaction.
    """
    await session.execute(
        text(
            "SELECT set_config('app.tenant_id', :tid, true), "
            "set_config('app.user_id', :uid, true), "
            "set_config('app.request_id', :rid, true)"
        ),
        {
            "tid": str(tenant_id),
            "uid": str(user_id) if user_id else "",
            "rid": request_id or "",
        },
    )
