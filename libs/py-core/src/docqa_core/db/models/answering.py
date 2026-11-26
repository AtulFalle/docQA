"""Answering tables (RLS)."""

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import Index, UniqueConstraint
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from docqa_core.db.base import Base, TimestampMixin
from docqa_core.db.models._columns import created_ts, enum_type, tenant_fk, tenant_ref, uuid_pk
from docqa_core.db.models.enums import FeedbackRating, QuerySource, QueryStatus


class Conversation(TimestampMixin, Base):
    """Groups a user's follow-up questions."""

    __tablename__ = "conversations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        tenant_ref("user_id", "users", "fk_conversations_user_id_users"),
        Index(
            "ix_conversations_tenant_id_user_id_created_at", "tenant_id", "user_id", "created_at"
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = tenant_fk()
    user_id: Mapped[uuid.UUID]
    title: Mapped[str | None] = mapped_column(sa.String(512))


class Query(TimestampMixin, Base):
    """One question, with the principal set that was in scope."""

    __tablename__ = "queries"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        tenant_ref("user_id", "users", "fk_queries_user_id_users"),
        tenant_ref(
            "conversation_id",
            "conversations",
            "fk_queries_conversation_id_conversations",
            ondelete="CASCADE",
        ),
        Index("ix_queries_tenant_id_created_at", "tenant_id", "created_at"),
        Index("ix_queries_tenant_id_conversation_id", "tenant_id", "conversation_id"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = tenant_fk()
    user_id: Mapped[uuid.UUID]
    conversation_id: Mapped[uuid.UUID | None]
    question: Mapped[str] = mapped_column(sa.Text)
    source: Mapped[QuerySource] = mapped_column(
        enum_type(QuerySource, "query_source"), server_default=QuerySource.USER.value
    )
    index_id: Mapped[uuid.UUID | None]
    acl_principals: Mapped[list[str] | None] = mapped_column(
        postgresql.ARRAY(sa.Text), server_default=sa.text("ARRAY[]::text[]")
    )
    document_ids: Mapped[list[uuid.UUID] | None] = mapped_column(
        postgresql.ARRAY(postgresql.UUID(as_uuid=True)), server_default=sa.text("ARRAY[]::uuid[]")
    )
    status: Mapped[QueryStatus] = mapped_column(
        enum_type(QueryStatus, "query_status"), server_default=QueryStatus.PENDING.value
    )
    retrieved_count: Mapped[int | None]
    latency_ms: Mapped[int | None]
    time_to_first_token_ms: Mapped[int | None]
    request_id: Mapped[str | None] = mapped_column(sa.String(64))
    trace_id: Mapped[str | None] = mapped_column(sa.String(32))
    langfuse_trace_id: Mapped[str | None] = mapped_column(sa.String(64))


class Answer(Base):
    """A generated answer. A query can have several (regenerate)."""

    __tablename__ = "answers"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        tenant_ref("query_id", "queries", "fk_answers_query_id_queries", ondelete="CASCADE"),
        Index("ix_answers_tenant_id_query_id", "tenant_id", "query_id"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = tenant_fk()
    query_id: Mapped[uuid.UUID]
    text: Mapped[str] = mapped_column(sa.Text)
    provider: Mapped[str] = mapped_column(sa.String(100))
    model: Mapped[str] = mapped_column(sa.String(255))
    prompt_version: Mapped[str] = mapped_column(sa.String(50))
    confidence: Mapped[float | None] = mapped_column(sa.REAL)
    created_at: Mapped[datetime] = created_ts()


class Citation(Base):
    """A quote an answer relies on. Purging the cited version deletes it."""

    __tablename__ = "citations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "answer_id", "ordinal"),
        tenant_ref("answer_id", "answers", "fk_citations_answer_id_answers", ondelete="CASCADE"),
        tenant_ref(
            "document_version_id",
            "document_versions",
            "fk_citations_document_version_id_document_versions",
            ondelete="CASCADE",
        ),
        Index("ix_citations_tenant_id_document_version_id", "tenant_id", "document_version_id"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = tenant_fk()
    answer_id: Mapped[uuid.UUID]
    ordinal: Mapped[int]
    chunk_id: Mapped[uuid.UUID]
    document_id: Mapped[uuid.UUID]
    document_version_id: Mapped[uuid.UUID]
    page_start: Mapped[int | None]
    page_end: Mapped[int | None]
    char_start: Mapped[int | None]
    char_end: Mapped[int | None]
    quote: Mapped[str] = mapped_column(sa.Text)
    score: Mapped[float | None] = mapped_column(sa.REAL)
    created_at: Mapped[datetime] = created_ts()


class Feedback(TimestampMixin, Base):
    """A user's rating of an answer. A new rating replaces the old one."""

    __tablename__ = "feedback"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "answer_id", "user_id"),
        tenant_ref("answer_id", "answers", "fk_feedback_answer_id_answers", ondelete="CASCADE"),
        tenant_ref("user_id", "users", "fk_feedback_user_id_users"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = tenant_fk()
    answer_id: Mapped[uuid.UUID]
    user_id: Mapped[uuid.UUID]
    rating: Mapped[FeedbackRating] = mapped_column(enum_type(FeedbackRating, "feedback_rating"))
    reason: Mapped[str | None] = mapped_column(sa.String(64))
    comment: Mapped[str | None] = mapped_column(sa.Text)
