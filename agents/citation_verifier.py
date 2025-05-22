from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, List

from pypdf import PdfReader

from gpc_agents.src.agents import GuardrailFunctionOutput, output_guardrail

from .structures import AnswerWithCitations

_PDF_PATH = os.path.join(os.path.dirname(__file__), "data", "EastBatonRouge_Zoning.pdf")


@lru_cache(maxsize=1)
def _load_pdf_text() -> List[str]:
    reader = PdfReader(_PDF_PATH)
    pages_text = []
    for page in reader.pages:
        pages_text.append(page.extract_text() or "")
    return pages_text


@output_guardrail
async def verify_citations(_, __, output: Any) -> GuardrailFunctionOutput:  # type: ignore[override]
    """Validate that each cited page actually contains the cited section string."""

    if not isinstance(output, AnswerWithCitations):
        # Only verify when structured
        return GuardrailFunctionOutput(output_info="non-structured", tripwire_triggered=False)

    pages = _load_pdf_text()
    failures: list[str] = []

    for cit in output.citations:
        try:
            page_num = int(cit.page.split("-")[0]) - 1  # pages are 1-indexed in PDF
            if page_num < 0 or page_num >= len(pages):
                failures.append(cit.section)
                continue
            if cit.section not in pages[page_num]:
                failures.append(cit.section)
        except Exception:
            failures.append(cit.section)

    return GuardrailFunctionOutput(output_info={"invalid_citations": failures}, tripwire_triggered=bool(failures))

__all__ = ["verify_citations"] 