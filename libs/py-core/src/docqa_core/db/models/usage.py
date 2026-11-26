"""Usage and audit tables. usage_events and audit_log are partitioned by month."""

import uuid
from datetime import date, datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy import ForeignKey, Index
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from docqa_core.db.base import Base, TimestampMixin
from docqa_core.db.models._columns import UUIDV7, enum_type
from docqa_core.db.models.enums import ActorType, AuditOutcome, UsageKind, UsageSource


class UsageEvent(Base):
    """One provider call with its cost. A log: no FKs, never blocks a purge."""

    __tablename__ = "usage_events"
    __table_args__ = (
        Index("ix_usage_events_tenant_id_occurred_at", "tenant_id", "occurred_at"),
        {"postgresql_partition_by": "RANGE (occurred_at)"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, server_default=UUIDV7
    )
    occurred_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), primary_key=True, server_default=sa.func.now()
    )
    tenant_id: Mapped[uuid.UUID]
    kind: Mapped[UsageKind] = mapped_column(enum_type(UsageKind, "usage_kind"))
    source: Mapped[UsageSource] = mapped_column(enum_type(UsageSource, "usage_source"))
    provider: Mapped[str] = mapped_column(sa.String(100))
    model: Mapped[str] = mapped_column(sa.String(255))
    input_tokens: Mapped[int] = mapped_column(server_default="0")
    output_tokens: Mapped[int] = mapped_column(server_default="0")
    units: Mapped[int] = mapped_column(server_default="0")
    cost_micros: Mapped[int] = mapped_column(sa.BigInteger, server_default="0")
    currency: Mapped[str] = mapped_column(sa.CHAR(3), server_default="USD")
    request_id: Mapped[str | None] = mapped_column(sa.String(64))
    trace_id: Mapped[str | None] = mapped_column(sa.String(32))
    user_id: Mapped[uuid.UUID | None]
    query_id: Mapped[uuid.UUID | None]
    job_id: Mapped[uuid.UUID | None]
    document_version_id: Mapped[uuid.UUID | None]


class UsageDaily(TimestampMixin, Base):
    """Daily usage totals per tenant, kept long-term."""

    __tablename__ = "usage_daily"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True
    )
    day: Mapped[date] = mapped_column(sa.Date, primary_key=True)
    kind: Mapped[UsageKind] = mapped_column(enum_type(UsageKind, "usage_kind"), primary_key=True)
    source: Mapped[UsageSource] = mapped_column(
        enum_type(UsageSource, "usage_source"), primary_key=True
    )
    provider: Mapped[str] = mapped_column(sa.String(100), primary_key=True)
    model: Mapped[str] = mapped_column(sa.String(255), primary_key=True)
    input_tokens: Mapped[int] = mapped_column(sa.BigInteger, server_default="0")
    output_tokens: Mapped[int] = mapped_column(sa.BigInteger, server_default="0")
    units: Mapped[int] = mapped_column(sa.BigInteger, server_default="0")
    cost_micros: Mapped[int] = mapped_column(sa.BigInteger, server_default="0")
    currency: Mapped[str] = mapped_column(sa.CHAR(3), server_default="USD")
    event_count: Mapped[int] = mapped_column(server_default="0")


class AuditLog(Base):
    """Append-only record of security-relevant actions. No FKs: history survives the tenant."""

    __tablename__ = "audit_log"
    __table_args__ = (
        Index("ix_audit_log_tenant_id_created_at", "tenant_id", "created_at"),
        {"postgresql_partition_by": "RANGE (created_at)"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, server_default=UUIDV7
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), primary_key=True, server_default=sa.func.now()
    )
    tenant_id: Mapped[uuid.UUID | None]
    actor_type: Mapped[ActorType] = mapped_column(enum_type(ActorType, "actor_type"))
    actor_user_id: Mapped[uuid.UUID | None]
    action: Mapped[str] = mapped_column(sa.String(100))
    resource_type: Mapped[str] = mapped_column(sa.String(100))
    resource_id: Mapped[str | None] = mapped_column(sa.String(255))
    outcome: Mapped[AuditOutcome] = mapped_column(
        enum_type(AuditOutcome, "audit_outcome"), server_default=AuditOutcome.SUCCESS.value
    )
    request_id: Mapped[str | None] = mapped_column(sa.String(64))
    trace_id: Mapped[str | None] = mapped_column(sa.String(32))
    ip: Mapped[str | None] = mapped_column(postgresql.INET)
    user_agent: Mapped[str | None] = mapped_column(sa.String(512))
    details: Mapped[dict[str, Any]] = mapped_column(
        postgresql.JSONB, server_default=sa.text("'{}'::jsonb")
    )
