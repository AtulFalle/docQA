"""Contracts every parser and chunker must satisfy. Run per registered provider."""

from uuid import uuid4

import pytest

from docqa_core.domain import (
    Chunk,
    Document,
    ParsedDocument,
    ParsedPage,
    UnsupportedMediaTypeError,
)
from docqa_core.providers import Chunker, Parser, chunkers, parsers
from docqa_core.registry import import_plugins

DOCUMENT = Document(
    id=uuid4(), tenant_id=uuid4(), version_id=uuid4(), title="Leave policy", acl_principals=("t",)
)
PARSED = ParsedDocument(
    DOCUMENT,
    (
        ParsedPage(1, "# Leave\n\nEach employee receives 18 days of annual leave."),
        ParsedPage(2, "## Carry forward\n\nUp to 5 days carry into the next year."),
    ),
)

# Register the built-in providers the way the composition root does.
import_plugins(["docqa_core.providers.fakes"])


@pytest.fixture(params=parsers.names())
def parser(request: pytest.FixtureRequest) -> Parser:
    return parsers.create(request.param)


@pytest.fixture(params=chunkers.names())
def chunker(request: pytest.FixtureRequest) -> Chunker:
    return chunkers.create(request.param)


def test_parser_contract_provider_implements_the_protocol(parser):
    assert isinstance(parser, Parser)


def test_parser_contract_rejects_a_media_type_it_does_not_support(parser):
    unsupported = "application/x-docqa-unknown"

    assert not parser.supports(unsupported)
    with pytest.raises(UnsupportedMediaTypeError):
        parser.parse(DOCUMENT, b"data", media_type=unsupported)


def test_chunker_contract_provider_implements_the_protocol(chunker):
    assert isinstance(chunker, Chunker)
    assert chunker.version


def test_chunker_contract_chunks_carry_the_documents_identity_and_acl(chunker):
    chunks = chunker.chunk(PARSED)

    assert chunks
    assert all(isinstance(chunk, Chunk) for chunk in chunks)
    for chunk in chunks:
        assert chunk.tenant_id == DOCUMENT.tenant_id
        assert chunk.document_id == DOCUMENT.id
        assert chunk.document_version_id == DOCUMENT.version_id
        assert chunk.acl_principals == DOCUMENT.acl_principals


def test_chunker_contract_ordinals_run_from_zero_in_reading_order(chunker):
    chunks = chunker.chunk(PARSED)

    assert [chunk.ordinal for chunk in chunks] == list(range(len(chunks)))
    pages = [chunk.page_start for chunk in chunks if chunk.page_start is not None]
    assert pages == sorted(pages)


def test_chunker_contract_ids_are_stable_and_unique(chunker):
    first = [chunk.id for chunk in chunker.chunk(PARSED)]
    second = [chunk.id for chunk in chunker.chunk(PARSED)]

    assert first == second
    assert len(set(first)) == len(first)


def test_chunker_contract_ids_differ_between_versions(chunker):
    other_version = ParsedDocument(
        Document(
            id=DOCUMENT.id,
            tenant_id=DOCUMENT.tenant_id,
            version_id=uuid4(),
            title=DOCUMENT.title,
            acl_principals=DOCUMENT.acl_principals,
        ),
        PARSED.pages,
    )

    first = {chunk.id for chunk in chunker.chunk(PARSED)}
    second = {chunk.id for chunk in chunker.chunk(other_version)}

    assert first.isdisjoint(second)


def test_chunker_contract_returns_nothing_for_blank_pages(chunker):
    blank = ParsedDocument(DOCUMENT, (ParsedPage(1, "  \n\n  "),))

    assert chunker.chunk(blank) == []
