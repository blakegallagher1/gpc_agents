from agents import Agent, Runner, FileSearchTool, ModelSettings
from agents.models.openai_provider import OpenAIProvider
import sqlite3
from datetime import datetime
import os

# Path to the zoning code PDF
ZONING_CODE_PATH = os.path.join(os.path.dirname(__file__), "data", "EastBatonRouge_Zoning.pdf")

# Vector store ID for the ingested PDF (replace with your actual ID after upload)
VECTOR_STORE_ID = "vs_67f06532f1008191921744f7b0643ab6"

# Agent instructions, focused on Parking & Loading Requirements
INSTRUCTIONS = (
    "You are an expert on the East Baton Rouge Zoning Code, specializing in Parking & Loading Requirements. "
    "Answer questions using the official zoning code as your primary source. "
    "If a question is outside the scope of Parking & Loading Requirements, politely decline to answer. "
    "Reference the relevant section or page of the zoning code PDF (EastBatonRouge_Zoning.pdf) whenever possible."
)

# Create the agent with the specified model, Responses API, and FileSearchTool
agent = Agent(
    name="EBR Zoning Parking & Loading Expert",
    instructions=INSTRUCTIONS,
    model="gpt-4.1-mini-2025-04-14",
    model_settings=ModelSettings(),
    tools=[
        FileSearchTool(
            vector_store_ids=[VECTOR_STORE_ID],
            max_num_results=5,
            include_search_results=True,
        )
    ],
)

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "Parking and Loading.db")

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

# --- Wrap the agent's __call__ method to always log Q&A ---
class LoggingAgentWrapper:
    def __init__(self, agent, log_func):
        self._agent = agent
        self._log_func = log_func
        # Copy attributes for compatibility
        for attr in dir(agent):
            if not attr.startswith("_") and not hasattr(self, attr):
                setattr(self, attr, getattr(agent, attr))

    def __call__(self, question, *args, **kwargs):
        result = self._agent(question, *args, **kwargs)
        # result may be a string or an object with .final_output
        answer = getattr(result, "final_output", result)
        self._log_func(question, answer)
        return result

    # For compatibility with Runner.run_sync etc.
    def run(self, *args, **kwargs):
        result = self._agent.run(*args, **kwargs)
        # Try to extract question from args if possible
        question = args[0] if args else kwargs.get("question", "")
        answer = getattr(result, "final_output", result)
        self._log_func(question, answer)
        return result

# Replace the agent with the logging wrapper
agent = LoggingAgentWrapper(agent, log_qa_to_db)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY environment variable must be set to run this agent.")

if __name__ == "__main__":
    import sys
    question = " ".join(sys.argv[1:]) or "What are the minimum parking requirements for retail stores?"
    result = Runner.run_sync(agent, question)
    print(getattr(result, "final_output", result))
