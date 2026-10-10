import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


class MemoryStore:
    def __init__(self, database_path="data/memories.sqlite3"):
        self.database_path = database_path
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        self._create_table()

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.database_path)
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _create_table(self):
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    source_message TEXT NOT NULL,
                    slot TEXT,
                    status TEXT NOT NULL DEFAULT 'active',
                    replaced_by INTEGER,
                    embedding TEXT
                )
                """
            )

    def add_memory(
        self,
        text,
        memory_type,
        source_message,
        slot=None,
        embedding=None,
    ):
        created_at = datetime.now(timezone.utc).isoformat()
        embedding_json = json.dumps(embedding) if embedding is not None else None

        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO memories
                    (text, memory_type, created_at, source_message, slot, embedding)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    text,
                    memory_type,
                    created_at,
                    source_message,
                    slot,
                    embedding_json,
                ),
            )
            new_id = cursor.lastrowid

            if slot:
                connection.execute(
                    """
                    UPDATE memories
                    SET status = 'replaced', replaced_by = ?
                    WHERE slot = ? AND status = 'active' AND id != ?
                    """,
                    (new_id, slot, new_id),
                )

        return new_id

    def list_memories(self, include_replaced=True):
        query = """
            SELECT id, text, memory_type, created_at, source_message,
                   slot, status, replaced_by
            FROM memories
        """
        if not include_replaced:
            query += " WHERE status = 'active'"
        query += " ORDER BY id"

        with self._connect() as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(query).fetchall()
            return [dict(row) for row in rows]

    def get_active_memories_with_embeddings(self):
        with self._connect() as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT id, text, memory_type, created_at, source_message, embedding
                FROM memories
                WHERE status = 'active' AND embedding IS NOT NULL
                """
            ).fetchall()
            return [dict(row) for row in rows]

    def delete_memory(self, memory_id):
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM memories WHERE id = ?",
                (memory_id,),
            )
            return cursor.rowcount > 0
