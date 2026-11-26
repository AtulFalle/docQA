"""Platform tables: global, no RLS."""

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from docqa_core.db.base import Base, TimestampMixin
from docqa_core.db.models._columns import created_ts, enum_type, opt_ts, uuid_pk
from docqa_core.db.models.enums import Distance, SearchIndexStatus, TenantStatus, UsageKind


class Tenant(TimestampMixin, Base):
    """Isolation boundary that owns all other rows."""

    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = uuid_pk()
    slug: Mapped[str] = mapped_column(sa.String(100), unique=True)
    name: Mapped[str] = mapped_column(sa.String(255))
    status: Mapped[TenantStatus] = mapped_column(
        enum_type(TenantStatus, "tenant_status"), server_default=TenantStatus.ACTIVE.value
    )
    idp_organization_id: Mapped[str | None] = mapped_column(sa.String(255), unique=True)
    legal_hold_at: Mapped[datetime | None] = opt_ts()
    deleted_at: Mapped[datetime | None] = opt_ts()


class TenantSettings(TimestampMixin, Base):
    """Per-tenant overrides. Null means the deployment default."""

    __tablename__ = "tenant_settings"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True
    )
    deleted_document_retention_days: Mapped[int | None]
    query_retention_days: Mapped[int | None]
    max_file_bytes: Mapped[int | None] = mapped_column(sa.BigInteger)
    max_pages_per_document: Mapped[int | None]
    max_ocr_pages_per_document: Mapped[int | None]
    max_chunks_per_version: Mapped[int | None]
    max_storage_bytes: Mapped[int | None] = mapped_column(sa.BigInteger)
    max_documents: Mapped[int | None]
    max_concurrent_uploads_per_user: Mapped[int | None]
    max_concurrent_uploads: Mapped[int | None]
    max_running_jobs: Mapped[int | None]
    max_queued_jobs: Mapped[int | None]
    max_queries_per_minute_per_user: Mapped[int | None]
    max_queries_per_minute: Mapped[int | None]
    monthly_budget_micros: Mapped[int | None] = mapped_column(sa.BigInteger)
    allowed_mime_types: Mapped[list[str] | None] = mapped_column(
        postgresql.ARRAY(sa.String(255)), server_default=sa.text("ARRAY[]::varchar[]")
    )


class SearchIndex(TimestampMixin, Base):
    """One embedding model plus one Qdrant collection. At most one is active."""

    __tablename__ = "search_indexes"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(sa.String(100), unique=True)
    embedding_provider: Mapped[str] = mapped_column(sa.String(100))
    embedding_model: Mapped[str] = mapped_column(sa.String(255))
    model_version: Mapped[str | None] = mapped_column(sa.String(100))
    dimension: Mapped[int]
    distance: Mapped[Distance] = mapped_column(
        enum_type(Distance, "distance"), server_default=Distance.COSINE.value
    )
    qdrant_collection: Mapped[str] = mapped_column(sa.String(255), unique=True)
    chunker_version: Mapped[str] = mapped_column(sa.String(50))
    status: Mapped[SearchIndexStatus] = mapped_column(
        enum_type(SearchIndexStatus, "search_index_status"),
        server_default=SearchIndexStatus.BUILDING.value,
    )
    activated_at: Mapped[datetime | None] = opt_ts()
    retired_at: Mapped[datetime | None] = opt_ts()


class ModelPrice(Base):
    """Price of a model, effective from a date. Costs are worked out when usage is written."""

    __tablename__ = "model_prices"
    __table_args__ = (UniqueConstraint("provider", "model", "kind", "effective_from"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    provider: Mapped[str] = mapped_column(sa.String(100))
    model: Mapped[str] = mapped_column(sa.String(255))
    kind: Mapped[UsageKind] = mapped_column(enum_type(UsageKind, "usage_kind"))
    input_micros_per_mtok: Mapped[int | None] = mapped_column(sa.BigInteger)
    output_micros_per_mtok: Mapped[int | None] = mapped_column(sa.BigInteger)
    unit_micros: Mapped[int | None] = mapped_column(sa.BigInteger)
    currency: Mapped[str] = mapped_column(sa.CHAR(3), server_default="USD")
    effective_from: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True))
    created_at: Mapped[datetime] = created_ts()
