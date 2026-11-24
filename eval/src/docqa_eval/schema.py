"""Schema for golden-set items: questions, expected behaviour and gold evidence."""

from __future__ import annotations

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

QuestionType = Literal[
    "factual",
    "multi_hop",
    "aggregation",
    "unanswerable",
    "acl_trap",
    "conversational",
]
ExpectedBehavior = Literal["answer", "abstain", "deny"]


class GoldEvidence(BaseModel):
    """One piece of evidence a correct answer must be grounded in."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    doc_id: str = Field(min_length=1)
    page: int | None = Field(default=None, ge=1)
    chunk_id: str | None = None
    quote: str | None = None


class GoldenItem(BaseModel):
    """One golden question with its expected evidence and expected behaviour."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    asking_user: str = Field(min_length=1)
    question: str = Field(min_length=1)
    question_type: QuestionType
    expected_behavior: ExpectedBehavior
    gold: list[GoldEvidence] = Field(default_factory=list)
    reference_answer: str | None = None
    tags: list[str] = Field(default_factory=list)
    notes: str | None = None

    @model_validator(mode="after")
    def _check_consistency(self) -> Self:
        if self.expected_behavior == "answer":
            if not self.gold:
                raise ValueError(f"{self.id}: expected_behavior 'answer' requires gold evidence")
            if not self.reference_answer:
                raise ValueError(f"{self.id}: expected_behavior 'answer' requires reference_answer")
        if self.question_type == "unanswerable":
            if self.expected_behavior != "abstain":
                raise ValueError(
                    f"{self.id}: unanswerable items must have expected_behavior 'abstain'"
                )
            if self.gold:
                raise ValueError(f"{self.id}: unanswerable items must have empty gold")
        if self.question_type == "acl_trap" and self.expected_behavior not in ("abstain", "deny"):
            raise ValueError(f"{self.id}: acl_trap items must expect 'abstain' or 'deny'")
        return self
