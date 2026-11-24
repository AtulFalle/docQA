"""Validator rules for GoldenItem."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from docqa_eval.schema import GoldenItem


def _payload(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "id": "t-1",
        "tenant_id": "tenant_demo",
        "asking_user": "u_hr_1",
        "question": "How many years of Python does Priya have?",
        "question_type": "factual",
        "expected_behavior": "answer",
        "gold": [{"doc_id": "resume_priya_sharma", "page": 1}],
        "reference_answer": "7 years.",
    }
    data.update(overrides)
    return data


def test_valid_answer_item_passes() -> None:
    item = GoldenItem.model_validate(_payload())
    assert item.gold[0].doc_id == "resume_priya_sharma"
    assert item.tags == []


def test_answer_without_gold_is_rejected() -> None:
    with pytest.raises(ValidationError, match="requires gold evidence"):
        GoldenItem.model_validate(_payload(gold=[]))


def test_answer_without_reference_is_rejected() -> None:
    with pytest.raises(ValidationError, match="requires reference_answer"):
        GoldenItem.model_validate(_payload(reference_answer=None))


def test_unanswerable_abstain_with_empty_gold_passes() -> None:
    item = GoldenItem.model_validate(
        _payload(
            question_type="unanswerable",
            expected_behavior="abstain",
            gold=[],
            reference_answer=None,
        )
    )
    assert item.gold == []


def test_unanswerable_expecting_answer_is_rejected() -> None:
    with pytest.raises(ValidationError, match="must have expected_behavior 'abstain'"):
        GoldenItem.model_validate(_payload(question_type="unanswerable"))


def test_unanswerable_with_gold_is_rejected() -> None:
    with pytest.raises(ValidationError, match="must have empty gold"):
        GoldenItem.model_validate(
            _payload(
                question_type="unanswerable",
                expected_behavior="abstain",
                reference_answer=None,
            )
        )


@pytest.mark.parametrize("behavior", ["abstain", "deny"])
def test_acl_trap_with_refusal_passes(behavior: str) -> None:
    item = GoldenItem.model_validate(
        _payload(
            question_type="acl_trap",
            expected_behavior=behavior,
            gold=[],
            reference_answer=None,
        )
    )
    assert item.expected_behavior == behavior


def test_acl_trap_expecting_answer_is_rejected() -> None:
    with pytest.raises(ValidationError, match="acl_trap items must expect"):
        GoldenItem.model_validate(_payload(question_type="acl_trap"))


def test_unknown_question_type_is_rejected() -> None:
    with pytest.raises(ValidationError):
        GoldenItem.model_validate(_payload(question_type="trivia"))


def test_page_below_one_is_rejected() -> None:
    with pytest.raises(ValidationError):
        GoldenItem.model_validate(_payload(gold=[{"doc_id": "x", "page": 0}]))


def test_unknown_field_is_rejected() -> None:
    with pytest.raises(ValidationError):
        GoldenItem.model_validate(_payload(difficulty="hard"))


def test_empty_question_is_rejected() -> None:
    with pytest.raises(ValidationError):
        GoldenItem.model_validate(_payload(question=""))
