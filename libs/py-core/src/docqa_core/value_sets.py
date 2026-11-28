"""Value sets shared by the database, the domain types and ``@docqa/contracts``.

Each must match the CHECK constraint in the Prisma migration and, where the API exposes it,
the ``as const`` list in ``@docqa/contracts``. Tests check both. The module imports only the
standard library, so domain types can use these enums without depending on SQLAlchemy.
"""

import enum


class TenantStatus(enum.StrEnum):
    """Lifecycle of a tenant."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETING = "deleting"


class SearchIndexStatus(enum.StrEnum):
    """Lifecycle of a search index (one embedding model plus one Qdrant collection)."""

    BUILDING = "building"
    ACTIVE = "active"
    RETIRED = "retired"


class Distance(enum.StrEnum):
    """Vector distance of a search index."""

    COSINE = "cosine"
    DOT = "dot"
    EUCLID = "euclid"


class UsageKind(enum.StrEnum):
    """Kind of provider call, for prices and usage."""

    EMBEDDING = "embedding"
    GENERATION = "generation"
    RERANK = "rerank"
    OCR = "ocr"


class UsageSource(enum.StrEnum):
    """What caused a provider call."""

    USER = "user"
    EVAL = "eval"
    API = "api"
    INGEST = "ingest"


class UserRole(enum.StrEnum):
    """Role of a user within their tenant."""

    MEMBER = "member"
    ADMIN = "admin"


class MembershipSource(enum.StrEnum):
    """Where a group or membership comes from: created in docQA or synced from the IdP."""

    LOCAL = "local"
    IDP = "idp"


class PrincipalType(enum.StrEnum):
    """Kind of principal an ACL entry grants access to."""

    USER = "user"
    GROUP = "group"
    TENANT = "tenant"


class Permission(enum.StrEnum):
    """Access level granted by an ACL entry: read < write < admin."""

    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class DocumentStatus(enum.StrEnum):
    """Lifecycle of a document. Ingestion state lives on its versions."""

    ACTIVE = "active"
    DELETING = "deleting"


class VersionStatus(enum.StrEnum):
    """Ingestion state of a document version."""

    PENDING = "pending"
    SCANNING = "scanning"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    REJECTED = "rejected"


class RejectionReason(enum.StrEnum):
    """Why a version was rejected. Rejections are never retried."""

    TOO_LARGE = "too_large"
    TOO_MANY_PAGES = "too_many_pages"
    TOO_MANY_CHUNKS = "too_many_chunks"
    UNSUPPORTED_TYPE = "unsupported_type"
    ENCRYPTED = "encrypted"
    INFECTED = "infected"
    DUPLICATE = "duplicate"
    HASH_MISMATCH = "hash_mismatch"
    QUOTA_EXCEEDED = "quota_exceeded"


class UploadStatus(enum.StrEnum):
    """State of a presigned multipart upload."""

    INITIATED = "initiated"
    COMPLETED = "completed"
    ABORTED = "aborted"
    EXPIRED = "expired"


class IndexEntryStatus(enum.StrEnum):
    """State of one version in one search index."""

    PENDING = "pending"
    INDEXING = "indexing"
    INDEXED = "indexed"
    FAILED = "failed"
    REMOVED = "removed"


class JobKind(enum.StrEnum):
    """Type of background job."""

    INGEST = "ingest"
    REINDEX = "reindex"
    DELETE = "delete"
    PURGE = "purge"
    PERMISSION_SYNC = "permission_sync"


class JobStatus(enum.StrEnum):
    """Execution state of a background job."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QuerySource(enum.StrEnum):
    """Who asked a question."""

    USER = "user"
    EVAL = "eval"
    API = "api"


class QueryStatus(enum.StrEnum):
    """Outcome of a question."""

    PENDING = "pending"
    ANSWERED = "answered"
    NO_ANSWER = "no_answer"
    FAILED = "failed"


class FeedbackRating(enum.StrEnum):
    """A user's rating of an answer."""

    UP = "up"
    DOWN = "down"


class ActorType(enum.StrEnum):
    """Who performed an audited action."""

    USER = "user"
    PLATFORM_ADMIN = "platform_admin"
    SYSTEM = "system"
    SERVICE = "service"


class AuditOutcome(enum.StrEnum):
    """Result of an audited action."""

    SUCCESS = "success"
    DENIED = "denied"
    FAILURE = "failure"
