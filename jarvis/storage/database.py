"""
JARVIS Storage Engine - SQLite Database Management
Stores sessions, messages, and action logs securely in AppData/Local/JARVIS/
"""

import os
import sqlite3
from pathlib import Path
from typing import Optional


def get_data_dir() -> Path:
    """Returns the user data directory: %LOCALAPPDATA%/JARVIS or fallback to ~/.jarvis"""
    local_app_data = os.getenv("LOCALAPPDATA")
    if local_app_data:
        data_dir = Path(local_app_data) / "JARVIS"
    else:
        data_dir = Path.home() / ".jarvis"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_db_path() -> Path:
    return get_data_dir() / "jarvis.db"


class Database:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or get_db_path()
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_db(self):
        """Initializes tables and indexes for high-speed searching."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL, -- 'user', 'assistant', 'system'
                    content TEXT NOT NULL,
                    reply_to_id TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                )
            """)

            # Actions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS actions (
                    id TEXT PRIMARY KEY,
                    message_id TEXT,
                    tool TEXT NOT NULL,
                    action TEXT NOT NULL,
                    params TEXT,
                    status TEXT NOT NULL, -- 'SUCCESS', 'FAILED', 'REQUIRES_CONFIRMATION', 'CANCELLED'
                    result_summary TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE SET NULL
                )
            """)

            # Settings key-value table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Indexes for fast historical search
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_actions_timestamp ON actions(timestamp DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_actions_tool ON actions(tool)")

            conn.commit()
