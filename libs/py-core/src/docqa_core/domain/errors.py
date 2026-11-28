"""Domain errors.

Services raise these; the edges translate them (HTTP status in the API, non-retryable
``ApplicationError`` in Temporal). Each error has a stable ``code`` for logs and envelopes, and a
``retryable`` flag that tells callers whether trying again can succeed.
"""

from typing import ClassVar


class DocqaError(Exception):
    """Base class for every docQA domain error."""

    code: ClassVar[str] = "internal_error"
    default_retryable: ClassVar[bool] = False

    def __init__(self, message: str, *, retryable: bool | None = None) -> None:
        """Create the error.

        Args:
            message: Safe, human-readable description. Never include document text or secrets.
            retryable: Overrides the class default when the caller knows better.
        """
        super().__init__(message)
        self.message = message
        self.retryable = self.default_retryable if retryable is None else retryable


class InvalidInputError(DocqaError):
    """The input breaks a rule of the domain. Retrying the same input fails again."""

    code = "invalid_input"


class NotFoundError(DocqaError):
    """The resource does not exist, or the caller may not know that it exists."""

    code = "not_found"


class PermissionDeniedError(DocqaError):
    """The principal may not perform this action."""

    code = "permission_denied"


class ConflictError(DocqaError):
    """The request conflicts with the current state, for example duplicate content."""

    code = "conflict"


class ProviderError(DocqaError):
    """A model provider (LLM, embedder, reranker, parser) failed."""

    code = "provider_error"


class ProviderUnavailableError(ProviderError):
    """The provider could not be reached or returned a server error."""

    code = "provider_unavailable"
    default_retryable = True


class ProviderTimeoutError(ProviderError):
    """The provider did not answer within its timeout."""

    code = "provider_timeout"
    default_retryable = True


class RateLimitedError(ProviderError):
    """The provider rejected the call because of a rate limit."""

    code = "rate_limited"
    default_retryable = True

    def __init__(self, message: str, *, retry_after_s: float | None = None) -> None:
        """Create the error.

        Args:
            message: Safe, human-readable description.
            retry_after_s: Seconds the provider asked us to wait, when it said so.

        Raises:
            InvalidInputError: If ``retry_after_s`` is negative.
        """
        if retry_after_s is not None and retry_after_s < 0:
            raise InvalidInputError("retry_after_s must not be negative")
        super().__init__(message)
        self.retry_after_s = retry_after_s


class ContextTooLongError(ProviderError):
    """The prompt does not fit the model's context window. Retrying cannot help."""

    code = "context_too_long"
