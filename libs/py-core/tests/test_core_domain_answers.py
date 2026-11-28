"""Answers and citations."""

from uuid import uuid4

import pytest

from docqa_core.domain import Answer, Citation, InvalidInputError, Usage
from docqa_core.value_sets import UsageKind


def make_citation(ordinal: int = 1, **overrides: object) -> Citation:
    values: dict[str, object] = {
        "ordinal": ordinal,
        "chunk_id": uuid4(),
        "document_id": uuid4(),
        "document_version_id": uuid4(),
    }
    values.update(overrides)
    return Citation(**values)  # type: ignore[arg-type]


def make_answer(**overrides: object) -> Answer:
    values: dict[str, object] = {
        "text": "Leave accrues monthly [1].",
        "citations": (make_citation(1),),
        "model": "fake-1",
        "prompt_version": "answer_v1",
    }
    values.update(overrides)
    return Answer(**values)  # type: ignore[arg-type]


def test_answer_lists_the_chunks_it_cites():
    first, second = make_citation(1), make_citation(2)

    answer = make_answer(citations=(first, second))

    assert answer.cited_chunk_ids == frozenset({first.chunk_id, second.chunk_id})
    assert not answer.abstained


def test_answer_keeps_usage_for_provenance():
    usage = Usage(kind=UsageKind.GENERATION, provider="fake", model="fake-1", output_tokens=7)

    assert make_answer(usage=(usage,)).usage == (usage,)


def test_answer_without_citations_is_rejected():
    with pytest.raises(InvalidInputError, match="at least one source"):
        make_answer(citations=())


def test_abstention_has_no_citations():
    answer = make_answer(
        text="I could not find this in the documents you have access to.",
        citations=(),
        abstained=True,
    )

    assert answer.abstained
    assert answer.cited_chunk_ids == frozenset()


def test_abstention_with_citations_is_rejected():
    with pytest.raises(InvalidInputError, match="cites nothing"):
        make_answer(abstained=True)


def test_answer_rejects_blank_text():
    with pytest.raises(InvalidInputError, match="blank"):
        make_answer(text=" ")


@pytest.mark.parametrize("ordinals", [(2,), (1, 3), (2, 1), (1, 1)])
def test_answer_rejects_citation_ordinals_out_of_sequence(ordinals):
    citations = tuple(make_citation(ordinal) for ordinal in ordinals)

    with pytest.raises(InvalidInputError, match="in order"):
        make_answer(citations=citations)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"ordinal": 0}, "start at 1"),
        ({"page_start": 3, "page_end": 2}, "after page_end"),
        ({"score": float("nan")}, "finite"),
    ],
)
def test_citation_rejects_invalid_values(overrides, message):
    with pytest.raises(InvalidInputError, match=message):
        make_citation(**overrides)


def test_citation_keeps_quote_pages_and_score():
    citation = make_citation(page_start=4, page_end=4, quote="accrued monthly", score=0.9)

    assert (citation.page_start, citation.page_end, citation.quote) == (4, 4, "accrued monthly")
    assert citation.score == pytest.approx(0.9)
