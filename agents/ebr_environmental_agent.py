from agents import Agent, Runner, FileSearchTool, ModelSettings
import sqlite3
from datetime import datetime
import os
ZONING_CODE_PATH = os.path.join(os.path.dirname(__file__), "data", "EastBatonRouge_Zoning.pdf")
VECTOR_STORE_ID = "vs_67f06532f1008191921744f7b0643ab6"
INSTRUCTIONS = (
    "You are an expert on the East Baton Rouge Zoning Code, specializing in environmental regulations: floodways, floodplains, drainage, water quality, stormwater management, hazard area permits, site clearing, and open space requirements. "
    "Answer questions using the official zoning code as your primary source, focusing on Chapters 15, 12, and relevant site clearing sections of 3. "
    "If a question is outside this scope, politely decline to answer. "
    "Reference the relevant section or page of the zoning code PDF whenever possible."
)
agent = Agent(
    name="EBR Environmental Regulations Specialist",
    instructions=INSTRUCTIONS,
    model="gpt-4.1-mini-2025-04-14",
    model_settings=ModelSettings(),
    tools=[FileSearchTool(vector_store_ids=[VECTOR_STORE_ID], max_num_results=5, include_search_results=True)],
)
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "Environmental and Site Clearing.db")

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

class LoggingAgentWrapper:
    def __init__(self, agent, log_func):
        self._agent = agent
        self._log_func = log_func
        for attr in dir(agent):
            if not attr.startswith("_") and not hasattr(self, attr):
                setattr(self, attr, getattr(agent, attr))

    def __call__(self, question, *args, **kwargs):
        result = self._agent(question, *args, **kwargs)
        answer = getattr(result, "final_output", result)
        self._log_func(question, answer)
        return result

    def run(self, *args, **kwargs):
        result = self._agent.run(*args, **kwargs)
        question = args[0] if args else kwargs.get("question", "")
        answer = getattr(result, "final_output", result)
        self._log_func(question, answer)
        return result

agent = LoggingAgentWrapper(agent, log_qa_to_db)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY environment variable must be set to run this agent.")
if __name__ == "__main__":
    import sys
    question = " ".join(sys.argv[1:]) or "What are the requirements for development in a floodplain?"
    result = Runner.run_sync(agent, question)
    print(result.final_output)
    log_qa_to_db(question, result.final_output)
