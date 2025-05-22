import sys
from pathlib import Path

# Ensure the internal gpc_agents source dir is importable if project not installed
_root = Path(__file__).resolve().parent.parent
_gpc_src = _root / "gpc_agents" / "src"
if str(_gpc_src) not in sys.path:
    sys.path.insert(0, str(_gpc_src))

# Re-export frequently-used helpers so downstream code can `from agents import X`
from .config import DEFAULT_MODEL  # noqa: E402  (import after path tweak)
from .specialists import ALL_SPECIALISTS  # noqa: E402
from .master_orchestrator_agent import ORCHESTRATOR  # noqa: E402

__all__ = [
    "DEFAULT_MODEL",
    "ALL_SPECIALISTS",
    "ORCHESTRATOR",
] 