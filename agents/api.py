from __future__ import annotations

import asyncio
import os
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .master_orchestrator_agent import ORCHESTRATOR
from .usage_monitor import BudgetExceededError, run_with_budget
from .persistence import persist_run_result

app = FastAPI(title="EBR Zoning Code Assistant")


class AskRequest(BaseModel):
    question: str = Field(..., description="User question about zoning code")


class AskResponse(BaseModel):
    answer: Any
    run_result_path: str | None = None


@app.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest):
    try:
        result = await run_with_budget(starting_agent=ORCHESTRATOR, input=req.question)
    except BudgetExceededError as e:
        raise HTTPException(status_code=429, detail=str(e))

    path = persist_run_result(result)
    return AskResponse(answer=result.final_output, run_result_path=path)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    import uvicorn

    uvicorn.run("agents.api:app", host="0.0.0.0", port=port, workers=2) 