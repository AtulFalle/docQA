"""Contract every LLM provider must satisfy. Runs once per registered provider.

A provider is built with no parameters here, so every parameter needs a safe default.
"""

import pytest

import docqa_core.providers.fakes  # noqa: F401  # registers the built-in providers
from docqa_core.domain import LLMRequest, LLMResponse, Message, Role
from docqa_core.providers import LLMProvider, llms
from docqa_core.value_sets import UsageKind

REQUEST = LLMRequest(
    messages=(
        Message(Role.SYSTEM, "Answer only from the sources."),
        Message(Role.USER, "How many days of annual leave do employees get?"),
    ),
    max_output_tokens=64,
)


@pytest.fixture(params=llms.names())
async def llm(request: pytest.FixtureRequest):
    provider = llms.create(request.param)
    yield provider
    await provider.aclose()


def test_llm_contract_provider_implements_the_protocol(llm):
    assert isinstance(llm, LLMProvider)


async def test_llm_contract_generate_returns_text_model_and_generation_usage(llm):
    response = await llm.generate(REQUEST)

    assert isinstance(response, LLMResponse)
    assert response.text.strip()
    assert response.model
    assert response.usage.kind is UsageKind.GENERATION
    assert response.usage.model == response.model
    assert response.usage.output_tokens <= REQUEST.max_output_tokens


async def test_llm_contract_stream_joins_to_the_generated_text(llm):
    expected = (await llm.generate(REQUEST)).text

    pieces = [piece async for piece in llm.stream(REQUEST)]

    assert pieces
    assert "".join(pieces) == expected


async def test_llm_contract_respects_a_small_output_limit(llm):
    short = LLMRequest(messages=REQUEST.messages, max_output_tokens=2)

    response = await llm.generate(short)

    assert response.usage.output_tokens <= 2


async def test_llm_contract_aclose_can_be_called_twice(llm):
    await llm.aclose()
    await llm.aclose()
