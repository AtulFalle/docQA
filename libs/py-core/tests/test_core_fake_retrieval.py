"""Fake embedder, in-memory vector store and lexical reranker."""

import math
from uuid import uuid4

import pytest

from docqa_core.domain import Chunk, ConfigError, InvalidInputError, Principal, ScoredChunk
from docqa_core.providers import embedders, rerankers, vector_stores
from docqa_core.providers.fakes import FakeEmbedder, InMemoryVectorStore, LexicalReranker

TENANT = uuid4()
PRINCIPAL = Principal(tenant_id=TENANT, user_id=uuid4())


def chunk(text: str) -> Chunk:
    return Chunk(
        id=uuid4(),
        tenant_id=TENANT,
        document_id=uuid4(),
        document_version_id=uuid4(),
        ordinal=0,
        text=text,
        acl_principals=("t",),
    )


def cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


def test_fakes_are_registered_as_fake():
    assert embedders.get("fake") is FakeEmbedder
    assert vector_stores.get("fake") is InMemoryVectorStore
    assert rerankers.get("fake") is LexicalReranker


async def test_fake_embedder_puts_related_texts_closer_than_unrelated_ones():
    embedder = FakeEmbedder(dimension=256)
    leave, holiday, payment = await embedder.embed_documents(
        ["annual leave days per year", "how many annual leave days", "invoice payment terms"]
    )

    assert cosine(leave, holiday) > cosine(leave, payment)


async def test_fake_embedder_returns_unit_vectors():
    [vector] = await FakeEmbedder().embed_documents(["annual leave"])

    assert math.sqrt(sum(value * value for value in vector)) == pytest.approx(1.0)


async def test_fake_embedder_embeds_text_without_words_as_zeros():
    assert await FakeEmbedder(dimension=8).embed_query("... !!!") == [0.0] * 8


@pytest.mark.parametrize("dimension", [7, 4097])
def test_fake_embedder_rejects_an_out_of_range_dimension(dimension):
    with pytest.raises(ConfigError, match="dimension"):
        FakeEmbedder(dimension=dimension)


async def test_store_finds_the_chunk_that_matches_the_question():
    embedder, store = FakeEmbedder(dimension=256), InMemoryVectorStore()
    chunks = [
        chunk("Each employee receives 18 days of annual leave per calendar year."),
        chunk("Invoices are payable within 45 days of receipt."),
        chunk("Either party may terminate with 30 days written notice."),
    ]
    await store.upsert(chunks, await embedder.embed_documents([c.text for c in chunks]))

    query = await embedder.embed_query("How many days of annual leave per year?")
    [best] = await store.search(query, principal=PRINCIPAL, limit=1)

    assert best.chunk.id == chunks[0].id


async def test_store_with_nothing_indexed_returns_nothing():
    assert await InMemoryVectorStore().search([1.0, 0.0], principal=PRINCIPAL, limit=3) == []


async def test_store_rejects_a_vector_of_a_different_dimension():
    store = InMemoryVectorStore()
    await store.upsert([chunk("a")], [[1.0, 0.0]])

    with pytest.raises(InvalidInputError, match="2 values"):
        await store.search([1.0, 0.0, 0.0], principal=PRINCIPAL, limit=1)


async def test_store_rejects_an_empty_vector():
    with pytest.raises(InvalidInputError, match="empty"):
        await InMemoryVectorStore().upsert([chunk("a")], [[]])


async def test_store_rejects_a_limit_above_its_maximum():
    with pytest.raises(InvalidInputError, match="between 1 and 5"):
        await InMemoryVectorStore(max_limit=5).search([1.0], principal=PRINCIPAL, limit=6)


async def test_store_scores_a_zero_vector_as_zero():
    store = InMemoryVectorStore()
    await store.upsert([chunk("a")], [[0.0, 0.0]])

    [result] = await store.search([1.0, 0.0], principal=PRINCIPAL, limit=1)

    assert result.score == 0.0


def test_store_rejects_max_limit_below_one():
    with pytest.raises(ConfigError, match="max_limit"):
        InMemoryVectorStore(max_limit=0)


async def test_reranker_prefers_chunks_covering_more_of_the_query():
    leave = ScoredChunk(chunk("18 days of annual leave per year"), 0.1)
    notice = ScoredChunk(chunk("30 days notice"), 0.9)

    results = await LexicalReranker().rerank("annual leave days", [notice, leave], limit=2)

    assert [item.chunk.id for item in results] == [leave.chunk.id, notice.chunk.id]
    assert results[0].score == pytest.approx(1.0)
    assert results[1].score == pytest.approx(1 / 3)


async def test_reranker_keeps_incoming_order_for_equal_scores():
    first, second = ScoredChunk(chunk("alpha"), 0.2), ScoredChunk(chunk("beta"), 0.9)

    results = await LexicalReranker().rerank("gamma", [first, second], limit=2)

    assert [item.chunk.id for item in results] == [first.chunk.id, second.chunk.id]


async def test_reranker_scores_everything_zero_for_a_query_without_words():
    results = await LexicalReranker().rerank("???", [ScoredChunk(chunk("text"), 0.5)], limit=1)

    assert results[0].score == 0.0


async def test_reranker_rejects_a_limit_below_one():
    with pytest.raises(InvalidInputError, match="at least 1"):
        await LexicalReranker().rerank("q", [], limit=0)
