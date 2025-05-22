# CAPABILITIES

## Overview

- Multi-agent Q&A system for the East Baton Rouge Zoning Code driven by `gpc_agents` SDK.
- Central orchestrator delegates to 11 domain-specialist agents (see below) via handoffs.
- Hardened guardrails (profanity, PII/parcel confidentiality, length, citation validation) ensure compliant and structured outputs.
- Cost governor logs token usage and enforces a daily spend ceiling.
- Built-in tracing ➜ OpenTelemetry for end-to-end observability.

## Interfaces

| Channel | Details |
|---------|---------|
| **CLI** | `python -m agents.master_orchestrator_agent "your question"` (interactive variant coming soon). |
| **FastAPI** | `uvicorn agents.api:app --workers 2` → `POST /ask` JSON `{question}` returns structured answer + path to persisted run-result. |
| **Flask Web UI** | Legacy interface still available via `ebr_zoning_web.py` (will migrate to FastAPI). |

## Orchestrator

- `ORCHESTRATOR` Agent uses native handoffs; no regex routing logic to maintain.
- Guardrails run on every user prompt **before** tool/LLM execution.

### Active Guardrails

1. `profanity_filter` – blocks slurs / abusive language.
2. `pii_filter` – regex + spaCy NER to redact SSN, phones, emails, names, addresses.
3. `length_guardrail` – rejects prompts > `$PROMPT_TOKEN_LIMIT` (env, default 800 tokens).
4. `enforce_citation_json` – forces `AnswerWithCitations` schema.
5. `verify_citations` – confirms cited § string appears on referenced PDF page.

Tripwires raise exceptions surfaced as HTTP 429 with JSON error payload in API.

## Specialist Agents

- **Zoning Districts & Use Regulations** (Chapters 8 & 9)
- **Processes** (Chapter 3)
- **Parking & Loading Requirements** (Chapter 17)
- **Dimensional Standards** (Chapter 11)
- **Historic Overlay** (Chapter 10.3)
- **Environmental** (Chapter 15)
- **Signage** (Chapter 16)
- **Nonconformities** (Chapter 7)
- **Landscape, Trees & Utilities** (Chapters 14 & 18)
- **Definitions** (Chapter 19)
- **Administration, Waivers & Enforcement** (Chapters 2, 5 & 6)
- **Site Plans & Plats** (Chapter 4)

## Tools

- **FileSearchTool** – hybrid BM25 + embeddings reranker with chapter-level filters.
- **CodeInterpreterTool** – sandboxed Python 3.11 for FAR, parking-ratio and numeric checks.
- **WebSearchTool** – high-context web search scoped to US/LA for state regulations.
- **HostedMCPTool** – auto-added when `MCP_PERMIT_URL` env is set, exposing remote permit or GIS micro-service.
- **get_parcel_zoning** – GIS REST lookup; 1-hour cache via Redis (`REDIS_URL`) or in-proc fallback.
- **log_qa** – persists Q&A in per-domain SQLite, encrypted on-disk when `FERNET_KEY` env present.

## Cost & Usage Governance

`agents/usage_monitor.py` records token counts in `data/usage.sqlite3` and prevents runs that would exceed `OPENAI_DAILY_BUDGET` (default $10/day).

## Self-Evaluation

Each run is auto-scored by an 0-temperature **LLM Judge** (`agents/judge.py`).  The score (`1-5`) and rationale are appended to every persisted run-result JSON for continuous quality monitoring and future fine-tuning.

## Observability

- Traces exported via OpenTelemetry SDK (`OTEL_EXPORTER_OTLP_ENDPOINT` env) or stdout.
- GitHub Actions CI: lint, type-check, tests across 3 Python versions; secret scanning via truffleHog.
- Optional Grafana dashboard (prometheus scrape coming next iteration) shows latency, tokens, guardrail trips.
- Prometheus metrics: `redis_cache_hit_total`, `redis_cache_miss_total` counters; scrape `/metrics` when `prometheus_client` is installed.
- Grafana dashboard (tokens, latency, guardrail trips, cache hit-rate).

## Security

- SQLite Q&A logs encrypted with Fernet symmetric key (`FERNET_KEY`).
- Pre-commit hooks: black, ruff, mypy, truffleHog secret scan.

## Dependencies (key)

```
openai, fastapi, uvicorn, httpx, redis, spacy, pypdf, cryptography,
opentelemetry-sdk, prometheus-client
```

Run `./setup.sh` or `pip install -r agents/requirements.txt` to bootstrap.

## Setup & Installation

- Run `./setup.sh` to:
  1. Create `data/` directory.
  2. Check for and warn about missing `OPENAI_API_KEY`.
  3. Install dependencies from `requirements.txt`.
  4. Make CLI (`ebr_zoning_cli.py`) and web (`ebr_zoning_web.py`) scripts executable.

## Execution

- **CLI:**
  - Interactive: `./ebr_zoning_cli.py -i`
  - Single question: `./ebr_zoning_cli.py "Your question here"`

- **Web:**
  - Start server: `./ebr_zoning_web.py`
  - Access UI: http://localhost:5000 