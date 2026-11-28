"""LLM requests, responses and usage."""

import pytest

from docqa_core.domain import (
    FinishReason,
    InvalidInputError,
    LLMRequest,
    LLMResponse,
    Message,
    Role,
    Usage,
)
from docqa_core.value_sets import UsageKind

MESSAGES = (Message(Role.SYSTEM, "Use only the sources."), Message(Role.USER, "How is leave?"))


def make_usage(**overrides: object) -> Usage:
    values: dict[str, object] = {
        "kind": UsageKind.GENERATION,
        "provider": "fake",
        "model": "fake-1",
    }
    values.update(overrides)
    return Usage(**values)  # type: ignore[arg-type]


def test_llm_request_defaults_to_deterministic_sampling():
    request = LLMRequest(messages=MESSAGES, max_output_tokens=256)

    assert request.temperature == 0.0
    assert request.stop == ()


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"messages": ()}, "at least one message"),
        ({"max_output_tokens": 0}, "max_output_tokens"),
        ({"temperature": -0.1}, "temperature"),
        ({"temperature": 2.5}, "temperature"),
    ],
)
def test_llm_request_rejects_invalid_values(overrides, message):
    values: dict[str, object] = {"messages": MESSAGES, "max_output_tokens": 256}
    values.update(overrides)

    with pytest.raises(InvalidInputError, match=message):
        LLMRequest(**values)  # type: ignore[arg-type]


def test_llm_response_reports_model_usage_and_finish_reason():
    response = LLMResponse(text="Monthly [1].", model="fake-1", usage=make_usage(output_tokens=3))

    assert response.finish_reason is FinishReason.STOP
    assert response.usage.output_tokens == 3


def test_usage_counts_default_to_zero():
    usage = make_usage()

    assert (usage.input_tokens, usage.output_tokens, usage.units) == (0, 0, 0)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"provider": " "}, "provider"),
        ({"model": ""}, "model"),
        ({"input_tokens": -1}, "negative"),
        ({"output_tokens": -1}, "negative"),
        ({"units": -1}, "negative"),
    ],
)
def test_usage_rejects_invalid_values(overrides, message):
    with pytest.raises(InvalidInputError, match=message):
        make_usage(**overrides)


def test_role_and_finish_reason_values_are_stable():
    assert [role.value for role in Role] == ["system", "user", "assistant"]
    assert [reason.value for reason in FinishReason] == ["stop", "length"]
