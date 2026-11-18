"""SQLite conversations and atomic exchanges; no model or HTTP logic."""
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from uuid import uuid4
from .domain import AppError, Conversation, Message


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ChatRepository:
    def __init__(self, path: Path):
        self.path = path

    @contextmanager
    def connection(self):
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1):
                raise RuntimeError("Unsupported database version; run a reviewed migration")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY, title TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS messages (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    id TEXT NOT NULL UNIQUE,
                    conversation_id TEXT NOT NULL REFERENCES conversations(id),
                    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                    content TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS messages_conversation
                    ON messages(conversation_id, sequence);
                CREATE TABLE IF NOT EXISTS exchanges (
                    conversation_id TEXT NOT NULL REFERENCES conversations(id),
                    request_id TEXT NOT NULL, input TEXT NOT NULL,
                    assistant_message_id TEXT NOT NULL REFERENCES messages(id),
                    PRIMARY KEY(conversation_id, request_id)
                );
                PRAGMA user_version = 1;
            """)

    def create_conversation(self) -> Conversation:
        item = Conversation(str(uuid4()), "新会话", now())
        with self.connection() as db:
            db.execute("INSERT INTO conversations VALUES (?, ?, ?)",
                       (item.id, item.title, item.created_at))
        return item

    def list_conversations(self) -> list[Conversation]:
        with self.connection() as db:
            return [Conversation(**dict(row)) for row in db.execute(
                "SELECT * FROM conversations ORDER BY created_at DESC LIMIT 100")]

    def history(self, conversation_id: str) -> tuple[Message, ...]:
        with self.connection() as db:
            if not db.execute("SELECT 1 FROM conversations WHERE id=?", (conversation_id,)).fetchone():
                raise AppError("conversation_not_found", "会话不存在", 404)
            rows = db.execute("SELECT id,role,content,created_at FROM messages "
                              "WHERE conversation_id=? ORDER BY sequence", (conversation_id,))
            return tuple(Message(**dict(row)) for row in rows)

    def _existing(self, db, conversation_id: str, request_id: str, text: str) -> Message | None:
        row = db.execute("SELECT e.input,m.id,m.role,m.content,m.created_at FROM exchanges e "
                         "JOIN messages m ON m.id=e.assistant_message_id "
                         "WHERE e.conversation_id=? AND e.request_id=?",
                         (conversation_id, request_id)).fetchone()
        if row is None:
            return None
        if row["input"] != text:
            raise AppError("request_id_conflict", "同一请求标识不能用于不同消息", 409)
        return Message(row["id"], row["role"], row["content"], row["created_at"])

    def existing(self, conversation_id: str, request_id: str, text: str) -> Message | None:
        with self.connection() as db:
            return self._existing(db, conversation_id, request_id, text)

    def save_exchange(self, conversation_id: str, request_id: str, text: str,
                      reply: str, expected_count: int) -> Message:
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = self._existing(db, conversation_id, request_id, text)
            if existing:
                return existing
            count = db.execute("SELECT COUNT(*) FROM messages WHERE conversation_id=?",
                               (conversation_id,)).fetchone()[0]
            if count != expected_count:
                raise AppError("conversation_changed", "会话已更新，请刷新后重试", 409)
            result = Message(str(uuid4()), "assistant", reply, now())
            db.executemany("INSERT INTO messages(id,conversation_id,role,content,created_at) "
                           "VALUES (?,?,?,?,?)", [
                (str(uuid4()), conversation_id, "user", text, now()),
                (result.id, conversation_id, result.role, result.content, result.created_at),
            ])
            db.execute("INSERT INTO exchanges VALUES (?,?,?,?)",
                       (conversation_id, request_id, text, result.id))
            if count == 0:
                db.execute("UPDATE conversations SET title=? WHERE id=?", (text[:24], conversation_id))
            return result
