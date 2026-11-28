"""Retrieval interfaces (embedder, vector store, reranker) and their registries."""

from collections.abc import Sequence
from typing import Protocol, runtime_checkable
from uuid import UUID

from docqa_core.domain.access import Principal
from docqa_core.domain.documents import Chunk, ScoredChunk
from docqa_core.registry import Registry


@runtime_checkable
class Embedder(Protocol):
    """Turns text into vectors. Documents and queries share one vector space."""

    @property
    def model(self) -> str:
        """Model name and version, recorded on every vector (provenance)."""

    @property
    def dimension(self) -> int:
        """Length of every vector this embedder returns."""

    async def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        """Return one vector per text, in the same order."""

    async def embed_query(self, text: str) -> list[float]:
        """Return the vector for a search query."""


@runtime_checkable
class VectorStore(Protocol):
    """Stores chunk vectors and searches them, filtering by tenant and ACL first.

    The filter is applied before ranking, never after (ADR 0006): a chunk the principal may
    not see must not influence results, counts or timing.
    """

    async def upsert(self, chunks: Sequence[Chunk], vectors: Sequence[Sequence[float]]) -> None:
        """Insert or replace chunks by id, each with its vector."""

    async def search(
        self, vector: Sequence[float], *, principal: Principal, limit: int
    ) -> list[ScoredChunk]:
        """Return up to ``limit`` visible chunks, most similar first."""

    async def delete_document(self, *, tenant_id: UUID, document_id: UUID) -> int:
        """Remove every chunk of one document. Return how many were removed."""


@runtime_checkable
class Reranker(Protocol):
    """Reorders retrieved candidates by relevance to the query."""

    async def rerank(
        self, query: str, candidates: Sequence[ScoredChunk], *, limit: int
    ) -> list[ScoredChunk]:
        """Return up to ``limit`` of the candidates, most relevant first, with new scores."""


embedders: Registry[Embedder] = Registry("embedder")
vector_stores: Registry[VectorStore] = Registry("vector_store")
rerankers: Registry[Reranker] = Registry("reranker")
