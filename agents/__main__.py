from __future__ import annotations

import asyncio
import sys

from .master_orchestrator_agent import main as orchestrator_main

if __name__ == "__main__":
    # If called as `python -m agents ...` forward args to orchestrator
    asyncio.run(orchestrator_main()) 