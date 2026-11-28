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


@dataclass(frozen=True, slots=True)
class ParsedPage:
    """The text of one page, as a parser extracted it. Pages are numbered from 1."""

    number: int
    text: str

    def __post_init__(self) -> None:
        """Validate the page number."""
        require(self.number >= 1, "page numbers start at 1")


@dataclass(frozen=True, slots=True)
class ParsedDocument:
    """A parsed document version: the document plus its pages, in order."""

    document: Document
    pages: tuple[ParsedPage, ...]

    def __post_init__(self) -> None:
        """Check that pages run 1, 2, 3, ... in order."""
        numbers = [page.number for page in self.pages]
        require(numbers == list(range(1, len(numbers) + 1)), "pages must run 1, 2, 3, ...")


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
