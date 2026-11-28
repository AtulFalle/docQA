"""Requests to and responses from a language model, and the usage they record.

The model name is not part of the request: providers read it from ``Settings`` (see
``docs/engineering/rag-and-llm.md``) and report it back on the response for provenance.
"""

import enum
from dataclasses import dataclass

from docqa_core.domain._checks import require
from docqa_core.value_sets import UsageKind

MAX_TEMPERATURE = 2.0


class Role(enum.StrEnum):
    """Who wrote a message in a conversation with the model."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class FinishReason(enum.StrEnum):
    """Why the model stopped writing."""

    STOP = "stop"
    LENGTH = "length"


@dataclass(frozen=True, slots=True)
class Message:
    """One message sent to the model."""

    role: Role
    content: str


@dataclass(frozen=True, slots=True, kw_only=True)
class Usage:
    """What one provider call consumed. Cost is worked out later from ``model_prices``."""

    kind: UsageKind
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    units: int = 0

    def __post_init__(self) -> None:
        """Validate the counts."""
        require(bool(self.provider.strip()), "usage needs a provider")
        require(bool(self.model.strip()), "usage needs a model")
        require(
            min(self.input_tokens, self.output_tokens, self.units) >= 0,
            "usage counts must not be negative",
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class LLMRequest:
    """A generation request: the messages plus sampling limits."""

    messages: tuple[Message, ...]
    max_output_tokens: int
    temperature: float = 0.0
    stop: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate the request."""
        require(len(self.messages) > 0, "a request needs at least one message")
        require(self.max_output_tokens > 0, "max_output_tokens must be positive")
        require(
            0.0 <= self.temperature <= MAX_TEMPERATURE,
            f"temperature must be between 0 and {MAX_TEMPERATURE}",
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class LLMResponse:
    """The model's reply, with the model that wrote it and what the call used."""

    text: str
    model: str
    usage: Usage
    finish_reason: FinishReason = FinishReason.STOP
