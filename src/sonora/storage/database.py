"""SQLite persistence. Each operation opens its own short-lived connection."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from sonora.config import data_dir
from sonora.models import DownloadItem


class DownloadRepository:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or (data_dir() / "sonora.sqlite3")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS downloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress REAL NOT NULL DEFAULT 0,
                    detail TEXT NOT NULL DEFAULT '',
                    file_path TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL
                )
                """
            )

    def add(self, item: DownloadItem) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO downloads
                    (url, title, status, progress, detail, file_path, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.url, item.title, item.status, item.progress,
                    item.detail, item.file_path, item.created_at,
                ),
            )
            return int(cursor.lastrowid)

    def update(self, item: DownloadItem) -> None:
        if item.id is None:
            return
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE downloads
                SET title=?, status=?, progress=?, detail=?, file_path=?
                WHERE id=?
                """,
                (
                    item.title, item.status, item.progress, item.detail,
                    item.file_path, item.id,
                ),
            )

    def recent(self, limit: int = 100) -> list[DownloadItem]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM downloads ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [
            DownloadItem(
                id=row["id"], url=row["url"], title=row["title"],
                status=row["status"], progress=row["progress"],
                detail=row["detail"], file_path=row["file_path"],
                created_at=row["created_at"],
            )
            for row in rows
        ]
