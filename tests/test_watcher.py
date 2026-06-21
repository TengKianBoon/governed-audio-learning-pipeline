from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from app.config import load_config
from app.watcher import process_folder_once


class WatcherTest(unittest.TestCase):
    def make_config(self, temp_dir: str):
        config_path = Path(temp_dir) / "paths.test.yaml"
        sandbox = Path(temp_dir) / "sandbox"
        config_path.write_text(
            "\n".join(
                [
                    f'sandbox_root: "{sandbox}"',
                    f'portfolio_public_root: "{Path(temp_dir) / "portfolio_public"}"',
                    f'notebooklm_artifacts_root: "{Path(temp_dir) / "notebooklm_artifacts"}"',
                    'ffmpeg_path: ""',
                    'ffprobe_path: ""',
                    'whisper_command: "whisper"',
                    "file_stability_checks: 1",
                    "file_stability_interval_seconds: 0",
                    "max_retries: 2",
                    "retry_backoff_seconds: 0",
                ]
            ),
            encoding="utf-8",
        )
        return load_config(config_path)

    def test_watcher_archives_successful_files_and_skips_processed_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self.make_config(temp_dir)
            incoming = config.incoming_dir
            incoming.mkdir(parents=True)
            source = incoming / "daily_note.m4a"
            source.write_bytes(b"fake audio")

            first = process_folder_once(incoming, config, mock=True, archive_after_success=True)
            second = process_folder_once(incoming, config, mock=True, archive_after_success=True)

            self.assertEqual(len(first), 1)
            self.assertEqual(second, [])
            self.assertFalse(source.exists())
            self.assertTrue((config.processed_archive_dir / "daily_note.m4a").exists())


if __name__ == "__main__":
    unittest.main()
