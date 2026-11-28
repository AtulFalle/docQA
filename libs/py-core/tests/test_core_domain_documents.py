"""Documents, chunks and scored chunks."""

import math
from uuid import uuid4

import pytest

from docqa_core.domain import Chunk, Document, InvalidInputError, ScoredChunk


def make_chunk(**overrides: object) -> Chunk:
    values: dict[str, object] = {
        "id": uuid4(),
        "tenant_id": uuid4(),
        "document_id": uuid4(),
        "document_version_id": uuid4(),
        "ordinal": 0,
        "text": "Leave is accrued monthly.",
    }
    values.update(overrides)
    return Chunk(**values)  # type: ignore[arg-type]


def test_document_keeps_its_acl_principals():
    document = Document(
        id=uuid4(),
        tenant_id=uuid4(),
        version_id=uuid4(),
        title="Leave policy",
        acl_principals=("t",),
    )

    assert document.acl_principals == ("t",)


def test_document_rejects_a_blank_title():
    with pytest.raises(InvalidInputError, match="title"):
        Document(id=uuid4(), tenant_id=uuid4(), version_id=uuid4(), title="  ")


def test_chunk_accepts_a_page_range_and_section_path():
    chunk = make_chunk(page_start=2, page_end=3, section_path=("Policy", "Accrual"))

    assert (chunk.page_start, chunk.page_end) == (2, 3)
    assert chunk.section_path == ("Policy", "Accrual")


def test_chunk_without_pages_is_allowed():
    chunk = make_chunk()

    assert chunk.page_start is None
    assert chunk.page_end is None


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"ordinal": -1}, "ordinal"),
        ({"text": "\n "}, "text"),
        ({"page_start": 1}, "both ends"),
        ({"page_end": 4}, "both ends"),
        ({"page_start": 0, "page_end": 1}, "1-based"),
        ({"page_start": 5, "page_end": 4}, "after page_end"),
    ],
)
def test_chunk_rejects_invalid_values(overrides, message):
    with pytest.raises(InvalidInputError, match=message):
        make_chunk(**overrides)


def test_chunk_is_keyword_only():
    with pytest.raises(TypeError):
        Chunk(uuid4(), uuid4(), uuid4(), uuid4(), 0, "text")  # type: ignore[misc]


def test_scored_chunk_keeps_the_score():
    scored = ScoredChunk(make_chunk(), 0.82)

    assert scored.score == pytest.approx(0.82)


@pytest.mark.parametrize("score", [math.nan, math.inf, -math.inf])
def test_scored_chunk_rejects_a_score_that_is_not_finite(score):
    with pytest.raises(InvalidInputError, match="finite"):
        ScoredChunk(make_chunk(), score)
