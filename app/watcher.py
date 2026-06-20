from __future__ import annotations

from pathlib import Path
import time

from .config import AppConfig
from .media import is_supported_input, wait_until_stable
from .pipeline import process_file


def process_folder_once(folder: Path, config: AppConfig, *, mock: bool = False) -> list:
    results = []
    for path in sorted(folder.iterdir()):
        if path.is_file() and is_supported_input(path):
            wait_until_stable(path, config.file_stability_checks, config.file_stability_interval_seconds)
            results.append(process_file(path, config, mock=mock))
    return results


def watch_folder(folder: Path, config: AppConfig, *, once: bool = False, mock: bool = False, poll_seconds: int = 10) -> None:
    while True:
        process_folder_once(folder, config, mock=mock)
        if once:
            return
        time.sleep(poll_seconds)
