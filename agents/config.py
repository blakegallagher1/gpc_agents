import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure gpc_agents/src is importable BEFORE we touch the SDK
# ---------------------------------------------------------------------------
_repo_root = Path(__file__).resolve().parent.parent
_gpc_src = _repo_root / "gpc_agents" / "src"
if str(_gpc_src) not in sys.path:
    sys.path.insert(0, str(_gpc_src))

from gpc_agents.src.agents import (
    enable_verbose_stdout_logging,
    set_default_openai_api,
    set_default_openai_client,
    set_default_openai_key,
    set_tracing_export_api_key,
)

# ---------------------------------------------------------------------------
# Public constants
# ---------------------------------------------------------------------------

# Allow env override, otherwise default to GPT-4o-mini (fast, low-cost)
DEFAULT_MODEL: str = os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4o-mini")

# Switch between "responses" (streaming, tool use) and "chat_completions" APIs
DEFAULT_OPENAI_API: str = os.getenv("OPENAI_API_TYPE", "responses")

# ---------------------------------------------------------------------------
# One-time SDK initialisation – executed on import
# ---------------------------------------------------------------------------

# API key handling – honour env var first, then fallback to ~/.openai_key file
_api_key: str | None = os.getenv("OPENAI_API_KEY")
if not _api_key:
    key_path = os.path.expanduser("~/.openai_key")
    if os.path.exists(key_path):
        with open(key_path) as fp:
            _api_key = fp.read().strip()

if _api_key:
    # Set for both LLM requests and tracing export.
    set_default_openai_key(_api_key, use_for_tracing=True)
    # Ensure downstream libs can still rely on env var.
    os.environ.setdefault("OPENAI_API_KEY", _api_key)

# Select preferred endpoint (responses API gives function-calling out of the box).
set_default_openai_api(DEFAULT_OPENAI_API)  # type: ignore[arg-type]

# Optional verbose logs when DEBUG=1
if os.getenv("DEBUG") == "1":
    enable_verbose_stdout_logging()

__all__ = [
    "DEFAULT_MODEL",
    "DEFAULT_OPENAI_API",
] 