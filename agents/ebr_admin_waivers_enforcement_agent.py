from agents import Agent, Runner, FileSearchTool, ModelSettings
import sqlite3
from datetime import datetime
import os
ZONING_CODE_PATH = "EastBatonRouge_Zoning.pdf"
VECTOR_STORE_ID = "vs_67f06532f1008191921744f7b0643ab6"
INSTRUCTIONS = (
    "You are an expert on the East Baton Rouge Zoning Code, specializing in administration, waivers, and enforcement. "
    "You understand the roles and powers of the Metropolitan Council, Planning Commission, Board of Adjustment (Chapter 2), the procedures for obtaining waivers (Chapter 5), and the processes for enforcement, violations, and penalties (Chapter 6). "
    "You also understand building permit requirements and changes in use/occupancy. "
    "Answer questions using the official zoning code as your primary source, focusing on Chapters 2, 5, and 6. "
    "If a question is outside this scope, politely decline to answer. "
    "Reference the relevant section or page of the zoning code PDF whenever possible."
)
agent = Agent(
    name="EBR Administration, Waivers & Enforcement Specialist",
    instructions=INSTRUCTIONS,
    model="gpt-4.1-mini-2025-04-14",
    model_settings=ModelSettings(),
    tools=[FileSearchTool(vector_store_ids=[VECTOR_STORE_ID], max_num_results=5, include_search_results=True)],
)
DB_PATH = "Administration Waivers Enforcement.db"
def log_qa_to_db(question, answer):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS qa_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    c.execute(
        "INSERT INTO qa_log (question, answer, timestamp) VALUES (?, ?, ?)",
        (question, answer, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY environment variable must be set to run this agent.")
if __name__ == "__main__":
    import sys
    question = " ".join(sys.argv[1:]) or "How do I apply for a waiver from the zoning code?"
    result = Runner.run_sync(agent, question)
    print(result.final_output)
    log_qa_to_db(question, result.final_output)
