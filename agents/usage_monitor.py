from __future__ import annotations

import os
import sqlite3
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Tuple

from gpc_agents.src.agents import RunResult, Runner

DB_PATH = Path(os.path.dirname(__file__)) / "data" / "usage.sqlite3"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Cost per 1K tokens in USD – adapt as needed per model tier.
_COST_PER_1K_TOKENS = float(os.getenv("OPENAI_COST_PER_1K", "0.005"))
_DAILY_BUDGET_USD = float(os.getenv("OPENAI_DAILY_BUDGET", "10.0"))


class BudgetExceededError(RuntimeError):
    """Raised when the daily OpenAI spend would exceed budget."""


# ---------------------------------------------------------------------------
# SQLite helpers
# ---------------------------------------------------------------------------


def _init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS usage (
            ts TEXT NOT NULL,
            prompt_tokens INTEGER NOT NULL,
            completion_tokens INTEGER NOT NULL,
            cost_usd REAL NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


_init_db()


def _log_usage(prompt_tokens: int, completion_tokens: int) -> None:
    cost = ((prompt_tokens + completion_tokens) / 1000) * _COST_PER_1K_TOKENS
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO usage (ts, prompt_tokens, completion_tokens, cost_usd) VALUES (?, ?, ?, ?)",
        (datetime.utcnow().isoformat(), prompt_tokens, completion_tokens, cost),
    )
    conn.commit()
    conn.close()


def _spent_last_24h() -> float:
    since = datetime.utcnow() - timedelta(days=1)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("SELECT SUM(cost_usd) FROM usage WHERE ts >= ?", (since.isoformat(),))
    row = cur.fetchone()
    conn.close()
    return float(row[0] or 0.0)


async def run_with_budget(
    *,
    starting_agent,
    input: str,
    context: Any | None = None,
    max_turns: int = 10,
) -> RunResult:
    """Run agent respecting daily budget + log usage.

    Raises BudgetExceededError if projected spend would exceed _DAILY_BUDGET_USD.
    """

    # Pre-budget check (rough approximate cost per run). If about to exceed, abort early.
    if _spent_last_24h() >= _DAILY_BUDGET_USD:
        raise BudgetExceededError("Daily OpenAI budget exceeded; aborting run.")

    result = await Runner.run(
        starting_agent=starting_agent,
        input=input,
        context=context or {},
        max_turns=max_turns,
    )

    # SDK records token usage per response; sum over raw_responses
    prompt_tokens = sum(r.prompt_tokens or 0 for r in result.raw_responses)
    completion_tokens = sum(r.completion_tokens or 0 for r in result.raw_responses)
    _log_usage(prompt_tokens, completion_tokens)

    if _spent_last_24h() > _DAILY_BUDGET_USD:
        # Rollback last log to respect budget
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "DELETE FROM usage WHERE rowid = (SELECT MAX(rowid) FROM usage)")
        conn.commit()
        conn.close()
        raise BudgetExceededError("Run would exceed daily budget; aborted post-factum and rolled back log.")

    return result

__all__ = [
    "run_with_budget",
    "BudgetExceededError",
] 