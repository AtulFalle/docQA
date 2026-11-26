"""ORM models: a hand-maintained MIRROR of the Prisma schema (ADR 0005, design in ADR 0006).

Prisma (apps/backend/prisma) is the source of truth for the Postgres schema. Do not create
migrations from these models. ``tests/test_core_schema_contract.py`` fails CI when the mirror
drifts from the live schema, and ``tests/test_core_value_sets.py`` when an enum drifts from the
CHECK constraints or ``@docqa/contracts``.
"""

from docqa_core.db.models.access import DocumentAcl, Group, GroupMembership, User
from docqa_core.db.models.answering import Answer, Citation, Conversation, Feedback, Query
from docqa_core.db.models.documents import (
    Chunk,
    Document,
    DocumentVersion,
    DocumentVersionIndex,
    Job,
    UploadSession,
)
from docqa_core.db.models.enums import (
    ActorType,
    AuditOutcome,
    Distance,
    DocumentStatus,
    FeedbackRating,
    IndexEntryStatus,
    JobKind,
    JobStatus,
    MembershipSource,
    Permission,
    PrincipalType,
    QuerySource,
    QueryStatus,
    RejectionReason,
    SearchIndexStatus,
    TenantStatus,
    UploadStatus,
    UsageKind,
    UsageSource,
    UserRole,
    VersionStatus,
)
from docqa_core.db.models.platform import ModelPrice, SearchIndex, Tenant, TenantSettings
from docqa_core.db.models.usage import AuditLog, UsageDaily, UsageEvent

#: Tables with the standard ``tenant_isolation`` RLS policy. audit_log has its own policies.
TENANT_SCOPED_TABLES: tuple[str, ...] = (
    "users",
    "groups",
    "group_memberships",
    "documents",
    "document_versions",
    "document_acls",
    "upload_sessions",
    "chunks",
    "document_version_indexes",
    "jobs",
    "conversations",
    "queries",
    "answers",
    "citations",
    "feedback",
    "usage_events",
    "usage_daily",
)

#: Global tables without RLS.
GLOBAL_TABLES: tuple[str, ...] = ("tenants", "tenant_settings", "search_indexes", "model_prices")

__all__ = [
    "GLOBAL_TABLES",
    "TENANT_SCOPED_TABLES",
    "ActorType",
    "Answer",
    "AuditLog",
    "AuditOutcome",
    "Chunk",
    "Citation",
    "Conversation",
    "Distance",
    "Document",
    "DocumentAcl",
    "DocumentStatus",
    "DocumentVersion",
    "DocumentVersionIndex",
    "Feedback",
    "FeedbackRating",
    "Group",
    "GroupMembership",
    "IndexEntryStatus",
    "Job",
    "JobKind",
    "JobStatus",
    "MembershipSource",
    "ModelPrice",
    "Permission",
    "PrincipalType",
    "Query",
    "QuerySource",
    "QueryStatus",
    "RejectionReason",
    "SearchIndex",
    "SearchIndexStatus",
    "Tenant",
    "TenantSettings",
    "TenantStatus",
    "UploadSession",
    "UploadStatus",
    "UsageDaily",
    "UsageEvent",
    "UsageKind",
    "UsageSource",
    "User",
    "UserRole",
    "VersionStatus",
]
