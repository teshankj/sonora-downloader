"""Domain models shared by the application."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(slots=True)
class DownloadItem:
    id: int | None
    url: str
    title: str = "Waiting for metadata"
    status: str = "PENDING"
    progress: float = 0.0
    detail: str = ""
    file_path: str = ""
    created_at: str = ""

    @classmethod
    def new(cls, url: str) -> "DownloadItem":
        return cls(
            id=None,
            url=url.strip(),
            created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )
