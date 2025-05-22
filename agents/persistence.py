import json
import os
from datetime import datetime
from typing import Any

from gpc_agents.src.agents import RunResult
from .judge import JUDGE, Score
from gpc_agents.src.agents import Runner

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_RESULTS_DIR = os.path.join(_DATA_DIR, "run_results")

os.makedirs(_RESULTS_DIR, exist_ok=True)


def _to_serialisable(obj: Any) -> Any:  # noqa: ANN401 – needs Any for recursion
    """Best-effort conversion of complex SDK objects to JSON-serialisable primitives."""

    from dataclasses import is_dataclass, asdict

    if is_dataclass(obj):
        return asdict(obj)

    if isinstance(obj, (list, tuple)):
        return [_to_serialisable(i) for i in obj]

    if isinstance(obj, dict):
        return {k: _to_serialisable(v) for k, v in obj.items()}

    return obj


def persist_run_result(result: RunResult) -> str:
    """Write RunResult to JSONL file – returns absolute path."""

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S%fZ")
    trace_id = (
        result.context_wrapper.trace.trace_id if result.context_wrapper.trace else "notrace"
    )
    fname = f"{timestamp}_{trace_id}.json"
    fpath = os.path.join(_RESULTS_DIR, fname)

    payload = {
        "input": result.input,
        "final_output": _to_serialisable(result.final_output),
        "new_items": _to_serialisable(result.new_items),
        "trace_id": trace_id,
        "token_usage": _to_serialisable(result.raw_responses),
    }

    # Run quality judge synchronously (blocking) to score output
    try:
        judge_result = Runner.run_sync(JUDGE, {
            "assistant_answer": result.final_output,
            "question": result.input if isinstance(result.input, str) else "",
        })
        score: Score = judge_result.final_output  # type: ignore[assignment]
        payload["quality_score"] = score.rating
        payload["quality_rationale"] = score.rationale
    except Exception:
        payload["quality_score"] = None

    with open(fpath, "w") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=2)

    return fpath

__all__ = [
    "persist_run_result",
] 