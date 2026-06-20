from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import time
import unittest

from app.cleanup import plan_cleanup
from app.config import ensure_sandbox_dirs, load_config
from app.mcp_tools import call_tool


class CleanupPlannerTest(unittest.TestCase):
    def make_config(self, temp_dir: str) -> Path:
        config_path = Path(temp_dir) / "paths.test.yaml"
        sandbox = Path(temp_dir) / "sandbox"
        config_path.write_text(
            "\n".join(
                [
                    f'sandbox_root: "{sandbox}"',
                    f'portfolio_public_root: "{Path(temp_dir) / "portfolio_public"}"',
                    'ffmpeg_path: ""',
                    'ffprobe_path: ""',
                    'whisper_command: ".venv/Scripts/whisper.exe"',
                ]
            ),
            encoding="utf-8",
        )
        return config_path

    def test_cleanup_dry_run_reports_expected_categories_without_deleting(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = self.make_config(temp_dir)
            config = load_config(config_path)
            ensure_sandbox_dirs(config)

            processing_file = config.processing_dir / "chunks" / "old.wav"
            processing_file.write_bytes(b"old processing file")
            old_time = time.time() - 3 * 86400
            os.utime(processing_file, (old_time, old_time))

            sample_public = config.public_review_dir / "20260619-sample-4f34cc3b"
            sample_public.mkdir(parents=True)
            (sample_public / "index.html").write_text("sample", encoding="utf-8")

            failed_public = config.public_review_dir / "20260620-real-failed"
            failed_public.mkdir(parents=True)
            (failed_public / "quality_score.json").write_text(
                json.dumps({"score": 60, "passed": False, "transcript_findings": ["needs_review"]}),
                encoding="utf-8",
            )

            learning_a = config.private_outputs_dir / "learnings" / "duplicate-a"
            learning_b = config.private_outputs_dir / "learnings" / "duplicate-b"
            learning_a.mkdir(parents=True)
            learning_b.mkdir(parents=True)
            for package, score in ((learning_a, 80), (learning_b, 100)):
                (package / "source_metadata.json").write_text(
                    json.dumps({"fingerprint_sha256": "same-fingerprint", "processed_at": f"2026-06-20T00:00:0{score % 10}+00:00"}),
                    encoding="utf-8",
                )
                (package / "quality_score.json").write_text(json.dumps({"score": score}), encoding="utf-8")

            archive_file = config.processed_archive_dir / "large.m4a"
            archive_file.write_bytes(b"archive")

            report = plan_cleanup(config, processing_stale_days=1, oversized_archive_mb=0)
            categories = {candidate["category"] for candidate in report["candidates"]}

            self.assertEqual(report["mode"], "dry_run")
            self.assertFalse(report["applies_changes"])
            self.assertIn("stale_processing_file", categories)
            self.assertIn("development_public_package", categories)
            self.assertIn("failed_public_package", categories)
            self.assertIn("duplicate_private_package", categories)
            self.assertIn("oversized_archive_file", categories)
            self.assertTrue(processing_file.exists())
            self.assertTrue(sample_public.exists())

    def test_cleanup_tool_exposes_dry_run_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = self.make_config(temp_dir)
            result = call_tool(
                "plan_workspace_cleanup",
                {"config_path": str(config_path), "processing_stale_days": 1, "oversized_archive_mb": 1},
            )

            self.assertEqual(result["mode"], "dry_run")
            self.assertFalse(result["applies_changes"])
            self.assertIn("candidate_count", result["summary"])


if __name__ == "__main__":
    unittest.main()
