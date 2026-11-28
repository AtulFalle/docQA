"""Answers and their citations.

Citations are mandatory (``docs/engineering/rag-and-llm.md``): an answer either cites at least
one chunk or abstains. Citation ordinals are the numbers shown to users, ``[1]``, ``[2]``, ...
"""

from dataclasses import dataclass
from uuid import UUID

from docqa_core.domain._checks import require, require_finite, require_page_range
from docqa_core.domain.llm import Usage


@dataclass(frozen=True, slots=True, kw_only=True)
class Citation:
    """One source an answer relies on, pointing at a chunk the user may see."""

    ordinal: int
    chunk_id: UUID
    document_id: UUID
    document_version_id: UUID
    page_start: int | None = None
    page_end: int | None = None
    quote: str | None = None
    score: float | None = None

    def __post_init__(self) -> None:
        """Validate the citation."""
        require(self.ordinal >= 1, "citation ordinals start at 1")
        require_page_range(self.page_start, self.page_end)
        if self.score is not None:
            require_finite(self.score, "citation score")


@dataclass(frozen=True, slots=True, kw_only=True)
class Answer:
    """A generated answer with its citations and provenance."""

    text: str
    citations: tuple[Citation, ...]
    model: str
    prompt_version: str
    abstained: bool = False
    usage: tuple[Usage, ...] = ()

    def __post_init__(self) -> None:
        """Validate the answer."""
        require(bool(self.text.strip()), "answer text must not be blank")
        if self.abstained:
            require(not self.citations, "an abstention cites nothing")
        else:
            require(bool(self.citations), "an answer must cite at least one source")
        ordinals = [citation.ordinal for citation in self.citations]
        require(
            ordinals == list(range(1, len(ordinals) + 1)),
            "citation ordinals must run 1, 2, 3, ... in order",
        )

    @property
    def cited_chunk_ids(self) -> frozenset[UUID]:
        """The chunks this answer cites, for checking them against what was retrieved."""
        return frozenset(citation.chunk_id for citation in self.citations)
