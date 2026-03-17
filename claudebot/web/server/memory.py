"""Persistent memory for Mimi using SQLite.

Stores conversation history, user preferences, and session data
so nothing is lost across Railway redeploys.
"""

import os
import json
import sqlite3
import time
from pathlib import Path
from contextlib import contextmanager

# ---------------------------------------------------------------------------
# Database path — persistent across Railway redeploys if using a volume,
# otherwise falls back to local file (still better than pure in-memory).
# ---------------------------------------------------------------------------

_DB_DIR = os.getenv("MIMI_DATA_DIR", os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(_DB_DIR, "mimi_memory.db")


@contextmanager
def _get_db():
    """Thread-safe database connection context manager."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create tables if they don't exist."""
    with _get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel TEXT NOT NULL,         -- 'telegram', 'web', 'sms'
                user_id TEXT NOT NULL,         -- telegram uid, phone number, 'web'
                role TEXT NOT NULL,            -- 'user' or 'assistant'
                content TEXT NOT NULL,         -- JSON-encoded message content
                timestamp REAL NOT NULL,       -- Unix timestamp
                session_id TEXT DEFAULT NULL   -- Optional session grouping
            );

            CREATE INDEX IF NOT EXISTS idx_conv_user
                ON conversations(channel, user_id, timestamp);

            CREATE TABLE IF NOT EXISTS summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel TEXT NOT NULL,
                user_id TEXT NOT NULL,
                summary TEXT NOT NULL,         -- Compressed summary of older messages
                messages_covered INTEGER,      -- How many messages this summary covers
                timestamp REAL NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_summaries_user
                ON summaries(channel, user_id, timestamp);

            CREATE TABLE IF NOT EXISTS user_preferences (
                channel TEXT NOT NULL,
                user_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                updated_at REAL NOT NULL,
                PRIMARY KEY (channel, user_id, key)
            );
        """)


# ---------------------------------------------------------------------------
# Conversation history
# ---------------------------------------------------------------------------

def save_message(channel: str, user_id: str, role: str, content, session_id: str = None):
    """Save a message to persistent storage. Content can be str or list (for image blocks)."""
    content_json = json.dumps(content, default=str, ensure_ascii=False) if not isinstance(content, str) else content
    with _get_db() as conn:
        conn.execute(
            "INSERT INTO conversations (channel, user_id, role, content, timestamp, session_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (channel, str(user_id), role, content_json, time.time(), session_id),
        )


def get_history(channel: str, user_id: str, limit: int = 50) -> list[dict]:
    """Retrieve recent conversation history for a user.
    Returns messages in chronological order (oldest first).
    """
    with _get_db() as conn:
        rows = conn.execute(
            "SELECT role, content, timestamp FROM conversations "
            "WHERE channel = ? AND user_id = ? "
            "ORDER BY timestamp DESC LIMIT ?",
            (channel, str(user_id), limit),
        ).fetchall()

    messages = []
    for row in reversed(rows):  # Reverse to get chronological order
        try:
            content = json.loads(row["content"])
        except (json.JSONDecodeError, TypeError):
            content = row["content"]
        messages.append({"role": row["role"], "content": content})
    return messages


def clear_history(channel: str, user_id: str):
    """Clear all conversation history for a user."""
    with _get_db() as conn:
        conn.execute(
            "DELETE FROM conversations WHERE channel = ? AND user_id = ?",
            (channel, str(user_id)),
        )


def get_message_count(channel: str, user_id: str) -> int:
    """Get total message count for a user."""
    with _get_db() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM conversations WHERE channel = ? AND user_id = ?",
            (channel, str(user_id)),
        ).fetchone()
        return row["cnt"] if row else 0


# ---------------------------------------------------------------------------
# Conversation summaries (for smart truncation)
# ---------------------------------------------------------------------------

def save_summary(channel: str, user_id: str, summary: str, messages_covered: int):
    """Save a conversation summary."""
    with _get_db() as conn:
        conn.execute(
            "INSERT INTO summaries (channel, user_id, summary, messages_covered, timestamp) "
            "VALUES (?, ?, ?, ?, ?)",
            (channel, str(user_id), summary, messages_covered, time.time()),
        )


def get_latest_summary(channel: str, user_id: str) -> dict | None:
    """Get the most recent summary for a user."""
    with _get_db() as conn:
        row = conn.execute(
            "SELECT summary, messages_covered, timestamp FROM summaries "
            "WHERE channel = ? AND user_id = ? ORDER BY timestamp DESC LIMIT 1",
            (channel, str(user_id)),
        ).fetchone()
        if row:
            return {
                "summary": row["summary"],
                "messages_covered": row["messages_covered"],
                "timestamp": row["timestamp"],
            }
    return None


# ---------------------------------------------------------------------------
# User preferences
# ---------------------------------------------------------------------------

def set_preference(channel: str, user_id: str, key: str, value: str):
    """Set a user preference."""
    with _get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO user_preferences (channel, user_id, key, value, updated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (channel, str(user_id), key, value, time.time()),
        )


def get_preference(channel: str, user_id: str, key: str, default: str = None) -> str | None:
    """Get a user preference."""
    with _get_db() as conn:
        row = conn.execute(
            "SELECT value FROM user_preferences WHERE channel = ? AND user_id = ? AND key = ?",
            (channel, str(user_id), key),
        ).fetchone()
        return row["value"] if row else default


# ---------------------------------------------------------------------------
# Initialize on import
# ---------------------------------------------------------------------------

init_db()
