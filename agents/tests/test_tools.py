import os
import sqlite3

import pytest

from agents import tools as tools_mod
from agents.tools import log_qa


@pytest.mark.asyncio
async def test_log_qa_creates_db(tmp_path, monkeypatch):
    # Redirect data directory
    monkeypatch.setattr(tools_mod, "_RUN_LOGS_DIR", tmp_path)

    await log_qa("parking", "test q", "test a")

    db_path = os.path.join(tmp_path, "parking.sqlite3")
    assert os.path.exists(db_path)

    conn = sqlite3.connect(db_path)
    cur = conn.execute("SELECT question, answer FROM qa_log")
    row = cur.fetchone()
    conn.close()

    assert row == ("test q", "test a")