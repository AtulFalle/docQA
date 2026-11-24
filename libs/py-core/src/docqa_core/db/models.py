"""ORM models. All tables except ``tenants`` and ``audit_log`` are tenant-scoped (RLS).

Prisma (apps/backend/prisma) is the source of truth for the Postgres schema; these models are a
hand-maintained MIRROR for the Python AI services. Do not create migrations from them.
``tests/test_core_schema_contract.py`` fails CI when this mirror drifts from the live schema.
"""

import enum
import uuid
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy import ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from docqa_core.db.base import Base, TimestampMixin


def _enum(py_enum: type[enum.StrEnum], name: str) -> sa.Enum:
    return sa.Enum(
        py_enum,
        native_enum=False,
        length=32,
        name=name,
        values_callable=lambda e: [m.value for m in e],
    )


def _ts() -> Mapped[datetime]:
    return mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)


class TenantStatus(enum.StrEnum):
    """Lifecycle state of a tenant."""

    ACTIVE = "active"
    SUSPENDED = "suspended"


class DocumentStatus(enum.StrEnum):
    """Processing state of a document."""

    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    DELETED = "deleted"


class PrincipalType(enum.StrEnum):
    """Kind of principal an ACL entry grants access to."""

    USER = "user"
    GROUP = "group"
    TENANT = "tenant"


class Permission(enum.StrEnum):
    """Access level granted by an ACL entry."""

    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class JobKind(enum.StrEnum):
    """Type of background job."""

    INGEST = "ingest"
    REINDEX = "reindex"
    DELETE = "delete"
    PERMISSION_SYNC = "permission_sync"


