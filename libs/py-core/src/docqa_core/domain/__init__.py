"""Domain types and errors shared by every docQA Python service.

Plain frozen dataclasses with no framework imports (no SQLAlchemy, pydantic or web framework),
enforced by import-linter. Validation errors raise ``InvalidInputError``.
"""

from docqa_core.domain.access import (
    TENANT_PRINCIPAL,
    Principal,
    group_principal,
    user_principal,
)
from docqa_core.domain.answers import Answer, Citation
from docqa_core.domain.documents import (
    Chunk,
    Document,
    ParsedDocument,
    ParsedPage,
    ScoredChunk,
)
from docqa_core.domain.errors import (
    ConfigError,
    ConflictError,
    ContextTooLongError,
    DocqaError,
    InvalidInputError,
    NotFoundError,
    PermissionDeniedError,
    ProviderError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    RateLimitedError,
    UnsupportedMediaTypeError,
)
from docqa_core.domain.llm import FinishReason, LLMRequest, LLMResponse, Message, Role, Usage

__all__ = [
    "TENANT_PRINCIPAL",
    "Answer",
    "Chunk",
    "Citation",
    "ConfigError",
    "ConflictError",
    "ContextTooLongError",
    "DocqaError",
    "Document",
    "FinishReason",
    "InvalidInputError",
    "LLMRequest",
    "LLMResponse",
    "Message",
    "NotFoundError",
    "ParsedDocument",
    "ParsedPage",
    "PermissionDeniedError",
    "Principal",
    "ProviderError",
    "ProviderTimeoutError",
    "ProviderUnavailableError",
    "RateLimitedError",
    "Role",
    "ScoredChunk",
    "UnsupportedMediaTypeError",
    "Usage",
    "group_principal",
    "user_principal",
]
