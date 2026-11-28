"""Plain-text parser and paragraph chunker.

Enough to ingest the Markdown sample corpus end to end. The real parsers (PDF, Office) and the
token-aware recursive chunker arrive in M2 (PR-201, PR-202) behind the same interfaces.
"""

import hashlib
import re
import uuid

from docqa_core.domain.documents import Chunk, Document, ParsedDocument, ParsedPage
from docqa_core.domain.errors import ConfigError, InvalidInputError, UnsupportedMediaTypeError
from docqa_core.providers.ingestion import chunkers, parsers

PAGE_BREAK = "\f"
TEXT_MEDIA_TYPES = frozenset({"text/plain", "text/markdown"})
MIN_CHUNK_CHARS = 100

# Fixed namespace so chunk ids are stable across processes and releases.
_CHUNK_NAMESPACE = uuid.UUID("6f1f3a8e-2b8c-5d4e-9a7b-0c1d2e3f4a5b")
_PAGE_MARKER = re.compile(r"^[ \t]*<!--\s*page:\s*(\d+)\s*-->[ \t]*$", re.MULTILINE)
_PARAGRAPH_BREAK = re.compile(r"\n\s*\n")
_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


@parsers.register("fake")
class PlainTextParser:
    """Reads UTF-8 text or Markdown.

    Pages are marked with ``<!-- page: N -->`` comments (the eval corpus convention, numbered
    1, 2, 3, ...) or, when there are no markers, separated by form feed characters. Text before
    the first marker belongs to page 1.
    """

    def supports(self, media_type: str) -> bool:
        """Whether the media type (parameters such as ``charset`` ignored) is text."""
        return media_type.split(";", 1)[0].strip().lower() in TEXT_MEDIA_TYPES

    def parse(self, document: Document, content: bytes, *, media_type: str) -> ParsedDocument:
        """Split the text into pages.

        Raises:
            UnsupportedMediaTypeError: If the media type is not plain text or Markdown.
            InvalidInputError: If the content is not valid UTF-8.
        """
        if not self.supports(media_type):
            raise UnsupportedMediaTypeError(f"plain-text parser cannot read {media_type!r}")
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise InvalidInputError("document is not valid UTF-8 text") from exc
        return ParsedDocument(document, _pages(text))


def _pages(text: str) -> tuple[ParsedPage, ...]:
    markers = list(_PAGE_MARKER.finditer(text))
    if not markers:
        return tuple(ParsedPage(n, page) for n, page in enumerate(text.split(PAGE_BREAK), 1))
    numbers = [int(marker.group(1)) for marker in markers]
    if numbers != list(range(1, len(numbers) + 1)):
        raise InvalidInputError("page markers must run 1, 2, 3, ... in order")
    bounds = [marker.end() for marker in markers] + [len(text)]
    texts = [text[bounds[i] : markers[i + 1].start()] for i in range(len(markers) - 1)]
    texts.append(text[bounds[-2] :])
    texts[0] = text[: markers[0].start()] + texts[0]
    return tuple(ParsedPage(number, page) for number, page in enumerate(texts, 1))


@chunkers.register("fake")
class ParagraphChunker:
    """One chunk per paragraph, split further at sentence ends when longer than ``max_chars``.

    Markdown headings are not chunks themselves; they set the ``section_path`` of the chunks
    that follow. Every chunk inherits the document's tenant, ids and ACL principals.
    """

    def __init__(self, *, max_chars: int = 1200, version: str = "paragraph-v1") -> None:
        """Configure the largest chunk.

        Raises:
            ConfigError: If ``max_chars`` is below 100.
        """
        if max_chars < MIN_CHUNK_CHARS:
            raise ConfigError(f"paragraph chunker: max_chars must be at least {MIN_CHUNK_CHARS}")
        self._max_chars = max_chars
        self._version = version

    @property
    def version(self) -> str:
        """Chunker version recorded on every chunk."""
        return self._version

    def chunk(self, parsed: ParsedDocument) -> list[Chunk]:
        """Return the chunks in reading order."""
        chunks: list[Chunk] = []
        headings: list[tuple[int, str]] = []
        for page in parsed.pages:
            for paragraph in _PARAGRAPH_BREAK.split(page.text):
                text = paragraph.strip()
                heading = _HEADING.match(text) if "\n" not in text else None
                if heading:
                    _push_heading(headings, len(heading.group(1)), heading.group(2))
                    continue
                for piece in _split(text, self._max_chars):
                    chunks.append(self._make(parsed.document, len(chunks), piece, page, headings))
        return chunks

    def _make(
        self,
        document: Document,
        ordinal: int,
        text: str,
        page: ParsedPage,
        headings: list[tuple[int, str]],
    ) -> Chunk:
        text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        return Chunk(
            id=uuid.uuid5(_CHUNK_NAMESPACE, f"{document.version_id}:{ordinal}:{text_hash}"),
            tenant_id=document.tenant_id,
            document_id=document.id,
            document_version_id=document.version_id,
            ordinal=ordinal,
            text=text,
            page_start=page.number,
            page_end=page.number,
            section_path=tuple(title for _, title in headings),
            acl_principals=document.acl_principals,
        )


def _push_heading(headings: list[tuple[int, str]], level: int, title: str) -> None:
    while headings and headings[-1][0] >= level:
        headings.pop()
    headings.append((level, title))


def _split(text: str, max_chars: int) -> list[str]:
    """Split at sentence ends, then at spaces, so no piece is longer than ``max_chars``."""
    if not text:
        return []
    pieces: list[str] = []
    current = ""
    for sentence in _SENTENCE_END.split(text):
        for word_run in _hard_wrap(sentence, max_chars):
            candidate = f"{current} {word_run}".strip()
            if len(candidate) <= max_chars:
                current = candidate
                continue
            pieces.append(current)
            current = word_run
    if current:
        pieces.append(current)
    return pieces


def _hard_wrap(sentence: str, max_chars: int) -> list[str]:
    if len(sentence) <= max_chars:
        return [sentence]
    runs: list[str] = []
    current = ""
    for word in sentence.split():
        for start in range(0, len(word), max_chars):
            part = word[start : start + max_chars]
            candidate = f"{current} {part}".strip()
            if len(candidate) > max_chars:
                runs.append(current)
                candidate = part
            current = candidate
    if current:
        runs.append(current)
    return runs
