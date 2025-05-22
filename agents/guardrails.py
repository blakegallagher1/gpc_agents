import json
import re
import os
from typing import Any

from gpc_agents.src.agents import (
    InputGuardrailResult,
    OutputGuardrailResult,
    GuardrailFunctionOutput,
    input_guardrail,
    output_guardrail,
)

from .structures import AnswerWithCitations
import spacy
from cryptography.fernet import Fernet

# ---------------------------------------------------------------------------
# Input guardrail – basic sanitisation (extensible)
# ---------------------------------------------------------------------------

_PROFANITY_PATTERN = re.compile(
    r"\b(fuck|shit|bitch|cunt|asshole|nigger|faggot)\b", re.IGNORECASE
)

PII_PATTERN = re.compile(r"(\b\d{3}-\d{2}-\d{4}\b|\b\d{3}-\d{3}-\d{4}\b|[\w.-]+@[\w.-]+\.[A-Za-z]{2,6})")

try:
    _NLP = spacy.load("en_core_web_sm")
except OSError:
    _NLP = None  # spaCy model missing.

TOKEN_LIMIT = int(os.getenv("PROMPT_TOKEN_LIMIT", "800"))

@input_guardrail
async def profanity_filter(_, __, user_input: str) -> GuardrailFunctionOutput:  # type: ignore[override]
    """Reject prompts containing offensive slurs or profanity."""

    triggered = bool(_PROFANITY_PATTERN.search(user_input or ""))
    return GuardrailFunctionOutput(output_info={}, tripwire_triggered=triggered)


@input_guardrail
async def pii_filter(_, __, user_input: str) -> GuardrailFunctionOutput:  # type: ignore[override]
    if PII_PATTERN.search(user_input or ""):
        return GuardrailFunctionOutput(output_info="regex_pii", tripwire_triggered=True)

    if _NLP:
        ents = _NLP(user_input).ents
        if any(ent.label_ in {"PERSON", "GPE", "LOC", "ORG", "DATE", "CARDINAL"} for ent in ents):
            return GuardrailFunctionOutput(output_info="ner_pii", tripwire_triggered=True)

    return GuardrailFunctionOutput(output_info="clean", tripwire_triggered=False)


def _count_tokens(text: str) -> int:
    return len(text.split())


@input_guardrail
async def length_guardrail(_, __, user_input: str) -> GuardrailFunctionOutput:  # type: ignore[override]
    if _count_tokens(user_input) > TOKEN_LIMIT:
        return GuardrailFunctionOutput(output_info="too_long", tripwire_triggered=True)
    return GuardrailFunctionOutput(output_info="ok", tripwire_triggered=False)


# ---------------------------------------------------------------------------
# Output guardrail – force AnswerWithCitations JSON structure
# ---------------------------------------------------------------------------


@output_guardrail
async def enforce_citation_json(_, __, output: Any) -> GuardrailFunctionOutput:  # type: ignore[override]
    """Ensure the agent returns the expected AnswerWithCitations payload."""

    # Case 1: already dataclass instance
    if isinstance(output, AnswerWithCitations):
        return GuardrailFunctionOutput(output_info="dataclass", tripwire_triggered=False)

    # Parse JSON/dict path
    if isinstance(output, str):
        try:
            parsed = json.loads(output)
        except json.JSONDecodeError as exc:
            return GuardrailFunctionOutput(output_info="invalid json", tripwire_triggered=True)
    else:
        parsed = output

    valid = (
        isinstance(parsed, dict)
        and "answer" in parsed
        and "citations" in parsed
        and isinstance(parsed["citations"], list)
        and all(isinstance(c, dict) and {"section", "page"}.issubset(c) for c in parsed["citations"])
    )

    return GuardrailFunctionOutput(output_info="schema_check", tripwire_triggered=not valid)


__all__ = [
    "profanity_filter",
    "enforce_citation_json",
    "pii_filter",
    "length_guardrail",
] 