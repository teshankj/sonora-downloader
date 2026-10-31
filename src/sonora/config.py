"""Configuration loading and application paths."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

APP_NAME = "sonora"


def config_dir() -> Path:
    return Path.home() / ".config" / APP_NAME


def data_dir() -> Path:
    return Path.home() / ".local" / "share" / APP_NAME


def default_config_path() -> Path:
    return config_dir() / "config.toml"


def default_output_dir() -> Path:
    return Path.home() / "Music" / "SONORA"


def load_config() -> dict[str, Any]:
    path = default_config_path()
    if not path.exists():
        bundled = Path(__file__).resolve().parents[2] / "config" / "default.toml"
        if bundled.exists():
            with bundled.open("rb") as handle:
                return tomllib.load(handle)
        return {
            "download": {
                "output_dir": str(default_output_dir()),
                "audio_format": "mp3",
                "audio_quality": "192",
                "embed_thumbnail": True,
                "write_metadata": True,
                "noplaylist": False,
            }
        }

    with path.open("rb") as handle:
        return tomllib.load(handle)


def ensure_user_config() -> None:
    """Create a user config on first run, without overwriting an existing file."""
    path = default_config_path()
    if path.exists():
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    output = default_output_dir()
    output.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "[download]\\n"
        f'output_dir = "{output}"\\n'
        'audio_format = "mp3"\\n'
        'audio_quality = "192"\\n'
        "embed_thumbnail = true\\n"
        "write_metadata = true\\n"
        "noplaylist = false\\n",
        encoding="utf-8",
    )