class JobStatus(enum.StrEnum):
    """Execution state of a background job."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Tenant(TimestampMixin, Base):
    """Isolation boundary that owns all other rows."""

    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(sa.String(100), unique=True)
    name: Mapped[str] = mapped_column(sa.String(255))
    status: Mapped[TenantStatus] = mapped_column(
        _enum(TenantStatus, "tenant_status"),
        default=TenantStatus.ACTIVE,
        server_default=TenantStatus.ACTIVE.value,
    )


class User(TimestampMixin, Base):
    """A tenant member identified by an external subject."""

    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("tenant_id", "external_subject", name="uq_users_tenant_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    external_subject: Mapped[str] = mapped_column(sa.String(255))
    email: Mapped[str] = mapped_column(sa.String(320))
    display_name: Mapped[str | None] = mapped_column(sa.String(255))
    is_active: Mapped[bool] = mapped_column(default=True, server_default=sa.true())


class Group(TimestampMixin, Base):
    """A named set of users within a tenant."""

    __tablename__ = "groups"
    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_groups_tenant_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(sa.String(255))
    external_id: Mapped[str | None] = mapped_column(sa.String(255))


class GroupMembership(Base):
    """Association between a user and a group."""

    __tablename__ = "group_memberships"

    group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = _ts()


class Document(TimestampMixin, Base):
    """A logical document, deduplicated by content hash per tenant."""

    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("tenant_id", "content_hash", name="uq_documents_tenant_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(sa.String(512))
    source_uri: Mapped[str | None] = mapped_column(sa.Text)
    mime_type: Mapped[str | None] = mapped_column(sa.String(255))
    content_hash: Mapped[str] = mapped_column(sa.String(64))
    status: Mapped[DocumentStatus] = mapped_column(
        _enum(DocumentStatus, "document_status"),
        default=DocumentStatus.PENDING,
        server_default=DocumentStatus.PENDING.value,
    )
    current_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("document_versions.id", ondelete="SET NULL", use_alter=True)
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    deleted_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))


class DocumentAcl(Base):
    """Access-control entry granting a principal permission on a document."""

    __tablename__ = "document_acls"
    __table_args__ = (
        Index("ix_document_acls_tenant_principal", "tenant_id", "principal_type", "principal_id"),
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    principal_type: Mapped[PrincipalType] = mapped_column(
        _enum(PrincipalType, "principal_type"), primary_key=True
    )
    principal_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    permission: Mapped[Permission] = mapped_column(
        _enum(Permission, "permission"), primary_key=True
    )


class DocumentVersion(Base):
    """An immutable ingested revision of a document."""

    __tablename__ = "document_versions"
    __table_args__ = (
        UniqueConstraint("document_id", "version", name="uq_document_versions_document_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    version: Mapped[int]
    object_key: Mapped[str] = mapped_column(sa.Text)
    size_bytes: Mapped[int] = mapped_column(sa.BigInteger)
    page_count: Mapped[int | None]
    parser: Mapped[str | None] = mapped_column(sa.String(100))
    parser_version: Mapped[str | None] = mapped_column(sa.String(50))
    extraction_quality: Mapped[float | None] = mapped_column(sa.Float)
    injection_risk_score: Mapped[float | None] = mapped_column(sa.Float)
    status: Mapped[DocumentStatus] = mapped_column(
        _enum(DocumentStatus, "document_version_status"),
        default=DocumentStatus.PENDING,
        server_default=DocumentStatus.PENDING.value,
    )
    created_at: Mapped[datetime] = _ts()


class Chunk(Base):
    """A retrievable text segment of a document version."""

    __tablename__ = "chunks"
    __table_args__ = (
        Index("ix_chunks_tenant_id_document_version_id", "tenant_id", "document_version_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    document_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("document_versions.id", ondelete="CASCADE")
    )
    parent_chunk_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("chunks.id", ondelete="CASCADE")
    )
    ordinal: Mapped[int]
    text: Mapped[str] = mapped_column(sa.Text)
    token_count: Mapped[int]
    page_start: Mapped[int | None]
    page_end: Mapped[int | None]
    section_path: Mapped[list[str]] = mapped_column(
        postgresql.JSONB, default=list, server_default=sa.text("'[]'::jsonb")
    )
    chunker_version: Mapped[str] = mapped_column(sa.String(50))
    embedding_model: Mapped[str | None] = mapped_column(sa.String(100))
    index_version: Mapped[str | None] = mapped_column(sa.String(50))
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", postgresql.JSONB, default=dict, server_default=sa.text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = _ts()


class Job(TimestampMixin, Base):
    """A tracked background job (ingest or reindex)."""

    __tablename__ = "jobs"
    __table_args__ = (Index("ix_jobs_tenant_id_status", "tenant_id", "status"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    kind: Mapped[JobKind] = mapped_column(_enum(JobKind, "job_kind"))
    status: Mapped[JobStatus] = mapped_column(
        _enum(JobStatus, "job_status"),
        default=JobStatus.QUEUED,
        server_default=JobStatus.QUEUED.value,
    )
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL")
    )
    workflow_id: Mapped[str | None] = mapped_column(sa.String(255))
    attempt: Mapped[int] = mapped_column(default=0, server_default="0")
    error: Mapped[str | None] = mapped_column(sa.Text)
    payload: Mapped[dict[str, Any]] = mapped_column(
        postgresql.JSONB, default=dict, server_default=sa.text("'{}'::jsonb")
    )
    started_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))


class AuditLog(Base):
    """Append-only record of security-relevant actions."""

    __tablename__ = "audit_log"
    __table_args__ = (Index("ix_audit_log_tenant_id_created_at", "tenant_id", "created_at"),)

    id: Mapped[int] = mapped_column(sa.BigInteger, sa.Identity(), primary_key=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="SET NULL")
    )
    actor_user_id: Mapped[uuid.UUID | None]
    action: Mapped[str] = mapped_column(sa.String(100))
    resource_type: Mapped[str] = mapped_column(sa.String(100))
    resource_id: Mapped[str | None] = mapped_column(sa.String(255))
    request_id: Mapped[str | None] = mapped_column(sa.String(64))
    trace_id: Mapped[str | None] = mapped_column(sa.String(32))
    ip: Mapped[str | None] = mapped_column(sa.String(45))
    details: Mapped[dict[str, Any]] = mapped_column(
        postgresql.JSONB, default=dict, server_default=sa.text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = _ts()


TENANT_SCOPED_TABLES: tuple[str, ...] = (
    "users",
    "groups",
    "group_memberships",
    "documents",
    "document_acls",
    "document_versions",
    "chunks",
    "jobs",
)
