from dataclasses import dataclass
from typing import List

__all__ = [
    "Citation",
    "AnswerWithCitations",
]


@dataclass
class Citation:
    """Reference to a zoning-code provision."""

    section: str  # e.g. "§8.5.2"
    page: str  # PDF page number or range


@dataclass
class AnswerWithCitations:
    """Canonical agent response payload.

    All agents must return this structure to simplify downstream processing
    and fine-tuning data collection.
    """

    answer: str  # Natural-language explanation
    citations: List[Citation] 