"""Documents and ingestion tables (RLS)."""

import uuid
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy import ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from docqa_core.db.base import Base, TimestampMixin
from docqa_core.db.models._columns import (
    created_ts,
    enum_type,
    opt_ts,
    sha256_hex,
    tenant_fk,
    tenant_ref,
    uuid_pk,
)
from docqa_core.db.models.enums import (
    DocumentStatus,
    IndexEntryStatus,
    JobKind,
    JobStatus,
    RejectionReason,
    UploadStatus,
    VersionStatus,
)


class Document(TimestampMixin, Base):
    """The logical document users and ACLs see."""

    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        tenant_ref(
            "current_version_id",
            "document_versions",
            "fk_documents_current_version_id_document_versions",
            use_alter=True,
        ),
        tenant_ref("created_by", "users", "fk_documents_created_by_users"),
        tenant_ref("deleted_by", "users", "fk_documents_deleted_by_users"),
        Index("ix_documents_tenant_id_created_at", "tenant_id", "created_at"),
        Index("ix_documents_purge_after", "purge_after"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = tenant_fk()
    title: Mapped[str] = mapped_column(sa.String(512))
    status: Mapped[DocumentStatus] = mapped_column(
        enum_type(DocumentStatus, "document_status"), server_default=DocumentStatus.ACTIVE.value
    )
    current_version_id: Mapped[uuid.UUID | None]
    created_by: Mapped[uuid.UUID | None]
    acl_revision: Mapped[int] = mapped_column(server_default="0")
    acl_synced_revision: Mapped[int] = mapped_column(server_default="0")
    legal_hold_at: Mapped[datetime | None] = opt_ts()
    deleted_at: Mapped[datetime | None] = opt_ts()
    deleted_by: Mapped[uuid.UUID | None]
    purge_after: Mapped[datetime | None] = opt_ts()


class DocumentVersion(TimestampMixin, Base):
    """One uploaded file of a document, with its ingestion state."""

    __tablename__ = "document_versions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "document_id", "version"),
        tenant_ref(
            "document_id",
            "documents",
            "fk_document_versions_document_id_documents",
            ondelete="CASCADE",
        ),
        tenant_ref("created_by", "users", "fk_document_versions_created_by_users"),
        tenant_ref("deleted_by", "users", "fk_document_versions_deleted_by_users"),
        Index("ix_document_versions_purge_after", "purge_after"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = tenant_fk()
    document_id: Mapped[uuid.UUID]
    version: Mapped[int]
    content_hash: Mapped[str | None] = mapped_column(sha256_hex())
    quarantine_key: Mapped[str | None] = mapped_column(sa.Text)
    object_key: Mapped[str | None] = mapped_column(sa.Text)
    size_bytes: Mapped[int] = mapped_column(sa.BigInteger)
    declared_mime: Mapped[str | None] = mapped_column(sa.String(255))
    detected_mime: Mapped[str | None] = mapped_column(sa.String(255))
    original_filename: Mapped[str] = mapped_column(sa.String(512))
    status: Mapped[VersionStatus] = mapped_column(
        enum_type(VersionStatus, "version_status"), server_default=VersionStatus.PENDING.value
    )
    rejection_reason: Mapped[RejectionReason | None] = mapped_column(
        enum_type(RejectionReason, "rejection_reason")
    )
    error_code: Mapped[str | None] = mapped_column(sa.String(64))
    error_message: Mapped[str | None] = mapped_column(sa.Text)
    page_count: Mapped[int | None]
    ocr_page_count: Mapped[int | None]
    parser: Mapped[str | None] = mapped_column(sa.String(100))
    parser_version: Mapped[str | None] = mapped_column(sa.String(50))
    extraction_quality: Mapped[float | None] = mapped_column(sa.REAL)
    injection_risk_score: Mapped[float | None] = mapped_column(sa.REAL)
    created_by: Mapped[uuid.UUID | None]
    extract_started_at: Mapped[datetime | None] = opt_ts()
    ingested_at: Mapped[datetime | None] = opt_ts()
    superseded_at: Mapped[datetime | None] = opt_ts()
    deleted_at: Mapped[datetime | None] = opt_ts()
    deleted_by: Mapped[uuid.UUID | None]
    purge_after: Mapped[datetime | None] = opt_ts()


class UploadSession(TimestampMixin, Base):
    """A presigned multipart upload into quarantine/."""

    __tablename__ = "upload_sessions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        tenant_ref("user_id", "users", "fk_upload_sessions_user_id_users"),
        tenant_ref(
            "document_id",
            "documents",
            "fk_upload_sessions_document_id_documents",
            ondelete="CASCADE",
        ),
        tenant_ref(
            "document_version_id",
            "document_versions",
            "fk_upload_sessions_document_version_id_document_versions",
            ondelete="CASCADE",
        ),
        Index("ix_upload_sessions_tenant_id_user_id_status", "tenant_id", "user_id", "status"),
        Index("ix_upload_sessions_status_expires_at", "status", "expires_at"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = tenant_fk()
    user_id: Mapped[uuid.UUID]
    document_id: Mapped[uuid.UUID | None]
    declared_filename: Mapped[str] = mapped_column(sa.String(512))
    declared_size_bytes: Mapped[int] = mapped_column(sa.BigInteger)
    declared_mime: Mapped[str] = mapped_column(sa.String(255))
    declared_sha256: Mapped[str | None] = mapped_column(sha256_hex())
    object_key: Mapped[str] = mapped_column(sa.Text)
    s3_upload_id: Mapped[str] = mapped_column(sa.String(1024))
    part_size_bytes: Mapped[int]
    status: Mapped[UploadStatus] = mapped_column(
        enum_type(UploadStatus, "upload_status"), server_default=UploadStatus.INITIATED.value
    )
    expires_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True))
    document_version_id: Mapped[uuid.UUID | None]


class Chunk(Base):
    """A piece of extracted text. Its id is the Qdrant point id; only leaves are embedded."""

    __tablename__ = "chunks"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "document_version_id", "ordinal"),
        tenant_ref(
            "document_id", "documents", "fk_chunks_document_id_documents", ondelete="CASCADE"
        ),
        tenant_ref(
            "document_version_id",
            "document_versions",
            "fk_chunks_document_version_id_document_versions",
            ondelete="CASCADE",
        ),
        tenant_ref(
            "parent_chunk_id", "chunks", "fk_chunks_parent_chunk_id_chunks", ondelete="CASCADE"
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = tenant_fk()
    document_id: Mapped[uuid.UUID]
    document_version_id: Mapped[uuid.UUID]
    parent_chunk_id: Mapped[uuid.UUID | None]
    ordinal: Mapped[int]
    level: Mapped[int] = mapped_column(sa.SmallInteger, server_default="0")
    is_leaf: Mapped[bool] = mapped_column(server_default=sa.true())
    text: Mapped[str] = mapped_column(sa.Text)
    text_hash: Mapped[str] = mapped_column(sha256_hex())
    token_count: Mapped[int]
    page_start: Mapped[int | None]
    page_end: Mapped[int | None]
    char_start: Mapped[int | None]
    char_end: Mapped[int | None]
    section_path: Mapped[list[str] | None] = mapped_column(
        postgresql.ARRAY(sa.Text), server_default=sa.text("ARRAY[]::text[]")
    )
    chunker_version: Mapped[str] = mapped_column(sa.String(50))
    # "metadata" is reserved on declarative classes, so the attribute is metadata_.
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = created_ts()


class DocumentVersionIndex(TimestampMixin, Base):
    """Which versions are embedded in which search index; the resume point for a reindex."""

    __tablename__ = "document_version_indexes"
    __table_args__ = (
        tenant_ref(
            "document_version_id",
            "document_versions",
            "fk_document_version_indexes_document_version_id",
            ondelete="CASCADE",
        ),
        Index("ix_document_version_indexes_index_id_status", "index_id", "status"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True
    )
    document_version_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    index_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("search_indexes.id"), primary_key=True)
    status: Mapped[IndexEntryStatus] = mapped_column(
        enum_type(IndexEntryStatus, "index_entry_status"),
        server_default=IndexEntryStatus.PENDING.value,
    )
    chunk_count: Mapped[int] = mapped_column(server_default="0")
    embedded_count: Mapped[int] = mapped_column(server_default="0")
    indexed_at: Mapped[datetime | None] = opt_ts()


class Job(TimestampMixin, Base):
    """User-facing status of a background job. Links have no FKs: jobs outlive their targets."""

    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        tenant_ref("created_by", "users", "fk_jobs_created_by_users"),
        Index("ix_jobs_tenant_id_status", "tenant_id", "status"),
        Index("ix_jobs_tenant_id_document_id", "tenant_id", "document_id"),
        Index("ix_jobs_status_priority_created_at", "status", "priority", "created_at"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = tenant_fk()
    kind: Mapped[JobKind] = mapped_column(enum_type(JobKind, "job_kind"))
    status: Mapped[JobStatus] = mapped_column(
        enum_type(JobStatus, "job_status"), server_default=JobStatus.QUEUED.value
    )
    priority: Mapped[int] = mapped_column(sa.SmallInteger, server_default="100")
    document_id: Mapped[uuid.UUID | None]
    document_version_id: Mapped[uuid.UUID | None]
    index_id: Mapped[uuid.UUID | None]
    workflow_id: Mapped[str | None] = mapped_column(sa.String(255), unique=True)
    run_id: Mapped[str | None] = mapped_column(sa.String(255))
    attempt: Mapped[int] = mapped_column(server_default="0")
    step: Mapped[str | None] = mapped_column(sa.String(100))
    progress_current: Mapped[int | None]
    progress_total: Mapped[int | None]
    error_code: Mapped[str | None] = mapped_column(sa.String(64))
    error_message: Mapped[str | None] = mapped_column(sa.Text)
    created_by: Mapped[uuid.UUID | None]
    admitted_at: Mapped[datetime | None] = opt_ts()
    started_at: Mapped[datetime | None] = opt_ts()
    finished_at: Mapped[datetime | None] = opt_ts()
