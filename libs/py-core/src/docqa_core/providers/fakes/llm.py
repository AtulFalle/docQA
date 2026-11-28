"""A deterministic LLM for tests and local runs, with failure and latency injection."""

import asyncio
from collections.abc import AsyncIterator

from docqa_core.domain.errors import (
    ConfigError,
    ContextTooLongError,
    ProviderError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    RateLimitedError,
)
from docqa_core.domain.llm import FinishReason, LLMRequest, LLMResponse, Role, Usage
from docqa_core.providers.llm import llms
from docqa_core.value_sets import UsageKind

FAILURES: dict[str, type[ProviderError]] = {
    "unavailable": ProviderUnavailableError,
    "timeout": ProviderTimeoutError,
    "rate_limited": RateLimitedError,
    "context_too_long": ContextTooLongError,
}
_QUESTION_CHARS = 200


@llms.register("fake")
class FakeLLM:
    """Replies with a fixed or derived text that cites source ``[1]``.

    Without ``reply``, the text is ``Fake answer to: <last user message> [1]``. Output is cut to
    ``max_output_tokens`` words (finish reason ``length``). Usage counts words as tokens.

    Failure injection: ``fail_with`` names an error (see ``FAILURES``); with ``fail_times`` only
    the first N calls fail, which is how retry logic is tested.
    """

    def __init__(
        self,
        *,
        model: str = "fake-llm",
        reply: str | None = None,
        latency_ms: int = 0,
        fail_with: str | None = None,
        fail_times: int | None = None,
    ) -> None:
        """Configure the fake.

        Raises:
            ConfigError: If ``fail_with`` is unknown or a number is negative.
        """
        if fail_with is not None and fail_with not in FAILURES:
            known = ", ".join(sorted(FAILURES))
            raise ConfigError(f"fake llm: unknown fail_with {fail_with!r}; use one of {known}")
        if latency_ms < 0 or (fail_times is not None and fail_times < 0):
            raise ConfigError("fake llm: latency_ms and fail_times must not be negative")
        self.model = model
        self._reply = reply
        self._latency_s = latency_ms / 1000
        self._fail_with = fail_with
        self._fail_times = fail_times
        self.calls = 0
        self.closed = False

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Return the fake reply, or raise the configured failure."""
        if self.closed:
            raise ProviderUnavailableError("fake llm is closed", retryable=False)
        self.calls += 1
        if self._latency_s:
            await asyncio.sleep(self._latency_s)
        self._maybe_fail()
        words = self._text_for(request).split(" ")
        truncated = len(words) > request.max_output_tokens
        words = words[: request.max_output_tokens]
        prompt_tokens = sum(len(message.content.split()) for message in request.messages)
        return LLMResponse(
            text=" ".join(words),
            model=self.model,
            usage=Usage(
                kind=UsageKind.GENERATION,
                provider="fake",
                model=self.model,
                input_tokens=prompt_tokens,
                output_tokens=len(words),
            ),
            finish_reason=FinishReason.LENGTH if truncated else FinishReason.STOP,
        )

    async def stream(self, request: LLMRequest) -> AsyncIterator[str]:
        """Yield the reply word by word; the pieces join back to ``generate``'s text."""
        response = await self.generate(request)
        words = response.text.split(" ")
        for index, word in enumerate(words):
            yield word if index == len(words) - 1 else f"{word} "

    async def aclose(self) -> None:
        """Mark the fake closed. Later calls fail as if the provider were gone."""
        self.closed = True

    def _maybe_fail(self) -> None:
        if self._fail_with is None:
            return
        if self._fail_times is not None and self.calls > self._fail_times:
            return
        raise FAILURES[self._fail_with](f"fake llm injected failure: {self._fail_with}")

    def _text_for(self, request: LLMRequest) -> str:
        if self._reply is not None:
            return self._reply
        questions = [m.content for m in request.messages if m.role is Role.USER]
        if not questions:
            return "Fake answer [1]"
        question = " ".join(questions[-1].split())[:_QUESTION_CHARS]
        return f"Fake answer to: {question} [1]"
