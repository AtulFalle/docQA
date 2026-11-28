"""Tokenising shared by the fake providers."""

import re

_WORD = re.compile(r"\w+")


def tokens(text: str) -> list[str]:
    """Return the lower-cased word tokens of ``text``."""
    return _WORD.findall(text.lower())
