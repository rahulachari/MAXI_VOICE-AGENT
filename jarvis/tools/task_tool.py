"""
JARVIS Task Tool
Local task/todo management with SQLite persistence and Windows toast notifications.
Supports: "Add to my todo: review the Q3 doc", "What are my tasks?"
"""

from datetime import datetime, timedelta
from typing import Optional
from .base import BaseTool, ToolResult
from jarvis.storage.database import Database


class TaskTool(BaseTool):
    name = "TaskTool"
    description = "Manages local tasks, todos, and reminders."

    def __init__(self):
        self.db = Database()
        self._ensure_tasks_table()

    def _ensure_tasks_table(self):
        """Creates tasks table if it doesn't exist."""
        with self.db.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    due_at TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    reminder_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_due ON tasks(due_at)")
            conn.commit()

    def execute(self, action: str, **kwargs) -> ToolResult:
        action = action.lower().strip()

        if action == "add_task":
            return self.add_task(
                title=kwargs.get("title", ""),
                description=kwargs.get("description", ""),
                due_str=kwargs.get("due", ""),
            )
        elif action == "list_tasks":
            return self.list_tasks(status_filter=kwargs.get("status", "pending"))
        elif action == "complete_task":
            return self.complete_task(kwargs.get("query", ""))
        elif action == "delete_task":
            return self.delete_task(kwargs.get("query", ""))

        return ToolResult(status="FAILED", message=f"Unknown task action: {action}")

    def add_task(self, title: str, description: str = "", due_str: str = "") -> ToolResult:
        """Adds a new task."""
        if not title:
            return ToolResult(status="FAILED", message="What task should I add?")

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        due_at = None
        if due_str:
            due_at = self._parse_due_date(due_str)

        with self.db.get_connection() as conn:
            conn.execute(
                "INSERT INTO tasks (title, description, due_at, status, created_at) VALUES (?, ?, ?, 'pending', ?)",
                (title, description, due_at, now),
            )
            conn.commit()

        msg = f"Added to your tasks: {title}"
        if due_at:
            msg += f" (due {due_at})"
        return ToolResult(status="SUCCESS", message=msg + ".", data={"title": title})

    def list_tasks(self, status_filter: str = "pending") -> ToolResult:
        """Lists tasks with optional status filter."""
        with self.db.get_connection() as conn:
            if status_filter == "all":
                rows = conn.execute(
                    "SELECT title, status, due_at, created_at FROM tasks ORDER BY created_at DESC LIMIT 15"
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT title, status, due_at, created_at FROM tasks WHERE status = ? ORDER BY created_at DESC LIMIT 15",
                    (status_filter,),
                ).fetchall()

        if not rows:
            return ToolResult(status="SUCCESS", message="You don't have any pending tasks. Nice work!")

        task_titles = [row["title"] for row in rows]
        count = len(task_titles)
        label = "task" if count == 1 else "tasks"

        if count == 1:
            spoken_summary = f"You have 1 pending task: {task_titles[0]}."
        elif count <= 3:
            spoken_summary = f"You have {count} pending tasks: " + ", ".join(task_titles) + "."
        else:
            spoken_summary = f"You have {count} pending tasks, including {task_titles[0]}, and {task_titles[1]}."

        details = "\n".join([f"- {t}" for t in task_titles])
        return ToolResult(
            status="SUCCESS",
            message=spoken_summary,
            data={"count": count, "tasks": task_titles, "full_details": details},
        )

    def complete_task(self, query: str) -> ToolResult:
        """Marks a task as completed by fuzzy title match."""
        if not query:
            return ToolResult(status="FAILED", message="Which task should I mark as done?")

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT id, title FROM tasks WHERE status = 'pending' AND title LIKE ? LIMIT 1",
                (f"%{query}%",),
            ).fetchone()

            if row:
                conn.execute(
                    "UPDATE tasks SET status = 'completed', completed_at = ? WHERE id = ?",
                    (now, row["id"]),
                )
                conn.commit()
                return ToolResult(status="SUCCESS", message=f"Done! Marked '{row['title']}' as completed.")

        return ToolResult(status="FAILED", message=f"I couldn't find a pending task matching '{query}'.")

    def delete_task(self, query: str) -> ToolResult:
        """Deletes a task by fuzzy title match."""
        if not query:
            return ToolResult(status="FAILED", message="Which task should I delete?")

        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT id, title FROM tasks WHERE title LIKE ? LIMIT 1",
                (f"%{query}%",),
            ).fetchone()

            if row:
                conn.execute("DELETE FROM tasks WHERE id = ?", (row["id"],))
                conn.commit()
                return ToolResult(status="SUCCESS", message=f"Deleted task: '{row['title']}'.")

        return ToolResult(status="FAILED", message=f"I couldn't find a task matching '{query}'.")

    def _parse_due_date(self, due_str: str) -> Optional[str]:
        """Parses simple due date strings."""
        text = due_str.lower().strip()
        now = datetime.now()

        if text == "today":
            return now.strftime("%Y-%m-%d 23:59:59")
        elif text == "tomorrow":
            return (now + timedelta(days=1)).strftime("%Y-%m-%d 23:59:59")
        elif text == "next week":
            return (now + timedelta(weeks=1)).strftime("%Y-%m-%d 23:59:59")

        return due_str
