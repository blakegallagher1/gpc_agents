#!/usr/bin/env python3
import os
import sys
import argparse
import sqlite3
from datetime import datetime
from master_orchestrator_agent import route_question

# Path to the history database
HISTORY_DB_PATH = os.path.join(os.path.dirname(__file__), "data", "query_history.db")

def init_history_db():
    """Initialize the history database if it doesn't exist."""
    conn = sqlite3.connect(HISTORY_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS query_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_to_history(question, answer):
    """Save the question and answer to the history database."""
    conn = sqlite3.connect(HISTORY_DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO query_history (question, answer, timestamp) VALUES (?, ?, ?)",
        (question, answer, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

def get_history(limit=10):
    """Get the most recent queries from history."""
    conn = sqlite3.connect(HISTORY_DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT question, timestamp FROM query_history ORDER BY id DESC LIMIT ?",
        (limit,)
    )
    history = cursor.fetchall()
    conn.close()
    return history

def interactive_mode():
    """Run the CLI in interactive mode."""
    print("East Baton Rouge Zoning Code Assistant")
    print("======================================")
    print("Type 'exit', 'quit', or Ctrl+C to exit.")
    print("Type 'history' to view recent queries.")
    print()
    
    while True:
        try:
            question = input("Ask a question: ")
            
            # Handle special commands
            if question.lower() in ["exit", "quit"]:
                break
            elif question.lower() == "history":
                history = get_history()
                if not history:
                    print("No history found.")
                else:
                    print("\nRecent queries:")
                    for i, (q, ts) in enumerate(history, 1):
                        print(f"{i}. [{ts[:19]}] {q}")
                print()
                continue
            
            # Skip empty questions
            if not question.strip():
                continue
            
            # Route the question to the appropriate agent
            print("\nProcessing your question...")
            answer = route_question(question)
            
            # Save to history
            save_to_history(question, answer)
            
            # Print the response
            print("\nResponse:")
            print("----------")
            print(answer)
            print("\n")
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")

def main():
    # Ensure the OpenAI API key is set
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY environment variable must be set.")
        sys.exit(1)
    
    # Initialize the history database
    os.makedirs(os.path.dirname(HISTORY_DB_PATH), exist_ok=True)
    init_history_db()
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description="East Baton Rouge Zoning Code Assistant CLI")
    parser.add_argument("question", nargs="*", help="The question to ask (if not in interactive mode)")
    parser.add_argument("-i", "--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("--history", action="store_true", help="Show recent query history")
    
    args = parser.parse_args()
    
    # Handle history request
    if args.history:
        history = get_history(20)
        if not history:
            print("No history found.")
        else:
            print("Recent queries:")
            for i, (q, ts) in enumerate(history, 1):
                print(f"{i}. [{ts[:19]}] {q}")
        return
    
    # Run in interactive mode if requested or if no question provided
    if args.interactive or not args.question:
        interactive_mode()
        return
    
    # Process a single question from command line arguments
    question = " ".join(args.question)
    answer = route_question(question)
    save_to_history(question, answer)
    print(answer)

if __name__ == "__main__":
    main()