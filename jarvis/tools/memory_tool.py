"""
JARVIS Memory Tool
Persistent key-value memory store — "remember that X", "recall Y", "what did I ask yesterday?"
"""

import json
from datetime import datetime, timedelta
from .base import BaseTool, ToolResult
from jarvis.storage.database import Database


class MemoryTool(BaseTool):
    name = "MemoryTool"
    description = "Stores and retrieves persistent memories and past interactions."

    def __init__(self):
        self.db = Database()
        self._ensure_memory_table()

    def _ensure_memory_table(self):
        """Creates memory table if it doesn't exist."""
        with self.db.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_key ON memory(key)")
            conn.commit()

    def execute(self, action: str, **kwargs) -> ToolResult:
        action = action.lower().strip()

        if action == "remember":
            return self.remember(kwargs.get("key", ""), kwargs.get("value", ""))
        elif action == "recall":
            return self.recall(kwargs.get("query", ""))
        elif action == "recall_history":
            return self.recall_history(kwargs.get("query", ""), kwargs.get("timeframe", "yesterday"))
        elif action == "forget":
            return self.forget(kwargs.get("key", ""))
        elif action == "list_memories":
            return self.list_memories()

        return ToolResult(status="FAILED", message=f"Unknown memory action: {action}")

    def remember(self, key: str, value: str) -> ToolResult:
        """Stores a persistent memory."""
        if not key or not value:
            return ToolResult(status="FAILED", message="I need something to remember. Please tell me what to store.")

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.db.get_connection() as conn:
            # Update if key exists, otherwise insert
            existing = conn.execute("SELECT id FROM memory WHERE key = ?", (key.lower(),)).fetchone()
            if existing:
                conn.execute(
                    "UPDATE memory SET value = ?, last_accessed = ? WHERE key = ?",
                    (value, now, key.lower()),
                )
            else:
                conn.execute(
                    "INSERT INTO memory (key, value, created_at, last_accessed) VALUES (?, ?, ?, ?)",
                    (key.lower(), value, now, now),
                )
            conn.commit()

        return ToolResult(
            status="SUCCESS",
            message=f"Got it. I'll remember that {key} is {value}.",
            data={"key": key, "value": value},
        )

    def recall(self, query: str) -> ToolResult:
        """Retrieves a memory by fuzzy key match."""
        if not query:
            return self.list_memories()

        with self.db.get_connection() as conn:
            # Exact match first
            row = conn.execute(
                "SELECT key, value FROM memory WHERE key = ?", (query.lower(),)
            ).fetchone()

            if not row:
                # Fuzzy match
                row = conn.execute(
                    "SELECT key, value FROM memory WHERE key LIKE ? OR value LIKE ? ORDER BY last_accessed DESC LIMIT 1",
                    (f"%{query.lower()}%", f"%{query.lower()}%"),
                ).fetchone()

            if row:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                conn.execute("UPDATE memory SET last_accessed = ? WHERE key = ?", (now, row["key"]))
                conn.commit()
                return ToolResult(
                    status="SUCCESS",
                    message=f"{row['key'].capitalize()}: {row['value']}",
                    data={"key": row["key"], "value": row["value"]},
                )

        return ToolResult(status="FAILED", message=f"I don't have any memory about '{query}'.")

    def recall_history(self, query: str, timeframe: str = "yesterday") -> ToolResult:
        """Searches past command history for time-based queries like 'what did I ask yesterday?'"""
        now = datetime.now()
        if "yesterday" in timeframe:
            start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0)
            end = now.replace(hour=0, minute=0, second=0)
            label = "yesterday"
        elif "today" in timeframe:
            start = now.replace(hour=0, minute=0, second=0)
            end = now
            label = "today"
        elif "week" in timeframe:
            start = now - timedelta(days=7)
            end = now
            label = "this week"
        else:
            start = now - timedelta(days=1)
            end = now
            label = "recently"

        start_str = start.strftime("%Y-%m-%d %H:%M:%S")
        end_str = end.strftime("%Y-%m-%d %H:%M:%S")

        with self.db.get_connection() as conn:
            sql = """
                SELECT content, timestamp FROM messages
                WHERE role = 'user' AND timestamp BETWEEN ? AND ?
                ORDER BY timestamp DESC LIMIT 10
            """
            params = [start_str, end_str]
            if query:
                sql = """
                    SELECT content, timestamp FROM messages
                    WHERE role = 'user' AND timestamp BETWEEN ? AND ? AND content LIKE ?
                    ORDER BY timestamp DESC LIMIT 10
                """
                params.append(f"%{query}%")

            rows = conn.execute(sql, params).fetchall()

        if not rows:
            return ToolResult(status="SUCCESS", message=f"I don't have any records from {label}.")

        items = [f"• {row['content']}" for row in rows[:5]]
        summary = f"Here's what you asked {label}:\n" + "\n".join(items)
        return ToolResult(status="SUCCESS", message=summary, data={"count": len(rows)})

    def forget(self, key: str) -> ToolResult:
        """Removes a specific memory."""
        if not key:
            return ToolResult(status="FAILED", message="What should I forget?")

        with self.db.get_connection() as conn:
            cursor = conn.execute("DELETE FROM memory WHERE key LIKE ?", (f"%{key.lower()}%",))
            conn.commit()
            if cursor.rowcount > 0:
                return ToolResult(status="SUCCESS", message=f"I've forgotten about {key}.")
            return ToolResult(status="FAILED", message=f"I don't have any memory about '{key}'.")

    def list_memories(self) -> ToolResult:
        """Lists all stored memories."""
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT key, value FROM memory ORDER BY last_accessed DESC LIMIT 10"
            ).fetchall()

        if not rows:
            return ToolResult(status="SUCCESS", message="I don't have any memories stored yet.")

        items = [f"• {row['key']}: {row['value']}" for row in rows]
        return ToolResult(
            status="SUCCESS",
            message="Here's what I remember:\n" + "\n".join(items),
            data={"count": len(rows)},
        )
