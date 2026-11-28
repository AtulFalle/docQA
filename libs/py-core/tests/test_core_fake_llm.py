"""FakeLLM behaviour: replies, truncation, latency and failure injection."""

import pytest

from docqa_core.domain import (
    ConfigError,
    ContextTooLongError,
    FinishReason,
    LLMRequest,
    Message,
    ProviderTimeoutError,
    ProviderUnavailableError,
    RateLimitedError,
    Role,
)
from docqa_core.providers import llms
from docqa_core.providers.fakes import FakeLLM


def ask(question: str = "How is leave accrued?", *, max_output_tokens: int = 64) -> LLMRequest:
    return LLMRequest(
        messages=(Message(Role.SYSTEM, "Use only the sources."), Message(Role.USER, question)),
        max_output_tokens=max_output_tokens,
    )


def test_fake_llm_is_registered_as_fake():
    assert llms.get("fake") is FakeLLM


async def test_fake_llm_answers_the_last_user_message_and_cites_source_one():
    response = await FakeLLM().generate(ask("How is leave accrued?"))

    assert response.text == "Fake answer to: How is leave accrued? [1]"
    assert response.finish_reason is FinishReason.STOP
    assert response.model == "fake-llm"


async def test_fake_llm_uses_a_fixed_reply_when_configured():
    response = await FakeLLM(reply="Leave accrues monthly [1].").generate(ask())

    assert response.text == "Leave accrues monthly [1]."


async def test_fake_llm_without_a_user_message_still_cites():
    request = LLMRequest(messages=(Message(Role.SYSTEM, "x"),), max_output_tokens=8)

    assert (await FakeLLM().generate(request)).text == "Fake answer [1]"


async def test_fake_llm_counts_words_as_tokens():
    response = await FakeLLM(reply="one two three").generate(ask("a b c d"))

    assert response.usage.output_tokens == 3
    assert response.usage.input_tokens == 4 + 4  # "Use only the sources." + "a b c d"


async def test_fake_llm_truncates_to_max_output_tokens():
    response = await FakeLLM(reply="one two three four").generate(ask(max_output_tokens=2))

    assert response.text == "one two"
    assert response.finish_reason is FinishReason.LENGTH


@pytest.mark.parametrize(
    ("fail_with", "error_type", "retryable"),
    [
        ("unavailable", ProviderUnavailableError, True),
        ("timeout", ProviderTimeoutError, True),
        ("rate_limited", RateLimitedError, True),
        ("context_too_long", ContextTooLongError, False),
    ],
)
async def test_fake_llm_injects_the_configured_failure(fail_with, error_type, retryable):
    with pytest.raises(error_type) as info:
        await FakeLLM(fail_with=fail_with).generate(ask())

    assert info.value.retryable is retryable


async def test_fake_llm_fails_only_the_first_n_calls():
    llm = FakeLLM(fail_with="unavailable", fail_times=2)

    for _ in range(2):
        with pytest.raises(ProviderUnavailableError):
            await llm.generate(ask())
    response = await llm.generate(ask())

    assert response.text
    assert llm.calls == 3


async def test_fake_llm_stream_fails_like_generate():
    llm = FakeLLM(fail_with="timeout")

    with pytest.raises(ProviderTimeoutError):
        [piece async for piece in llm.stream(ask())]


async def test_fake_llm_with_latency_still_answers():
    assert (await FakeLLM(latency_ms=1).generate(ask())).text


async def test_closed_fake_llm_refuses_calls_without_retry():
    llm = FakeLLM()
    await llm.aclose()

    with pytest.raises(ProviderUnavailableError) as info:
        await llm.generate(ask())
    assert info.value.retryable is False


@pytest.mark.parametrize(
    ("params", "message"),
    [
        ({"fail_with": "explode"}, "unknown fail_with 'explode'"),
        ({"latency_ms": -1}, "must not be negative"),
        ({"fail_with": "timeout", "fail_times": -1}, "must not be negative"),
    ],
)
def test_fake_llm_rejects_bad_configuration(params, message):
    with pytest.raises(ConfigError, match=message):
        llms.create("fake", **params)
