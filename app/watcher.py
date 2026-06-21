from __future__ import annotations

from pathlib import Path
import time

from .config import AppConfig
from .media import is_supported_input, wait_until_stable
from .pipeline import process_file
from .registry import is_fingerprint_processed
from .utils import fingerprint_file


def process_folder_once(
    folder: Path,
    config: AppConfig,
    *,
    mock: bool = False,
    archive_after_success: bool = True,
    skip_processed: bool = True,
) -> list:
    results = []
    for path in sorted(folder.iterdir()):
        if path.is_file() and is_supported_input(path):
            wait_until_stable(path, config.file_stability_checks, config.file_stability_interval_seconds)
            fingerprint = fingerprint_file(path)
            if skip_processed and is_fingerprint_processed(config.state_dir, fingerprint):
                continue
            results.append(process_file(path, config, mock=mock, archive_after_success=archive_after_success))
    return results


def watch_folder(
    folder: Path,
    config: AppConfig,
    *,
    once: bool = False,
    mock: bool = False,
    poll_seconds: int = 10,
    archive_after_success: bool = True,
) -> None:
    while True:
        process_folder_once(folder, config, mock=mock, archive_after_success=archive_after_success)
        if once:
            return
        time.sleep(poll_seconds)
