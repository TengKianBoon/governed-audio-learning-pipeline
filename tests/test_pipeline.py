from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from app.config import load_config
from app.pipeline import process_file
from app.publishing import PublishingGateError, assert_public_safe, build_public_note, sanitize_all, sanitize_package


class PipelineTest(unittest.TestCase):
    def make_config(self, temp_dir: str):
        config_path = Path(temp_dir) / "paths.test.yaml"
        sandbox = Path(temp_dir) / "sandbox"
        config_path.write_text(
            "\n".join(
                [
                    f'sandbox_root: "{sandbox}"',
                    f'portfolio_public_root: "{Path(temp_dir) / "portfolio_public"}"',
                    "ffmpeg_path: \"\"",
                    "ffprobe_path: \"\"",
                    "whisper_command: \"whisper\"",
                    "max_retries: 2",
                    "retry_backoff_seconds: 0",
                ]
            ),
            encoding="utf-8",
        )
        return load_config(config_path)

    def make_config_with_full_translation(self, temp_dir: str):
        config_path = Path(temp_dir) / "paths.full-translation.test.yaml"
        sandbox = Path(temp_dir) / "sandbox"
        config_path.write_text(
            "\n".join(
                [
                    f'sandbox_root: "{sandbox}"',
                    f'portfolio_public_root: "{Path(temp_dir) / "portfolio_public"}"',
                    'ffmpeg_path: ""',
                    'ffprobe_path: ""',
                    'whisper_command: "whisper"',
                    "generate_full_english_transcript: true",
                    "max_retries: 2",
                    "retry_backoff_seconds: 0",
                ]
            ),
            encoding="utf-8",
        )
        return load_config(config_path)

    def test_mock_process_creates_private_artifacts_and_budget(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "sample.m4a"
            source.write_bytes(b"fake audio")
            config = self.make_config(temp_dir)

            result = process_file(source, config, mock=True, mock_duration_seconds=65)

            self.assertTrue(source.exists(), "source should not move unless --archive is used")
            self.assertEqual(result.quality_score, 100)
            self.assertTrue((result.private_output_dir / "source_metadata.json").exists())
            self.assertTrue((result.private_output_dir / "original_transcript.md").exists())
            self.assertTrue((result.private_output_dir / "english_transcribed.md").exists())
            self.assertTrue((result.private_output_dir / "mindmap_ingest.md").exists())
            self.assertTrue((result.private_output_dir / "cost_budget.json").exists())

    def test_mock_process_auto_applies_mindmap_delta_to_private_graph(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "agent_quality_loop.m4a"
            source.write_bytes(b"fake audio")
            config = self.make_config(temp_dir)

            result = process_file(source, config, mock=True, mock_duration_seconds=65)

            graph = json.loads((config.mindmap_dir / "graph.json").read_text(encoding="utf-8"))
            delta = json.loads((result.private_output_dir / "mindmap_delta.json").read_text(encoding="utf-8"))
            labels = {node["label"] for node in graph["nodes"]}
            self.assertTrue(delta["auto_applied_private_graph"])
            self.assertIn("agent", labels)

    def test_mock_process_accepts_english_text_transcript(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "phone_transcript.txt"
            source.write_text(
                "Enterprise AI agents need quality gates, human review, retry limits, and cost controls.",
                encoding="utf-8",
            )
            config = self.make_config(temp_dir)

            result = process_file(source, config, mock=True)

            metadata = json.loads((result.private_output_dir / "source_metadata.json").read_text(encoding="utf-8"))
            english = (result.private_output_dir / "english_transcribed.md").read_text(encoding="utf-8")
            summary = (result.private_output_dir / "summary.md").read_text(encoding="utf-8")
            self.assertEqual(metadata["input_kind"], "text_transcript")
            self.assertEqual(metadata["detected_language"], "en")
            self.assertEqual(metadata["translation_status"], "skipped_source_is_english")
            self.assertIn("Enterprise AI agents", english)
            self.assertIn("Learning Summary", summary)

    def test_mock_process_accepts_chinese_text_transcript(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "phone_transcript_cn.txt"
            source.write_text("企业人工智能代理需要质量关卡、人工审核、重试限制和成本控制。", encoding="utf-8")
            config = self.make_config(temp_dir)

            result = process_file(source, config, mock=True)

            metadata = json.loads((result.private_output_dir / "source_metadata.json").read_text(encoding="utf-8"))
            english = (result.private_output_dir / "english_transcribed.md").read_text(encoding="utf-8")
            self.assertEqual(metadata["input_kind"], "text_transcript")
            self.assertEqual(metadata["detected_language"], "zh")
            self.assertEqual(metadata["translation_status"], "skipped_full_translation_summary_direct")
            self.assertEqual(metadata["summary_input_artifact"], "original_transcript.md")
            self.assertIn("full English transcript was intentionally not generated", english)

    def test_full_translation_can_be_enabled_for_chinese_text_transcript(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "phone_transcript_cn.txt"
            source.write_text("企业人工智能代理需要质量关卡、人工审核、重试限制和成本控制。", encoding="utf-8")
            config = self.make_config_with_full_translation(temp_dir)

            result = process_file(source, config, mock=True)

            metadata = json.loads((result.private_output_dir / "source_metadata.json").read_text(encoding="utf-8"))
            english = (result.private_output_dir / "english_transcribed.md").read_text(encoding="utf-8")
            self.assertTrue(metadata["generate_full_english_transcript"])
            self.assertEqual(metadata["translation_status"], "openai_translated_to_english")
            self.assertEqual(metadata["summary_input_artifact"], "english_transcribed.md")
            self.assertIn("Mock English translation", english)

    def test_archive_only_after_success_when_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "archive_me.m4a"
            source.write_bytes(b"fake audio")
            config = self.make_config(temp_dir)

            result = process_file(source, config, mock=True, archive_after_success=True)

            self.assertFalse(source.exists())
            self.assertIsNotNone(result.archived_to)
            self.assertTrue(result.archived_to.exists())

    def test_sanitize_package_blocks_full_transcripts_from_public_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "sample.m4a"
            source.write_bytes(b"fake audio")
            config = self.make_config(temp_dir)
            result = process_file(source, config, mock=True)

            public_output = sanitize_package(result.private_output_dir, config.public_review_dir)

            self.assertTrue((public_output / "summary.md").exists())
            self.assertFalse((public_output / "original_transcript.md").exists())
            self.assertFalse((public_output / "english_transcribed.md").exists())
            assert_public_safe(public_output)

    def test_sanitize_package_creates_polished_index_and_removes_system_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "sample.m4a"
            source.write_bytes(b"fake audio")
            config = self.make_config(temp_dir)
            result = process_file(source, config, mock=True)

            stale_output = config.public_review_dir / result.private_output_dir.name
            stale_output.mkdir(parents=True)
            (stale_output / "desktop.ini").write_text("[ViewState]", encoding="utf-8")

            public_output = sanitize_package(result.private_output_dir, config.public_review_dir)

            self.assertTrue((public_output / "index.html").exists())
            self.assertTrue((public_output / "public_learning_note.html").exists())
            self.assertTrue((public_output / "mindmap_ingest.html").exists())
            self.assertTrue((public_output / "quality_gate.html").exists())
            self.assertTrue((public_output / "source_metadata.html").exists())
            self.assertFalse((public_output / "desktop.ini").exists())
            index_html = (public_output / "index.html").read_text(encoding="utf-8")
            self.assertIn("TKB Public Review Package", index_html)
            self.assertIn("../../mindmap/enterprise_ai_mindmap.html", index_html)
            self.assertIn("Back to Enterprise AI Solutions Framework", index_html)
            self.assertIn("public_learning_note.html", index_html)
            self.assertIn("mindmap_ingest.html", index_html)
            self.assertIn("quality_gate.html", index_html)
            self.assertIn("source_metadata.html", index_html)
            self.assertNotIn("mindmap_delta.json", index_html)

    def test_sanitize_package_hides_private_transcript_artifact_names_from_public_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "phone_transcript_cn.txt"
            source.write_text("智能代理需要质量门和人工审查。", encoding="utf-8")
            config = self.make_config(temp_dir)
            result = process_file(source, config, mock=True)

            public_output = sanitize_package(result.private_output_dir, config.public_review_dir)
            metadata_text = (public_output / "source_metadata_public.json").read_text(encoding="utf-8")
            metadata_html = (public_output / "source_metadata.html").read_text(encoding="utf-8")

            self.assertIn("private transcript artifact withheld", metadata_text)
            self.assertNotIn("original_transcript.md", metadata_text)
            self.assertNotIn("original_transcript.md", metadata_html)
            assert_public_safe(public_output)

    def test_sanitize_all_removes_root_system_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "sample.m4a"
            source.write_bytes(b"fake audio")
            config = self.make_config(temp_dir)
            process_file(source, config, mock=True)
            config.public_review_dir.mkdir(parents=True, exist_ok=True)
            (config.public_review_dir / "desktop.ini").write_text("[ViewState]", encoding="utf-8")

            sanitize_all(config.private_outputs_dir, config.public_review_dir)

            self.assertFalse((config.public_review_dir / "desktop.ini").exists())

    def test_sanitize_all_skips_development_sample_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "sample.m4a"
            source.write_bytes(b"fake audio")
            config = self.make_config(temp_dir)
            result = process_file(source, config, mock=True)
            stale_output = config.public_review_dir / result.private_output_dir.name
            stale_output.mkdir(parents=True, exist_ok=True)
            (stale_output / "index.html").write_text("old sample output", encoding="utf-8")

            outputs = sanitize_all(config.private_outputs_dir, config.public_review_dir)

            self.assertEqual(outputs, [])
            self.assertFalse(stale_output.exists())

    def test_sanitize_all_removes_orphaned_development_sample_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self.make_config(temp_dir)
            stale_output = config.public_review_dir / "20260619-sample-4f34cc3b"
            stale_output.mkdir(parents=True, exist_ok=True)
            (stale_output / "index.html").write_text("old sample output", encoding="utf-8")

            sanitize_all(config.private_outputs_dir, config.public_review_dir)

            self.assertFalse(stale_output.exists())

    def test_public_note_with_failed_quality_withholds_rough_machine_draft(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            package = Path(temp_dir) / "learning"
            package.mkdir()
            (package / "summary.md").write_text(
                "Out of my mind again I have been interested in self-proving agent self-improving agent.",
                encoding="utf-8",
            )
            (package / "source_metadata.json").write_text(
                '{"source_filename": "Voice 260619_170242 Self Improving Agent.m4a"}',
                encoding="utf-8",
            )
            note = build_public_note(
                package,
                quality={
                    "passed": False,
                    "score": 80,
                    "transcript_findings": ["english_translation_contains_cjk_characters"],
                },
            )

            self.assertIn("Review Holding Page", note)
            self.assertIn("Self Improving Agent", note)
            self.assertIn("intentionally withheld", note)
            self.assertNotIn("Out of my mind again", note)

    def test_public_note_scrubs_overt_hiring_and_fde_language_from_older_summaries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            package = Path(temp_dir) / "learning"
            package.mkdir()
            (package / "summary.md").write_text(
                "## Enterprise AI / FDE Relevance\n\n"
                "For a Field Deployment Engineer (FDE), this shows practical FDE thinking. "
                "This is what hiring reviewers care about.\n\n"
                "## Portfolio Note\n\n"
                "This is not a job application, but it says employment too loudly.",
                encoding="utf-8",
            )
            note = build_public_note(
                package,
                quality={"passed": True, "score": 100, "transcript_findings": [], "summary_findings": []},
            )

            self.assertIn("Enterprise AI Architecture and Delivery Relevance", note)
            self.assertIn("Public Practice Note", note)
            self.assertNotIn("Field Deployment Engineer", note)
            self.assertNotIn("FDE", note)
            self.assertNotIn("hiring reviewers", note)
            self.assertNotIn("employment", note)

    def test_public_gate_refuses_private_transcript(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            package = Path(temp_dir) / "bad_public"
            package.mkdir()
            (package / "original_transcript.md").write_text("private transcript", encoding="utf-8")
            with self.assertRaises(PublishingGateError):
                assert_public_safe(package)


if __name__ == "__main__":
    unittest.main()
