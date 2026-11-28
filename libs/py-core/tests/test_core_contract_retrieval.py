"""Contracts every embedder, vector store and reranker must satisfy. Run per registered provider.

The vector-store contract is the ACL rule of ADR 0006 in executable form: no result from
another tenant, and only chunks whose ``acl_principals`` meet the principal set.
"""

import math
from uuid import uuid4

import pytest

from docqa_core.domain import Chunk, InvalidInputError, Principal, ScoredChunk
from docqa_core.providers import (
    Embedder,
    Reranker,
    VectorStore,
    embedders,
    rerankers,
    vector_stores,
)
from docqa_core.registry import import_plugins
from docqa_core.value_sets import UserRole

# Register the built-in providers the way the composition root does.
import_plugins(["docqa_core.providers.fakes"])

TENANT, OTHER_TENANT = uuid4(), uuid4()
HR, LEGAL = uuid4(), uuid4()
ASHA = Principal(tenant_id=TENANT, user_id=uuid4(), group_ids=frozenset({HR}))
DOC = uuid4()


def make_chunk(text: str, *, tenant=TENANT, acl=("t",), document=DOC, ordinal=0) -> Chunk:
    return Chunk(
        id=uuid4(),
        tenant_id=tenant,
        document_id=document,
        document_version_id=uuid4(),
        ordinal=ordinal,
        text=text,
        acl_principals=acl,
    )


def unit_vector(dimension: int, index: int) -> list[float]:
    return [1.0 if position == index else 0.0 for position in range(dimension)]


# --- embedders ---------------------------------------------------------------------------


@pytest.fixture(params=embedders.names())
def embedder(request: pytest.FixtureRequest) -> Embedder:
    return embedders.create(request.param)


def test_embedder_contract_provider_implements_the_protocol(embedder):
    assert isinstance(embedder, Embedder)
    assert embedder.model
    assert embedder.dimension > 0


async def test_embedder_contract_returns_one_vector_per_text_of_the_right_size(embedder):
    vectors = await embedder.embed_documents(["annual leave policy", "notice period", "x"])

    assert len(vectors) == 3
    assert all(len(vector) == embedder.dimension for vector in vectors)
    assert all(math.isfinite(value) for vector in vectors for value in vector)


async def test_embedder_contract_is_deterministic(embedder):
    first = await embedder.embed_documents(["annual leave policy"])
    second = await embedder.embed_documents(["annual leave policy"])

    assert first == second


async def test_embedder_contract_queries_share_the_document_space(embedder):
    [document] = await embedder.embed_documents(["annual leave policy"])
    query = await embedder.embed_query("annual leave policy")

    assert len(query) == len(document)


async def test_embedder_contract_accepts_an_empty_batch(embedder):
    assert await embedder.embed_documents([]) == []


# --- vector stores -----------------------------------------------------------------------


@pytest.fixture(params=vector_stores.names())
def store(request: pytest.FixtureRequest) -> VectorStore:
    return vector_stores.create(request.param)


def test_vector_store_contract_provider_implements_the_protocol(store):
    assert isinstance(store, VectorStore)


async def test_vector_store_contract_never_returns_another_tenants_chunks(store):
    mine = make_chunk("mine")
    theirs = make_chunk("theirs", tenant=OTHER_TENANT)
    await store.upsert([mine, theirs], [unit_vector(4, 0), unit_vector(4, 0)])
    admin = Principal(tenant_id=TENANT, user_id=uuid4(), role=UserRole.ADMIN)

    results = await store.search(unit_vector(4, 0), principal=admin, limit=10)

    assert [item.chunk.id for item in results] == [mine.id]


async def test_vector_store_contract_filters_by_principal_set(store):
    for_all = make_chunk("all staff", acl=("t",))
    for_hr = make_chunk("hr only", acl=(f"g:{HR}",))
    for_legal = make_chunk("legal only", acl=(f"g:{LEGAL}",))
    for_me = make_chunk("just me", acl=(f"u:{ASHA.user_id}",))
    chunks = [for_all, for_hr, for_legal, for_me]
    await store.upsert(chunks, [unit_vector(4, 0)] * len(chunks))

    results = await store.search(unit_vector(4, 0), principal=ASHA, limit=10)

    assert {item.chunk.id for item in results} == {for_all.id, for_hr.id, for_me.id}


async def test_vector_store_contract_orders_by_similarity_and_honours_limit(store):
    near, middle, far = make_chunk("near"), make_chunk("middle"), make_chunk("far")
    await store.upsert([far, near, middle], [unit_vector(3, 2), unit_vector(3, 0), [0.7, 0.7, 0.0]])

    results = await store.search(unit_vector(3, 0), principal=ASHA, limit=2)

    assert [item.chunk.id for item in results] == [near.id, middle.id]
    assert results[0].score >= results[1].score


async def test_vector_store_contract_upsert_replaces_by_chunk_id(store):
    chunk = make_chunk("v1")
    await store.upsert([chunk], [unit_vector(2, 0)])
    await store.upsert([chunk], [unit_vector(2, 1)])

    results = await store.search(unit_vector(2, 1), principal=ASHA, limit=5)

    assert len(results) == 1
    assert results[0].score == pytest.approx(1.0)


async def test_vector_store_contract_delete_document_removes_only_that_document(store):
    gone = make_chunk("gone", document=DOC)
    kept = make_chunk("kept", document=uuid4())
    await store.upsert([gone, kept], [unit_vector(2, 0), unit_vector(2, 0)])

    removed = await store.delete_document(tenant_id=TENANT, document_id=DOC)
    results = await store.search(unit_vector(2, 0), principal=ASHA, limit=5)

    assert removed == 1
    assert [item.chunk.id for item in results] == [kept.id]


async def test_vector_store_contract_rejects_mismatched_vectors(store):
    with pytest.raises(InvalidInputError):
        await store.upsert([make_chunk("a"), make_chunk("b")], [unit_vector(2, 0)])


async def test_vector_store_contract_rejects_a_limit_below_one(store):
    with pytest.raises(InvalidInputError):
        await store.search(unit_vector(2, 0), principal=ASHA, limit=0)


# --- rerankers ---------------------------------------------------------------------------


@pytest.fixture(params=rerankers.names())
def reranker(request: pytest.FixtureRequest) -> Reranker:
    return rerankers.create(request.param)


CANDIDATES = [
    ScoredChunk(make_chunk("The notice period is 30 days."), 0.9),
    ScoredChunk(make_chunk("Each employee receives 18 days of annual leave."), 0.5),
    ScoredChunk(make_chunk("Payment is due within 45 days."), 0.4),
]


def test_reranker_contract_provider_implements_the_protocol(reranker):
    assert isinstance(reranker, Reranker)


async def test_reranker_contract_returns_only_given_candidates_sorted_and_limited(reranker):
    results = await reranker.rerank("annual leave days", CANDIDATES, limit=2)

    given = {item.chunk.id for item in CANDIDATES}
    assert len(results) <= 2
    assert {item.chunk.id for item in results} <= given
    assert [item.score for item in results] == sorted((i.score for i in results), reverse=True)


async def test_reranker_contract_accepts_no_candidates(reranker):
    assert await reranker.rerank("anything", [], limit=5) == []
