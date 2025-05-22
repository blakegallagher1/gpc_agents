# East Baton Rouge Zoning Code Multi-Agent System

This repository hosts a **production-ready**, multi-agent assistant for the East Baton Rouge (EBR) Unified Development Code.  It is built on the OpenAI `gpc_agents` SDK and augmented with tracing, guardrails, cost governance, and observability tooling.

## Quick-start

```bash
# clone & install
./setup.sh  # installs deps and downloads the spaCy en_core_web_sm model

# required secrets
export OPENAI_API_KEY="sk-..."

# optional env vars
export REDIS_URL="redis://localhost:6379/0"          # caching
export OPENAI_DAILY_BUDGET=10                         # USD / 24 h
export OTEL_EXPORTER_OTLP_ENDPOINT="http://otel:4318" # tracing
export MCP_PERMIT_URL="https://permits.example.com"   # remote MCP service
```

## Interfaces

| Interface | Command | Notes |
|-----------|---------|-------|
| **CLI**   | `python -m agents.master_orchestrator_agent "What uses are permitted in C-2?"` | Streams answer to stdout. |
| **FastAPI** | `uvicorn agents.api:app --workers 2 --host 0.0.0.0 --port 8000` | `POST /ask` ➜ `{question}` returns `answer` plus `run_result_path`. |
| **Flask** (legacy) | `./ebr_zoning_web.py` | Will migrate to FastAPI UI. |
| **Metrics** | expose `/metrics` (Prometheus) | Redis cache hit/miss counters etc. |

## Runtime Flow

1. **ORCHESTRATOR** agent receives the user prompt and chooses a specialist via native *handoffs*.
2. **Guardrails** run *before* LLM invocation: profanity → PII → length limits.
3. Specialist executes tools (vector search, code interpreter, web search, hosted MCP…).
4. **LLM Judge** scores the final answer (`1-5`) and rationale; persisted alongside each run.
5. Token usage is logged; budget breaker aborts if the 24-hour spend exceeds the configured limit.

## Specialist Agents (11)

Chapters: 8-9 (Districts & Uses), 3 (Processes), 17 (Parking), 11 (Dimensional), 10.3 (Historic), 15 (Environmental), 16 (Signage), 7 (Non-conformities), 14 & 18 (Landscape), 19 (Definitions), 2•5•6 (Admin), 4 (Site Plans).

They are created via `agents/specialist_builder.py`; adding a new domain is a one-liner:

```python
from agents.specialist_builder import create_specialist
MY_AGENT = create_specialist(name="Floodplain Expert", domain="flood", instructions="…")
```

## Built-in Tools

* **FileSearchTool** – hybrid BM25 + embedding reranker scoped to each chapter.
* **CodeInterpreterTool** – sandboxed `python:3.11` container for numeric calcs (FAR, parking ratios…).
* **WebSearchTool** – state-level regulation look-ups (US-LA).
* **HostedMCPTool** – remote permit/GIS micro-service when `MCP_PERMIT_URL` is set.
* **get_parcel_zoning** – GIS REST lookup (1 h Redis/in-proc cache).
* **log_qa** – encrypted SQLite Q&A log (needs `FERNET_KEY`).

## Observability & Security

* OpenTelemetry traces → OTLP / stdout.
* Prometheus counters: `redis_cache_hit_total`, `redis_cache_miss_total`.
* GitHub Actions CI: black, ruff, mypy, pytest, truffleHog secret scan.
* Guardrails enforce structured JSON (`AnswerWithCitations`) and validate citations against the PDF.

## Dependencies (key)

```
openai, fastapi, uvicorn, httpx, redis, spacy, pypdf, cryptography,
opentelemetry-sdk, prometheus-client
```

---
For detailed capability matrix consult `agents/CAPABILITIES.md`.