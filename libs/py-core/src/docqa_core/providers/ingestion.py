"""Ingestion interfaces (parser, chunker) and their registries.

Both are CPU-bound and synchronous; workers run them in an activity, off the event loop.
"""

from typing import Protocol, runtime_checkable

from docqa_core.domain.documents import Chunk, Document, ParsedDocument
from docqa_core.registry import Registry


@runtime_checkable
class Parser(Protocol):
    """Extracts page text from a file."""

    def supports(self, media_type: str) -> bool:
        """Whether this parser handles ``media_type`` (for example ``text/markdown``)."""
        ...

    def parse(self, document: Document, content: bytes, *, media_type: str) -> ParsedDocument:
        """Return the document's pages, numbered from 1.

        Raises:
            UnsupportedMediaTypeError: If ``supports(media_type)`` is false.
            InvalidInputError: If the content cannot be read as that type.
        """
        ...


@runtime_checkable
class Chunker(Protocol):
    """Splits a parsed document into chunks for embedding and retrieval."""

    @property
    def version(self) -> str:
        """Chunker version, recorded on every chunk (provenance, ``chunks.chunker_version``)."""
        ...

    def chunk(self, parsed: ParsedDocument) -> list[Chunk]:
        """Return the chunks in reading order, with ordinals from 0.

        Chunk ids are derived from the version, ordinal and text, so re-chunking the same
        version yields the same ids (idempotent ingestion).
        """
        ...


parsers: Registry[Parser] = Registry("parser")
chunkers: Registry[Chunker] = Registry("chunker")
