"""Database layer: declarative base, models and session helpers."""

from docqa_core.db.base import Base, TimestampMixin
from docqa_core.db.models import (
    TENANT_SCOPED_TABLES,
    AuditLog,
    Chunk,
    Document,
    DocumentAcl,
    DocumentStatus,
    DocumentVersion,
    Group,
    GroupMembership,
    Job,
    JobKind,
    JobStatus,
    Permission,
    PrincipalType,
    Tenant,
    TenantStatus,
    User,
)
from docqa_core.db.session import make_engine, make_sessionmaker, set_tenant_context

__all__ = [
    "TENANT_SCOPED_TABLES",
    "AuditLog",
    "Base",
    "Chunk",
    "Document",
    "DocumentAcl",
    "DocumentStatus",
    "DocumentVersion",
    "Group",
    "GroupMembership",
    "Job",
    "JobKind",
    "JobStatus",
    "Permission",
    "PrincipalType",
    "Tenant",
    "TenantStatus",
    "TimestampMixin",
    "User",
    "make_engine",
    "make_sessionmaker",
    "set_tenant_context",
]
