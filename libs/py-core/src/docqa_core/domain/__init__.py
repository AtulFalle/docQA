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
from docqa_core.domain.documents import Chunk, Document, ScoredChunk
from docqa_core.domain.errors import (
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
)
from docqa_core.domain.llm import FinishReason, LLMRequest, LLMResponse, Message, Role, Usage

__all__ = [
    "TENANT_PRINCIPAL",
    "Answer",
    "Chunk",
    "Citation",
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
    "PermissionDeniedError",
    "Principal",
    "ProviderError",
    "ProviderTimeoutError",
    "ProviderUnavailableError",
    "RateLimitedError",
    "Role",
    "ScoredChunk",
    "Usage",
    "group_principal",
    "user_principal",
]
