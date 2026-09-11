"""
JARVIS History Repository - Querying and logging voice interactions
Provides date-grouped command history, indexed search, and execution logs.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from .database import Database


class HistoryRepository:
    def __init__(self, db: Optional[Database] = None):
        self.db = db or Database()
        self._current_session_id: Optional[str] = None

    def get_or_create_session(self, title: str = "Voice Session") -> str:
        if self._current_session_id:
            return self._current_session_id

        session_id = str(uuid.uuid4())
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.db.get_connection() as conn:
            conn.execute(
                "INSERT INTO sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (session_id, title, now_str, now_str),
            )
            conn.commit()
        self._current_session_id = session_id
        return session_id

    def log_interaction(
        self,
        command_text: str,
        response_text: str,
        tool: str = "Assistant",
        action: str = "execute",
        params: Optional[Dict[str, Any]] = None,
        status: str = "SUCCESS",
        result_summary: str = "",
        session_id: Optional[str] = None,
    ) -> Dict[str, str]:
        """Logs a full user command, assistant response, and tool action trace."""
        sess_id = session_id or self.get_or_create_session()
        msg_id_user = str(uuid.uuid4())
        msg_id_asst = str(uuid.uuid4())
        action_id = str(uuid.uuid4())

        params_json = json.dumps(params or {}, ensure_ascii=False)

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.db.get_connection() as conn:
            # User message
            conn.execute(
                "INSERT INTO messages (id, session_id, role, content, reply_to_id, timestamp) VALUES (?, ?, 'user', ?, NULL, ?)",
                (msg_id_user, sess_id, command_text, now_str),
            )
            # Assistant message
            conn.execute(
                "INSERT INTO messages (id, session_id, role, content, reply_to_id, timestamp) VALUES (?, ?, 'assistant', ?, ?, ?)",
                (msg_id_asst, sess_id, response_text, msg_id_user, now_str),
            )
            # Action entry
            conn.execute(
                """INSERT INTO actions (id, message_id, tool, action, params, status, result_summary, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (action_id, msg_id_asst, tool, action, params_json, status, result_summary, now_str),
            )
            # Update session timestamp
            conn.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (now_str, sess_id),
            )
            conn.commit()

        return {
            "session_id": sess_id,
            "user_message_id": msg_id_user,
            "assistant_message_id": msg_id_asst,
            "action_id": action_id,
        }

    def get_grouped_history(self, search_query: str = "", limit: int = 100) -> Dict[str, List[Dict[str, Any]]]:
        """
        Returns history grouped by TODAY, YESTERDAY, THIS WEEK, OLDER.
        Efficiently joins user prompt, assistant answer, and action details.
        """
        now = datetime.now()
        today_start = datetime(now.year, now.month, now.day)
        yesterday_start = today_start - timedelta(days=1)
        this_week_start = today_start - timedelta(days=now.weekday())

        sql = """
            SELECT 
                u.id as user_msg_id,
                u.content as command,
                u.timestamp as timestamp,
                u.session_id as session_id,
                a.content as response,
                act.id as action_id,
                act.tool as tool,
                act.action as action_name,
                act.params as params,
                act.status as status,
                act.result_summary as result_summary
            FROM messages u
            LEFT JOIN messages a ON a.reply_to_id = u.id
            LEFT JOIN actions act ON act.message_id = a.id
            WHERE u.role = 'user'
        """
        params_list = []

        if search_query.strip():
            sql += " AND (u.content LIKE ? OR a.content LIKE ? OR act.tool LIKE ? OR act.action LIKE ?)"
            q = f"%{search_query.strip()}%"
            params_list.extend([q, q, q, q])

        sql += " GROUP BY u.id ORDER BY u.timestamp DESC LIMIT ?"
        params_list.append(limit)

        grouped = {
            "TODAY": [],
            "YESTERDAY": [],
            "THIS WEEK": [],
            "OLDER": [],
        }

        with self.db.get_connection() as conn:
            cursor = conn.execute(sql, params_list)
            rows = cursor.fetchall()

            for row in rows:
                item = dict(row)
                ts_str = item["timestamp"]
                try:
                    # SQLite timestamp format: 'YYYY-MM-DD HH:MM:SS'
                    item_dt = datetime.strptime(ts_str[:19], "%Y-%m-%d %H:%M:%S")
                except Exception:
                    item_dt = now

                # Display time like "09:42 PM"
                item["formatted_time"] = item_dt.strftime("%I:%M %p")
                item["formatted_date"] = item_dt.strftime("%b %d, %Y")

                if item_dt >= today_start:
                    grouped["TODAY"].append(item)
                elif item_dt >= yesterday_start:
                    grouped["YESTERDAY"].append(item)
                elif item_dt >= this_week_start:
                    grouped["THIS WEEK"].append(item)
                else:
                    grouped["OLDER"].append(item)

        return grouped

    def delete_item(self, user_msg_id: str) -> bool:
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM messages WHERE id = ?", (user_msg_id,))
            conn.commit()
            return True

    def clear_today(self) -> int:
        now = datetime.now()
        today_start = datetime(now.year, now.month, now.day).strftime("%Y-%m-%d 00:00:00")
        with self.db.get_connection() as conn:
            cursor = conn.execute("DELETE FROM messages WHERE timestamp >= ?", (today_start,))
            conn.commit()
            return cursor.rowcount

    def clear_all(self) -> int:
        with self.db.get_connection() as conn:
            cursor = conn.execute("DELETE FROM messages")
            conn.execute("DELETE FROM actions")
            conn.execute("DELETE FROM sessions")
            conn.commit()
            return cursor.rowcount
