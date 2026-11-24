"""Hand-computed checks for the retrieval metrics, including degenerate cases."""

from __future__ import annotations

import math
from collections.abc import Callable

import pytest

from docqa_eval.metrics import (
    hit_rate_at_k,
    mrr,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)

# Ranked list used by several tests: a, b, c, d. Relevant set {a, c, x}.
RANKED = ["a", "b", "c", "d"]
RELEVANT = {"a", "c", "x"}


def test_recall_at_k_top3() -> None:
    # Top 3 = a, b, c. Hits a and c out of 3 relevant -> 2/3.
    assert recall_at_k(RANKED, RELEVANT, 3) == pytest.approx(2 / 3)


def test_recall_at_k_k_larger_than_list() -> None:
    # Only two results exist and both are relevant -> recall 2/2.
    assert recall_at_k(["a", "b"], {"a", "b"}, 5) == 1.0


def test_recall_at_k_empty_relevant_is_zero() -> None:
    assert recall_at_k(RANKED, set(), 3) == 0.0


def test_precision_at_k_top3() -> None:
    # Top 3 holds a and c -> 2 hits out of 3 slots.
    assert precision_at_k(RANKED, RELEVANT, 3) == pytest.approx(2 / 3)


def test_precision_at_k_k_larger_than_list_uses_k_as_denominator() -> None:
    # One hit (a) out of k = 5 slots, even though only two results came back.
    assert precision_at_k(["a", "b"], {"a"}, 5) == pytest.approx(0.2)


def test_precision_at_k_k_one_miss() -> None:
    # Top 2 = a, b; only a is relevant -> 1/2.
    assert precision_at_k(["a", "b", "c"], {"a"}, 2) == 0.5


def test_precision_at_k_empty_relevant_is_zero() -> None:
    assert precision_at_k(RANKED, [], 3) == 0.0


def test_hit_rate_hit_inside_k() -> None:
    assert hit_rate_at_k(["x", "a"], {"a"}, 2) == 1.0


def test_hit_rate_hit_outside_k() -> None:
    assert hit_rate_at_k(["x", "a"], {"a"}, 1) == 0.0


def test_hit_rate_empty_relevant_is_zero() -> None:
    assert hit_rate_at_k(RANKED, set(), 4) == 0.0


def test_reciprocal_rank_third_position() -> None:
    assert reciprocal_rank(["x", "y", "a"], {"a"}) == pytest.approx(1 / 3)


def test_reciprocal_rank_not_retrieved_is_zero() -> None:
    assert reciprocal_rank(["x", "y"], {"a"}) == 0.0


def test_reciprocal_rank_empty_relevant_is_zero() -> None:
    assert reciprocal_rank(RANKED, set()) == 0.0


def test_mrr_mixed_runs() -> None:
    # RR values: 1/2 (b at rank 2), 0 (nothing relevant), 1 (e at rank 1). Mean = 0.5.
    runs = [(["a", "b"], {"b"}), (["c", "d"], {"x"}), (["e"], {"e"})]
    assert mrr(runs) == pytest.approx(0.5)


def test_mrr_no_runs_is_zero() -> None:
    assert mrr([]) == 0.0


def test_ndcg_single_relevant_at_rank_two() -> None:
    # DCG = 1/log2(3) = 0.6309297536; ideal for one relevant item is 1.0.
    assert ndcg_at_k(["x", "a"], {"a"}, 2) == pytest.approx(0.6309297536, abs=1e-9)


def test_ndcg_perfect_ranking_is_one() -> None:
    assert ndcg_at_k(["a", "c", "x"], {"a", "c"}, 3) == pytest.approx(1.0)


def test_ndcg_mixed_top3() -> None:
    # DCG = 1 + 1/log2(4) = 1.5.
    # IDCG for 3 relevant items = 1 + 1/log2(3) + 1/log2(4) = 2.1309297536.
    # nDCG = 1.5 / 2.1309297536 = 0.703918.
    assert ndcg_at_k(RANKED, RELEVANT, 3) == pytest.approx(0.703918, abs=1e-6)


def test_ndcg_k_larger_than_list_is_one_when_all_found() -> None:
    # Two relevant items, both retrieved; the ideal list also has only two slots filled.
    assert ndcg_at_k(["a", "b"], {"a", "b"}, 5) == pytest.approx(1.0)


def test_ndcg_empty_relevant_is_zero() -> None:
    assert ndcg_at_k(RANKED, set(), 3) == 0.0


def test_ndcg_discount_matches_log_formula() -> None:
    expected = (1 / math.log2(2)) / (1 / math.log2(2))
    assert ndcg_at_k(["a"], {"a"}, 1) == pytest.approx(expected)


@pytest.mark.parametrize(
    "metric",
    [recall_at_k, precision_at_k, hit_rate_at_k, ndcg_at_k],
)
def test_k_below_one_is_rejected(metric: Callable[[list[str], set[str], int], float]) -> None:
    with pytest.raises(ValueError, match="k must be >= 1"):
        metric(RANKED, RELEVANT, 0)
