from __future__ import annotations

import asyncio
import sys
from typing import List

from gpc_agents.src.agents import Agent, Runner

from .guardrails import enforce_citation_json, profanity_filter
from .specialists import ALL_SPECIALISTS
from .config import DEFAULT_MODEL
from .persistence import persist_run_result
from .structures import AnswerWithCitations

# ---------------------------------------------------------------------------
# Build master orchestrator agent – delegates via handoffs.
# ---------------------------------------------------------------------------

HANDOFFS: List[Agent] = list(ALL_SPECIALISTS.values())

ORCHESTRATOR = Agent[
    dict  # Context placeholder – can be extended later
](
    name="EBR Zoning Code Master Orchestrator",
    instructions=(
        "You are the Master Orchestrator for the East Baton Rouge Zoning Code Q&A system. "
        "Analyse the user's question and decide which specialist agent (provided via handoffs) can "
        "best answer. If multiple apply choose the most relevant single agent. "
        "After receiving that agent's answer, return it verbatim."
    ),
    handoffs=HANDOFFS,
    model=DEFAULT_MODEL,
    input_guardrails=[profanity_filter],
    output_guardrails=[enforce_citation_json],
    output_type=AnswerWithCitations,
)

# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:  # noqa: D401 – CLI helper
    question = (
        " ".join(sys.argv[1:])
        if len(sys.argv) > 1
        else "What are the zoning districts in East Baton Rouge Parish?"
    )

    result = asyncio.run(
        Runner.run(
            starting_agent=ORCHESTRATOR,
            input=question,
            context={},
            max_turns=10,  # safety net
        )
    )

    print(result.final_output)

    # Persist for audits / fine-tuning
    path = persist_run_result(result)
    print(f"[info] run saved to {path}")


if __name__ == "__main__":
    main()