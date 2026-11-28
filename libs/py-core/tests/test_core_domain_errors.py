"""Domain errors, their codes and the retryable flag."""

import subprocess
import sys

import pytest

from docqa_core.domain import (
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


@pytest.mark.parametrize(
    ("error_type", "code", "retryable"),
    [
        (DocqaError, "internal_error", False),
        (InvalidInputError, "invalid_input", False),
        (UnsupportedMediaTypeError, "unsupported_type", False),
        (NotFoundError, "not_found", False),
        (PermissionDeniedError, "permission_denied", False),
        (ConflictError, "conflict", False),
        (ConfigError, "config_error", False),
        (ProviderError, "provider_error", False),
        (ProviderUnavailableError, "provider_unavailable", True),
        (ProviderTimeoutError, "provider_timeout", True),
        (RateLimitedError, "rate_limited", True),
        (ContextTooLongError, "context_too_long", False),
    ],
)
def test_error_has_a_stable_code_and_default_retryable_flag(error_type, code, retryable):
    error = error_type("something went wrong")

    assert error.code == code
    assert error.retryable is retryable
    assert error.message == "something went wrong"
    assert str(error) == "something went wrong"
    assert isinstance(error, DocqaError)


def test_error_retryable_flag_can_be_overridden():
    assert ProviderError("bad gateway", retryable=True).retryable
    assert not ProviderUnavailableError("circuit open", retryable=False).retryable


def test_provider_errors_share_a_base_class():
    for error_type in (ProviderUnavailableError, ProviderTimeoutError, RateLimitedError):
        assert issubclass(error_type, ProviderError)
    assert issubclass(ContextTooLongError, ProviderError)


def test_rate_limited_error_keeps_retry_after():
    assert RateLimitedError("slow down", retry_after_s=2.5).retry_after_s == pytest.approx(2.5)
    assert RateLimitedError("slow down").retry_after_s is None


def test_rate_limited_error_rejects_a_negative_retry_after():
    with pytest.raises(InvalidInputError, match="retry_after_s"):
        raise RateLimitedError("slow down", retry_after_s=-1)


def test_domain_package_imports_no_framework():
    code = (
        "import sys, docqa_core.domain; "
        "loaded = [m for m in ('sqlalchemy', 'pydantic', 'structlog', 'opentelemetry') "
        "if m in sys.modules]; print(','.join(loaded))"
    )

    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )

    assert result.stdout.strip() == ""
