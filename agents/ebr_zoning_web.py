#!/usr/bin/env python3
import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from master_orchestrator_agent import route_question

app = Flask(__name__)

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
        "SELECT question, answer, timestamp FROM query_history ORDER BY id DESC LIMIT ?",
        (limit,)
    )
    history = cursor.fetchall()
    conn.close()
    return history

@app.route('/')
def index():
    history = get_history(5)
    return render_template('index.html', history=history)

@app.route('/api/ask', methods=['POST'])
def ask():
    data = request.json
    question = data.get('question', '')
    
    if not question.strip():
        return jsonify({'error': 'Question cannot be empty'})
    
    try:
        answer = route_question(question)
        save_to_history(question, answer)
        return jsonify({'answer': answer})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/history')
def history():
    limit = request.args.get('limit', 10, type=int)
    history = get_history(limit)
    return jsonify([{
        'question': q,
        'answer': a,
        'timestamp': ts
    } for q, a, ts in history])

if __name__ == '__main__':
    # Ensure the OpenAI API key is set
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY environment variable must be set.")
        exit(1)
    
    # Initialize the history database
    os.makedirs(os.path.dirname(HISTORY_DB_PATH), exist_ok=True)
    init_history_db()
    
    # Create templates directory if it doesn't exist
    os.makedirs(os.path.join(os.path.dirname(__file__), "templates"), exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)