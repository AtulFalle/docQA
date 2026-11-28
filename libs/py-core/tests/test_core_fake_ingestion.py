"""Plain-text parser and paragraph chunker, including the sample corpus end to end."""

import json
from pathlib import Path
from uuid import uuid4

import pytest

from docqa_core.domain import (
    ConfigError,
    Document,
    InvalidInputError,
    ParsedDocument,
    Principal,
    UnsupportedMediaTypeError,
)
from docqa_core.providers import chunkers, parsers
from docqa_core.providers.fakes import (
    FakeEmbedder,
    InMemoryVectorStore,
    LexicalReranker,
    ParagraphChunker,
    PlainTextParser,
)

CORPUS = Path(__file__).resolve().parents[3] / "eval" / "corpus" / "sample"
GOLDEN = Path(__file__).resolve().parents[3] / "eval" / "datasets" / "golden_v0.jsonl"


def document(**overrides: object) -> Document:
    values: dict[str, object] = {
        "id": uuid4(),
        "tenant_id": uuid4(),
        "version_id": uuid4(),
        "title": "Leave policy",
        "acl_principals": ("t",),
    }
    values.update(overrides)
    return Document(**values)  # type: ignore[arg-type]


def parse(text: str, media_type: str = "text/markdown") -> ParsedDocument:
    return PlainTextParser().parse(document(), text.encode(), media_type=media_type)


def test_fake_ingestion_providers_are_registered_as_fake():
    assert parsers.get("fake") is PlainTextParser
    assert chunkers.get("fake") is ParagraphChunker


@pytest.mark.parametrize(
    ("media_type", "supported"),
    [
        ("text/plain", True),
        ("text/markdown; charset=utf-8", True),
        ("TEXT/MARKDOWN", True),
        ("application/pdf", False),
    ],
)
def test_parser_supports_text_media_types(media_type, supported):
    assert PlainTextParser().supports(media_type) is supported


def test_parser_rejects_pdf_with_unsupported_type():
    with pytest.raises(UnsupportedMediaTypeError, match="application/pdf"):
        parse("%PDF-1.7", media_type="application/pdf")


def test_parser_rejects_content_that_is_not_utf8():
    with pytest.raises(InvalidInputError, match="UTF-8"):
        PlainTextParser().parse(document(), b"\xff\xfe\x00", media_type="text/plain")


def test_parser_splits_pages_on_page_markers():
    parsed = parse("<!-- page: 1 -->\nfirst\n<!-- page: 2 -->\nsecond\n")

    assert [(page.number, page.text.strip()) for page in parsed.pages] == [
        (1, "first"),
        (2, "second"),
    ]


def test_parser_keeps_text_before_the_first_marker_on_page_one():
    parsed = parse("intro\n<!-- page: 1 -->\nbody\n")

    assert [page.number for page in parsed.pages] == [1]
    assert "intro" in parsed.pages[0].text
    assert "body" in parsed.pages[0].text


def test_parser_rejects_page_markers_out_of_order():
    with pytest.raises(InvalidInputError, match="page markers"):
        parse("<!-- page: 1 -->\na\n<!-- page: 3 -->\nb\n")


def test_parser_splits_pages_on_form_feed_without_markers():
    parsed = parse("first\fsecond", media_type="text/plain")

    assert [page.text for page in parsed.pages] == ["first", "second"]


def test_chunker_tracks_nested_markdown_headings():
    text = (
        "# Policy\n\nIntro.\n\n## Annual\n\nEighteen days.\n\n## Sick\n\nTen days.\n\n# Other\n\nX."
    )
    chunks = ParagraphChunker().chunk(parse(text))

    assert [(c.text, c.section_path) for c in chunks] == [
        ("Intro.", ("Policy",)),
        ("Eighteen days.", ("Policy", "Annual")),
        ("Ten days.", ("Policy", "Sick")),
        ("X.", ("Other",)),
    ]


def test_chunker_records_the_page_of_each_chunk():
    chunks = ParagraphChunker().chunk(parse("<!-- page: 1 -->\na\n<!-- page: 2 -->\nb\n"))

    assert [(c.page_start, c.page_end) for c in chunks] == [(1, 1), (2, 2)]


def test_chunker_splits_long_paragraphs_at_sentence_ends():
    sentence = "Leave must be approved by a manager in advance. "
    chunks = ParagraphChunker(max_chars=120).chunk(parse(sentence * 6))

    assert len(chunks) > 1
    assert all(len(c.text) <= 120 for c in chunks)
    assert all(c.text.endswith(".") for c in chunks)


def test_chunker_hard_wraps_a_word_longer_than_the_limit():
    chunks = ParagraphChunker(max_chars=100).chunk(parse("x" * 250))

    assert [len(c.text) for c in chunks] == [100, 100, 50]


def test_chunker_rejects_a_tiny_max_chars():
    with pytest.raises(ConfigError, match="max_chars"):
        ParagraphChunker(max_chars=99)


def test_chunker_reports_its_version():
    assert ParagraphChunker(version="paragraph-v2").version == "paragraph-v2"


async def test_fake_pipeline_finds_the_gold_document_for_factual_golden_questions():
    """Parse, chunk, embed, search and rerank the sample corpus with the fakes only."""
    manifest = json.loads((CORPUS / "manifest.json").read_text())
    tenant = uuid4()
    store, embedder = InMemoryVectorStore(), FakeEmbedder(dimension=512)
    corpus_name = {}
    for doc_id in manifest:
        doc = document(tenant_id=tenant, title=doc_id)
        corpus_name[doc.id] = doc_id
        content = (CORPUS / f"{doc_id}.md").read_bytes()
        parsed = PlainTextParser().parse(doc, content, media_type="text/markdown")
        chunks = ParagraphChunker().chunk(parsed)
        await store.upsert(chunks, await embedder.embed_documents([c.text for c in chunks]))
    principal = Principal(tenant_id=tenant, user_id=uuid4())
    items = [json.loads(line) for line in GOLDEN.read_text().splitlines() if line.strip()]
    factual = [item for item in items if item["question_type"] == "factual"]
    assert factual

    for item in factual:
        query = await embedder.embed_query(item["question"])
        hits = await store.search(query, principal=principal, limit=10)
        top = await LexicalReranker().rerank(item["question"], hits, limit=3)
        found = {corpus_name[hit.chunk.document_id] for hit in top}
        gold = {evidence["doc_id"] for evidence in item["gold"]}
        assert gold & found, f"{item['id']}: gold {gold} not in top 3 {found}"
