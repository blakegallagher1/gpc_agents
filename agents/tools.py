import os
import sqlite3
import json
from datetime import datetime
from typing import Any

import httpx
from dotenv import load_dotenv
import redis
import time
from functools import lru_cache
from prometheus_client import Counter

from gpc_agents.src.agents import function_tool, CodeInterpreterTool, WebSearchTool

# Load .env if present – keeps credentials out of Git
load_dotenv()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_RUN_LOGS_DIR = os.path.join(_DATA_DIR, "run_logs")

os.makedirs(_RUN_LOGS_DIR, exist_ok=True)

REDIS_URL = os.getenv("REDIS_URL")
if REDIS_URL:
    _redis = redis.Redis.from_url(REDIS_URL)
else:
    _redis = None

_TTL_SECONDS = 3600

_local_cache: dict[str, tuple[float, str]] = {}

# Prometheus metrics
CACHE_HIT = Counter("redis_cache_hit_total", "Parcel zoning cache hits")
CACHE_MISS = Counter("redis_cache_miss_total", "Parcel zoning cache misses")


def _cache_get(key: str) -> str | None:
    if _redis:
        val = _redis.get(key)
        if val:
            CACHE_HIT.inc()
            return val.decode()
    if key in _local_cache:
        ts, v = _local_cache[key]
        if time.time() - ts < _TTL_SECONDS:
            CACHE_HIT.inc()
            return v
        _local_cache.pop(key, None)
    CACHE_MISS.inc()
    return None


def _cache_set(key: str, value: str):
    if _redis:
        _redis.setex(key, _TTL_SECONDS, value)
    else:
        _local_cache[key] = (time.time(), value)
    CACHE_MISS.inc()


# ---------------------------------------------------------------------------
# Function-callable tools (auto-schema via decorator)
# ---------------------------------------------------------------------------


@function_tool
def log_qa(domain: str, question: str, answer: str) -> None:  # noqa: D401
    """Persist a Q&A pair to SQLite for audit and future fine-tuning.

    Args:
        domain: Logical area (e.g. "parking", "signage"). Used to create table name.
        question: User prompt.
        answer: Agent's response.
    """

    db_path = os.path.join(_RUN_LOGS_DIR, f"{domain}.sqlite3")
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS qa_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "INSERT INTO qa_log (question, answer, timestamp) VALUES (?, ?, ?)",
        (question, answer, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


@function_tool
def get_parcel_zoning(parcel_id: str) -> str:  # noqa: D401
    """Look up zoning designation for a given East Baton Rouge parcel.

    This leverages the public EBR GIS REST service. Returns the zoning code string
    (e.g. "C2", "A1") or raises an error if not found.
    """

    cache_key = f"parcel:{parcel_id}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    # Example endpoint – replace with the authoritative API when available.
    api = os.getenv(
        "EBR_GIS_PARCEL_ENDPOINT",
        "https://gis.brla.gov/server/rest/services/Parish_Boundary/MapServer/0/query",
    )
    params = {
        "where": f"PARCEL_ID='{parcel_id}'",
        "outFields": "ZONING",
        "f": "json",
    }
    with httpx.Client(timeout=10) as client:
        resp = client.get(api, params=params)
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()

    try:
        zoning = data["features"][0]["attributes"]["ZONING"].strip()
    except (KeyError, IndexError):
        raise ValueError(f"Parcel {parcel_id} not found or zoning unavailable") from None

    _cache_set(cache_key, zoning)
    return zoning


__all__ = [
    "log_qa",
    "get_parcel_zoning",
] 