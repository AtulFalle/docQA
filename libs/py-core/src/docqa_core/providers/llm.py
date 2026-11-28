"""The language-model interface and its registry."""

from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable

from docqa_core.domain.llm import LLMRequest, LLMResponse
from docqa_core.registry import Registry


@runtime_checkable
class LLMProvider(Protocol):
    """Generates text from messages. Implementations are self-hosted (ADR 0003).

    The model is chosen by the provider's own parameters, never by the caller. Failures are
    raised as ``ProviderError`` subclasses, so callers can decide whether to retry.
    """

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Return the whole reply at once, with the model name and usage."""

    def stream(self, request: LLMRequest) -> AsyncIterator[str]:
        """Yield the reply in pieces. Joined, the pieces equal ``generate``'s text."""

    async def aclose(self) -> None:
        """Release connections. Safe to call more than once."""


llms: Registry[LLMProvider] = Registry("llm")
