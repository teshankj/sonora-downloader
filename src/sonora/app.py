"""Textual application shell and UI event orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, DataTable, Footer, Header, Input, Static

from sonora.audio.downloader import AudioDownloader
from sonora.config import ensure_user_config, load_config
from sonora.core.queue_manager import QueueManager
from sonora.storage.database import DownloadRepository


class SonoraApp(App[None]):
    TITLE = "SONORA Downloader"
    SUB_TITLE = "Local audio download manager"
    CSS_PATH = "ui/styles/app.tcss"

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+r", "start_queue", "Start queue"),
        ("ctrl+l", "focus_url", "URL"),
        ("f5", "refresh_table", "Refresh"),
    ]

    def __init__(self) -> None:
        super().__init__()
        ensure_user_config()
        self.config = load_config()
        self.repository = DownloadRepository()
        self.queue = QueueManager(self.repository)
        self._worker_running = False

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("♫  SONORA", id="app-title")
        yield Static("A terminal audio downloader", id="subtitle")
        yield Static("MEDIA URL", id="url-label")
        with Horizontal(id="url-row"):
            yield Input(
                placeholder="Paste a URL you are authorized to download…",
                id="url-input",
            )
            yield Button("Add to queue", id="add-button", variant="primary")
            yield Button("Start", id="start-button")
        yield Static("Ready · Add a URL to begin.", id="status-line")
        yield Static("DOWNLOAD QUEUE / HISTORY", classes="section-label")
        yield DataTable(id="queue-table")
        yield Static(
            "Ctrl+R Start queue   Ctrl+L Focus URL   F5 Refresh   Ctrl+Q Quit",
            id="help-line",
        )
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#queue-table", DataTable)
        table.add_columns("ID", "TITLE", "STATUS", "PROGRESS", "DETAIL")
        table.cursor_type = "row"
        self.refresh_table()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add-button":
            self.add_url()
        elif event.button.id == "start-button":
            self.start_queue()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "url-input":
            self.add_url()

    def add_url(self) -> None:
        input_widget = self.query_one("#url-input", Input)
        url = input_widget.value.strip()
        if not url:
            self.set_status("Enter a URL first.")
            return
        if not (url.startswith("https://") or url.startswith("http://")):
            self.set_status("Please enter a complete http:// or https:// URL.")
            return

        item = self.queue.enqueue(url)
        input_widget.value = ""
        self.set_status(f"Added task #{item.id} to the queue.")
        self.refresh_table()

    def action_focus_url(self) -> None:
        self.query_one("#url-input", Input).focus()

    def action_start_queue(self) -> None:
        self.start_queue()

    def start_queue(self) -> None:
        if self._worker_running:
            self.set_status("The queue is already running.")
            return
        if not self.queue.pending:
            self.set_status("There are no pending downloads.")
            return
        self._worker_running = True
        self.set_status("Starting download queue…")
        self.process_queue()

    @work(thread=True, exclusive=True, name="sonora-download-queue")
    def process_queue(self) -> None:
        try:
            while True:
                item = self.queue.next_item()
                if item is None:
                    break

                self.call_from_thread(self.refresh_table)
                self.call_from_thread(
                    self.set_status, f"Extracting metadata for task #{item.id}…"
                )

                download_settings = self.config.get("download", {})
                output_dir = Path(
                    download_settings.get("output_dir", "~/Music/SONORA")
                ).expanduser()

                downloader = AudioDownloader(
                    output_dir=output_dir,
                    audio_format=download_settings.get("audio_format", "mp3"),
                    audio_quality=str(download_settings.get("audio_quality", "192")),
                    embed_thumbnail=bool(
                        download_settings.get("embed_thumbnail", True)
                    ),
                    write_metadata=bool(
                        download_settings.get("write_metadata", True)
                    ),
                    noplaylist=bool(download_settings.get("noplaylist", False)),
                )

                def on_progress(data: dict[str, Any]) -> None:
                    status = data.get("status")
                    if status == "downloading":
                        total = data.get("total_bytes") or data.get(
                            "total_bytes_estimate"
                        )
                        downloaded = data.get("downloaded_bytes", 0)
                        percent = (
                            min(100.0, downloaded / total * 100.0)
                            if total else 0.0
                        )
                        item.progress = percent
                        item.status = "DOWNLOADING"
                        item.title = data.get("info_dict", {}).get(
                            "title", item.title
                        )
                        speed = data.get("_speed_str") or ""
                        eta = data.get("_eta_str") or ""
                        item.detail = f"{speed}  ETA {eta}".strip()
                        self.queue.update(item)
                        self.call_from_thread(self.refresh_table)
                    elif status == "finished":
                        item.progress = 100.0
                        item.status = "CONVERTING"
                        item.detail = "Download received; processing audio…"
                        self.queue.update(item)
                        self.call_from_thread(self.refresh_table)

                try:
                    result = downloader.download(item.url, on_progress)
                    item.title = result.get("title", item.title)
                    item.file_path = result.get("filepath", "")
                    item.status = "COMPLETED"
                    item.progress = 100.0
                    item.detail = (
                        f"{result.get('entries')} playlist entries"
                        if result.get("entries") is not None
                        else "Finished"
                    )
                except Exception as exc:
                    item.status = "FAILED"
                    item.detail = str(exc)[:180]
                finally:
                    self.queue.update(item)
                    self.queue.finish_active()
                    self.call_from_thread(self.refresh_table)
                    self.call_from_thread(
                        self.set_status, f"Task #{item.id}: {item.status} — {item.title}"
                    )
        finally:
            self._worker_running = False
            self.call_from_thread(self.refresh_table)
            self.call_from_thread(self.set_status, "Queue processing finished.")

    def refresh_table(self) -> None:
        table = self.query_one("#queue-table", DataTable)
        table.clear()
        for item in self.queue.snapshot():
            progress = f"{item.progress:.0f}%"
            title = item.title[:54]
            detail = item.detail[:42]
            table.add_row(
                str(item.id or ""),
                title,
                item.status,
                progress,
                detail,
                key=str(item.id or item.url),
            )

    def action_refresh_table(self) -> None:
        self.refresh_table()
        self.set_status("Queue/history refreshed.")

    def set_status(self, message: str) -> None:
        self.query_one("#status-line", Static).update(message)
