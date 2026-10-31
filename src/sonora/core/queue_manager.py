"""In-memory sequential queue with persisted task records."""

from __future__ import annotations

from collections import deque

from sonora.models import DownloadItem
from sonora.storage.database import DownloadRepository


class QueueManager:
    def __init__(self, repository: DownloadRepository) -> None:
        self.repository = repository
        self.pending: deque[DownloadItem] = deque()
        self.active: DownloadItem | None = None

    def enqueue(self, url: str) -> DownloadItem:
        item = DownloadItem.new(url)
        item.id = self.repository.add(item)
        self.pending.append(item)
        return item

    def next_item(self) -> DownloadItem | None:
        if not self.pending:
            return None
        self.active = self.pending.popleft()
        self.active.status = "EXTRACTING"
        self.repository.update(self.active)
        return self.active

    def update(self, item: DownloadItem) -> None:
        self.repository.update(item)

    def finish_active(self) -> None:
        self.active = None

    def snapshot(self) -> list[DownloadItem]:
        return list(reversed(self.repository.recent(100)))
