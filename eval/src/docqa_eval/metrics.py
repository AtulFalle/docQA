"""Binary-relevance retrieval metrics.

All functions take retrieved document (or chunk) ids in rank order and the set of relevant ids.
Conventions for degenerate cases:

* An empty ``relevant`` collection scores 0.0 on every metric (no relevant item can be found).
* ``precision_at_k`` divides by ``k`` even when fewer than ``k`` results were retrieved, so an
  under-filled result list is penalised rather than rewarded.
* ``k`` must be at least 1; smaller values raise ``ValueError``.
"""

from __future__ import annotations

import math
from collections.abc import Collection, Sequence


def _top_k(retrieved: Sequence[str], k: int) -> Sequence[str]:
    if k < 1:
        raise ValueError(f"k must be >= 1, got {k}")
    return retrieved[:k]


def recall_at_k(retrieved: Sequence[str], relevant: Collection[str], k: int) -> float:
    """Fraction of relevant items that appear in the top ``k``."""
    rel = set(relevant)
    top = _top_k(retrieved, k)
    if not rel:
        return 0.0
    return sum(1 for doc in top if doc in rel) / len(rel)


def precision_at_k(retrieved: Sequence[str], relevant: Collection[str], k: int) -> float:
    """Fraction of the top ``k`` slots that hold relevant items."""
    rel = set(relevant)
    top = _top_k(retrieved, k)
    if not rel:
        return 0.0
    return sum(1 for doc in top if doc in rel) / k


def hit_rate_at_k(retrieved: Sequence[str], relevant: Collection[str], k: int) -> float:
    """1.0 if at least one relevant item appears in the top ``k``, else 0.0."""
    rel = set(relevant)
    top = _top_k(retrieved, k)
    return 1.0 if any(doc in rel for doc in top) else 0.0


def reciprocal_rank(retrieved: Sequence[str], relevant: Collection[str]) -> float:
    """1 / rank of the first relevant item, or 0.0 if none is retrieved."""
    rel = set(relevant)
    for rank, doc in enumerate(retrieved, start=1):
        if doc in rel:
            return 1.0 / rank
    return 0.0


def mrr(runs: Sequence[tuple[Sequence[str], Collection[str]]]) -> float:
    """Mean reciprocal rank over ``(retrieved, relevant)`` pairs; 0.0 for no runs."""
    if not runs:
        return 0.0
    return sum(reciprocal_rank(retrieved, relevant) for retrieved, relevant in runs) / len(runs)


def ndcg_at_k(retrieved: Sequence[str], relevant: Collection[str], k: int) -> float:
    """Normalised DCG with binary gains and log2 position discounts."""
    rel = set(relevant)
    top = _top_k(retrieved, k)
    if not rel:
        return 0.0
    dcg = sum(1.0 / math.log2(i + 1) for i, doc in enumerate(top, start=1) if doc in rel)
    ideal = sum(1.0 / math.log2(i + 1) for i in range(1, min(k, len(rel)) + 1))
    return dcg / ideal
