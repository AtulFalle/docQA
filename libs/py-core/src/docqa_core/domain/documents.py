"""Documents and chunks as the retrieval pipeline sees them.

These are plain values, not ORM rows: Postgres owns the text (ADR 0006), and these types carry
what parsing, chunking, search and answering need, including the ACL fields search filters on.
"""

from dataclasses import dataclass
from uuid import UUID

from docqa_core.domain._checks import require, require_finite, require_page_range


@dataclass(frozen=True, slots=True, kw_only=True)
class Document:
    """One version of a document that can be parsed, chunked and searched."""

    id: UUID
    tenant_id: UUID
    version_id: UUID
    title: str
    acl_principals: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate the document."""
        require(bool(self.title.strip()), "document title must not be blank")


@dataclass(frozen=True, slots=True, kw_only=True)
class Chunk:
    """A piece of one document version, the unit that is embedded and retrieved."""

    id: UUID
    tenant_id: UUID
    document_id: UUID
    document_version_id: UUID
    ordinal: int
    text: str
    page_start: int | None = None
    page_end: int | None = None
    section_path: tuple[str, ...] = ()
    acl_principals: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate the chunk."""
        require(self.ordinal >= 0, "chunk ordinal must not be negative")
        require(bool(self.text.strip()), "chunk text must not be blank")
        require_page_range(self.page_start, self.page_end)


@dataclass(frozen=True, slots=True)
class ScoredChunk:
    """A retrieved chunk with its relevance score. Higher is more relevant."""

    chunk: Chunk
    score: float

    def __post_init__(self) -> None:
        """Validate the score."""
        require_finite(self.score, "score")
