"""Fake embedder, in-memory vector store and lexical reranker.

They behave like the real thing at small scale: similar texts get similar vectors, search
filters by tenant and principal set before ranking, and the reranker prefers chunks that
cover more of the query.
"""

import hashlib
import math
from collections.abc import Sequence
from uuid import UUID

from docqa_core.domain._checks import require
from docqa_core.domain.access import Principal
from docqa_core.domain.documents import Chunk, ScoredChunk
from docqa_core.domain.errors import ConfigError
from docqa_core.providers.fakes._text import tokens
from docqa_core.providers.retrieval import embedders, rerankers, vector_stores

MIN_DIMENSION = 8
MAX_DIMENSION = 4096


@embedders.register("fake")
class FakeEmbedder:
    """Hashing-trick bag of words: each token adds +1 or -1 to one dimension, then L2-normalised.

    Deterministic across processes (it uses BLAKE2b, not Python's salted ``hash``). Texts that
    share words have positive cosine similarity; a text with no words embeds to all zeros.
    """

    def __init__(self, *, dimension: int = 64, model: str = "fake-embedder-v1") -> None:
        """Configure the vector size.

        Raises:
            ConfigError: If ``dimension`` is outside 8..4096.
        """
        if not MIN_DIMENSION <= dimension <= MAX_DIMENSION:
            raise ConfigError(
                f"fake embedder: dimension must be between {MIN_DIMENSION} and {MAX_DIMENSION}"
            )
        self._dimension = dimension
        self._model = model

    @property
    def model(self) -> str:
        """Model name recorded on every vector."""
        return self._model

    @property
    def dimension(self) -> int:
        """Vector length."""
        return self._dimension

    async def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed each text."""
        return [self._embed(text) for text in texts]

    async def embed_query(self, text: str) -> list[float]:
        """Embed a query in the same space as documents."""
        return self._embed(text)

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self._dimension
        for token in tokens(text):
            digest = hashlib.blake2b(token.encode(), digest_size=8).digest()
            index = int.from_bytes(digest[:4], "big") % self._dimension
            vector[index] += 1.0 if digest[4] & 1 else -1.0
        norm = math.sqrt(sum(value * value for value in vector))
        return [value / norm for value in vector] if norm else vector


@vector_stores.register("fake")
class InMemoryVectorStore:
    """Vectors in a dict, cosine similarity, tenant and principal-set pre-filter.

    The filter uses ``Principal.can_access``, the same rule as the Qdrant payload filter, and
    runs before scoring. Ties are broken by chunk id so results are deterministic.
    """

    def __init__(self, *, max_limit: int = 100) -> None:
        """Configure the largest ``limit`` a search may ask for.

        Raises:
            ConfigError: If ``max_limit`` is less than 1.
        """
        if max_limit < 1:
            raise ConfigError("in-memory vector store: max_limit must be at least 1")
        self._max_limit = max_limit
        self._entries: dict[UUID, tuple[Chunk, tuple[float, ...]]] = {}
        self._dimension: int | None = None

    async def upsert(self, chunks: Sequence[Chunk], vectors: Sequence[Sequence[float]]) -> None:
        """Insert or replace chunks by id.

        Raises:
            InvalidInputError: If counts differ or a vector has the wrong dimension.
        """
        require(len(chunks) == len(vectors), "upsert needs exactly one vector per chunk")
        for chunk, vector in zip(chunks, vectors, strict=True):
            self._check_dimension(vector)
            self._entries[chunk.id] = (chunk, tuple(vector))

    async def search(
        self, vector: Sequence[float], *, principal: Principal, limit: int
    ) -> list[ScoredChunk]:
        """Return up to ``limit`` visible chunks by cosine similarity, best first.

        Raises:
            InvalidInputError: If ``limit`` is out of range or the vector has the wrong size.
        """
        require(1 <= limit <= self._max_limit, f"limit must be between 1 and {self._max_limit}")
        if self._dimension is not None:
            self._check_dimension(vector)
        visible = [
            (chunk, stored)
            for chunk, stored in self._entries.values()
            if principal.can_access(tenant_id=chunk.tenant_id, acl_principals=chunk.acl_principals)
        ]
        scored = [ScoredChunk(chunk, _cosine(vector, stored)) for chunk, stored in visible]
        scored.sort(key=lambda item: (-item.score, str(item.chunk.id)))
        return scored[:limit]

    async def delete_document(self, *, tenant_id: UUID, document_id: UUID) -> int:
        """Remove every chunk of one document in one tenant."""
        doomed = [
            chunk_id
            for chunk_id, (chunk, _) in self._entries.items()
            if chunk.tenant_id == tenant_id and chunk.document_id == document_id
        ]
        for chunk_id in doomed:
            del self._entries[chunk_id]
        return len(doomed)

    def _check_dimension(self, vector: Sequence[float]) -> None:
        if self._dimension is None:
            require(len(vector) > 0, "vectors must not be empty")
            self._dimension = len(vector)
        require(len(vector) == self._dimension, f"vectors must have {self._dimension} values")


@rerankers.register("fake")
class LexicalReranker:
    """Scores each candidate by the share of distinct query words it contains (0..1).

    Python's sort is stable, so candidates with equal scores keep their incoming order.
    """

    async def rerank(
        self, query: str, candidates: Sequence[ScoredChunk], *, limit: int
    ) -> list[ScoredChunk]:
        """Return up to ``limit`` candidates by query-word coverage, best first.

        Raises:
            InvalidInputError: If ``limit`` is less than 1.
        """
        require(limit >= 1, "limit must be at least 1")
        wanted = set(tokens(query))
        rescored = [
            ScoredChunk(item.chunk, _coverage(wanted, item.chunk.text)) for item in candidates
        ]
        rescored.sort(key=lambda item: -item.score)
        return rescored[:limit]


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    norms = math.sqrt(sum(a * a for a in left)) * math.sqrt(sum(b * b for b in right))
    return dot / norms if norms else 0.0


def _coverage(wanted: set[str], text: str) -> float:
    if not wanted:
        return 0.0
    return len(wanted & set(tokens(text))) / len(wanted)
