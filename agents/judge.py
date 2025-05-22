from dataclasses import dataclass

from gpc_agents.src.agents import Agent, ModelSettings
from .config import DEFAULT_MODEL

@dataclass
class Score:
    rating: int  # 1-5
    rationale: str

JUDGE = Agent(
    name="LLM Judge",
    instructions=(
        "You are an impartial quality judge. Rate the given assistant answer on accuracy, citation quality, and completeness on a scale of 1 (poor) to 5 (excellent). "
        "Return JSON with `rating` (int 1-5) and `rationale` (short string)."
    ),
    model=DEFAULT_MODEL,
    output_type=Score,
    model_settings=ModelSettings(temperature=0.0),
)

__all__ = ["JUDGE", "Score"] 