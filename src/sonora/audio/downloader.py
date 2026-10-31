"""yt-dlp download engine, deliberately independent of the Textual UI."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from yt_dlp import YoutubeDL


ProgressCallback = Callable[[dict[str, Any]], None]


class AudioDownloader:
    def __init__(
        self,
        output_dir: Path,
        audio_format: str = "mp3",
        audio_quality: str = "192",
        embed_thumbnail: bool = True,
        write_metadata: bool = True,
        noplaylist: bool = False,
    ) -> None:
        self.output_dir = output_dir.expanduser()
        self.audio_format = audio_format.lower()
        self.audio_quality = audio_quality
        self.embed_thumbnail = embed_thumbnail
        self.write_metadata = write_metadata
        self.noplaylist = noplaylist

    def download(self, url: str, progress_callback: ProgressCallback) -> dict[str, Any]:
        self.output_dir.mkdir(parents=True, exist_ok=True)

        def hook(data: dict[str, Any]) -> None:
            progress_callback(data)

        postprocessors: list[dict[str, Any]] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": self.audio_format,
                "preferredquality": self.audio_quality,
            }
        ]
        if self.write_metadata:
            postprocessors.append({"key": "FFmpegMetadata"})
        if self.embed_thumbnail:
            postprocessors.append(
                {"key": "EmbedThumbnail", "already_have_thumbnail": False}
            )

        options: dict[str, Any] = {
            "format": "bestaudio/best",
            "outtmpl": str(self.output_dir / "%(title).180B [%(id)s].%(ext)s"),
            "noplaylist": self.noplaylist,
            "ignoreerrors": False,
            "continuedl": True,
            "overwrites": False,
            "writethumbnail": self.embed_thumbnail,
            "progress_hooks": [hook],
            "postprocessors": postprocessors,
            "quiet": True,
            "no_warnings": False,
        }

        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            if info is None:
                raise RuntimeError("yt-dlp did not return media information")
            if "entries" in info:
                entries = [entry for entry in info.get("entries", []) if entry]
                title = info.get("title") or "Playlist"
                return {"title": title, "filepath": "", "entries": len(entries)}
            return {
                "title": info.get("title") or "Untitled",
                "filepath": info.get("filepath") or "",
                "id": info.get("id"),
            }
