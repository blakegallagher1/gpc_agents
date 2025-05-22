import pytest

from agents.guardrails import profanity_filter, enforce_citation_json
from agents.structures import AnswerWithCitations, Citation

@pytest.mark.asyncio
async def test_profanity_filter_blocks():
    out = await profanity_filter.guardrail_function(None, None, "you are a bitch")  # type: ignore[arg-type]
    assert out.tripwire_triggered


@pytest.mark.asyncio
async def test_profanity_filter_passes():
    out = await profanity_filter.guardrail_function(None, None, "Hello world")  # type: ignore[arg-type]
    assert not out.tripwire_triggered


@pytest.mark.asyncio
async def test_enforce_citation_json_pass_dataclass():
    payload = AnswerWithCitations(answer="ok", citations=[Citation(section="§1", page="2")])
    out = await enforce_citation_json.guardrail_function(None, None, payload)  # type: ignore[arg-type]
    assert not out.tripwire_triggered


@pytest.mark.asyncio
async def test_enforce_citation_json_fail():
    bad = {"text": "oops"}
    out = await enforce_citation_json.guardrail_function(None, None, bad)  # type: ignore[arg-type]
    assert out.tripwire_triggered