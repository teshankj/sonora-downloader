# SONORA Downloader v0.1.0

A modular, dark-themed terminal audio downloader built with Textual, yt-dlp, FFmpeg, and SQLite.

## Scope

- Add supported media URLs to a local download queue.
- Download audio using yt-dlp.
- Optionally extract/convert audio to MP3, M4A, OPUS, or FLAC.
- Display progress and task states.
- Persist download history in SQLite.
- Keep UI, download engine, configuration, and persistence separate.

Only download content you own, are authorized to download, or that is otherwise legally downloadable. Follow source-site terms and applicable copyright law. This app does not bypass DRM, paywalls, or access controls.

## Requirements

- Python 3.12+
- FFmpeg available on `PATH`
- yt-dlp-compatible source URL

## Install on Linux Mint / Ubuntu

```bash
sudo apt update
sudo apt install -y ffmpeg python3-venv

cd ~/Projects/sonora-downloader
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

If you already created the virtual environment and installed the dependencies, run:

```bash
python -m pip install -e .
```

## Run

```bash
sonora
# or
python -m sonora.main
```

## Keyboard shortcuts

- `Ctrl+Q`: quit
- `Ctrl+R`: start queued downloads
- `Ctrl+L`: focus URL input
- `F5`: refresh history/queue display

## Default locations

- Downloads: `~/Music/SONORA`
- Database: `~/.local/share/sonora/sonora.sqlite3`
- Configuration: `~/.config/sonora/config.toml`

The application creates these directories automatically.

## Notes

- v0.1.0 processes queued items sequentially (one active download).
- Progress callbacks are sent from the yt-dlp worker thread to the Textual UI.
- Pause/resume is not exposed in this first version; cancellation and robust resume handling are future work.
- FLAC conversion does not restore quality lost in a lossy source.
