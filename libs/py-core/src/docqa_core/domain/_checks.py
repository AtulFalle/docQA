"""Small validation helpers shared by the domain types."""

import math

from docqa_core.domain.errors import InvalidInputError


def require(condition: bool, message: str) -> None:  # noqa: FBT001  # a guard, not an option
    """Raise ``InvalidInputError`` with ``message`` when ``condition`` is false."""
    if not condition:
        raise InvalidInputError(message)


def require_page_range(page_start: int | None, page_end: int | None) -> None:
    """Check an optional 1-based, inclusive page range."""
    if page_start is None or page_end is None:
        require(page_start is None and page_end is None, "page range needs both ends")
        return
    require(page_start >= 1, "page_start is 1-based")
    require(page_start <= page_end, "page_start must not be after page_end")


def require_finite(value: float, name: str) -> None:
    """Check that a score is a real number (not NaN or infinite)."""
    require(math.isfinite(value), f"{name} must be finite")
