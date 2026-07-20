"""Chat History Repository —— 对话记录持久化

支持按 auth_code 保存和查询对话历史。
表结构:

  chat_history
  ├── id            INTEGER PRIMARY KEY
  ├── auth_code     TEXT NOT NULL       — 用户授权码
  ├── session_id    TEXT NOT NULL       — 前端会话 ID（用于同一组对话归组）
  ├── role          TEXT NOT NULL       — 'user' | 'assistant'
  ├── content       TEXT NOT NULL       — 消息内容
  ├── scene         TEXT DEFAULT ''     — 对话场景 (school/essay/visa)
  ├── created_at    TEXT DEFAULT (datetime('now'))
"""

import sqlite3
import logging
from typing import Optional
from ..core.config import settings

logger = logging.getLogger(__name__)

TABLE = "chat_history"

CREATE_SQL = f"""
CREATE TABLE IF NOT EXISTS {TABLE} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    auth_code TEXT NOT NULL,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    scene TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
CREATE INDEX IF NOT EXISTS idx_chat_auth_code ON {TABLE}(auth_code);
CREATE INDEX IF NOT EXISTS idx_chat_session ON {TABLE}(auth_code, session_id);
"""


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def ensure_table():
    """确保 chat_history 表存在（幂等）。"""
    with _get_conn() as conn:
        conn.executescript(CREATE_SQL)
        conn.commit()


def save_turn(
    auth_code: str,
    session_id: str,
    user_message: str,
    assistant_message: str,
    scene: str = "",
) -> None:
    """保存一轮用户+助手的对话。"""
    ensure_table()
    with _get_conn() as conn:
        conn.execute(
            f"INSERT INTO {TABLE} (auth_code, session_id, role, content, scene) VALUES (?, ?, 'user', ?, ?)",
            (auth_code, session_id, user_message, scene),
        )
        conn.execute(
            f"INSERT INTO {TABLE} (auth_code, session_id, role, content, scene) VALUES (?, ?, 'assistant', ?, ?)",
            (auth_code, session_id, assistant_message, scene),
        )
        conn.commit()


def get_history(
    auth_code: str,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    """获取用户的历史对话记录，按时间倒序，每条含完整消息列表。"""
    ensure_table()
    with _get_conn() as conn:
        # 先获取所有 session_id（最近对话在前）
        sessions = conn.execute(
            f"""SELECT session_id, scene, MAX(created_at) as last_time
                FROM {TABLE}
                WHERE auth_code = ?
                GROUP BY session_id, scene
                ORDER BY last_time DESC
                LIMIT ? OFFSET ?""",
            (auth_code, limit, offset),
        ).fetchall()

        result = []
        for sess in sessions:
            messages = conn.execute(
                f"""SELECT role, content, scene, created_at
                    FROM {TABLE}
                    WHERE auth_code = ? AND session_id = ?
                    ORDER BY id ASC""",
                (auth_code, sess["session_id"]),
            ).fetchall()
            result.append({
                "session_id": sess["session_id"],
                "scene": sess["scene"],
                "last_time": sess["last_time"],
                "message_count": len(messages),
                "messages": [dict(m) for m in messages],
            })
        return result


def delete_history(auth_code: str, session_id: Optional[str] = None) -> int:
    """删除用户的历史记录。session_id 为空时清空全部。"""
    ensure_table()
    with _get_conn() as conn:
        if session_id:
            r = conn.execute(
                f"DELETE FROM {TABLE} WHERE auth_code = ? AND session_id = ?",
                (auth_code, session_id),
            )
        else:
            r = conn.execute(
                f"DELETE FROM {TABLE} WHERE auth_code = ?",
                (auth_code,),
            )
        conn.commit()
        return r.rowcount
