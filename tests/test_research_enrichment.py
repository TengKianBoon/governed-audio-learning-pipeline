from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from app.config import load_config
from app.pipeline import process_file
from app.publishing import sanitize_package
from app.research_enrichment import enrich_learning_research


class ResearchEnrichmentTest(unittest.TestCase):
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
                    'openai_research_model: "gpt-5.4-mini"',
                    'openai_research_reasoning_effort: "high"',
                    'openai_research_search_context_size: "high"',
                    "max_retries: 2",
                    "retry_backoff_seconds: 0",
                ]
            ),
            encoding="utf-8",
        )
        return load_config(config_path)

    def test_mock_research_enrichment_creates_report_and_notebooklm_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "agent_quality_loop.m4a"
            source.write_bytes(b"fake audio")
            config = self.make_config(temp_dir)
            result = process_file(source, config, mock=True, mock_duration_seconds=65)

            enrich_result = enrich_learning_research(result.private_output_dir, config, mock=True)

            self.assertTrue(enrich_result["passed"])
            self.assertTrue((result.private_output_dir / "research_enriched_report.md").exists())
            self.assertTrue((result.private_output_dir / "research_enriched_report.html").exists())
            self.assertTrue((result.private_output_dir / "research_sources.json").exists())
            self.assertTrue((result.private_output_dir / "research_enrichment_status.json").exists())
            self.assertTrue((result.private_output_dir / "audio_podcast_script_research_enriched.md").exists())
            self.assertTrue((result.private_output_dir / "notebooklm_package" / "research_enriched_report.md").exists())
            self.assertTrue(
                (result.private_output_dir / "notebooklm_package" / "audio_podcast_script_research_enriched.md").exists()
            )

    def test_public_sanitize_includes_research_report_only_after_passed_enrichment(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "agent_quality_loop.m4a"
            source.write_bytes(b"fake audio")
            config = self.make_config(temp_dir)
            result = process_file(source, config, mock=True, mock_duration_seconds=65)
            enrich_learning_research(result.private_output_dir, config, mock=True)

            public_output = sanitize_package(result.private_output_dir, config.public_review_dir)

            self.assertTrue((public_output / "research_enriched_report.html").exists())
            index_html = (public_output / "index.html").read_text(encoding="utf-8")
            self.assertIn("Research-Enriched Report", index_html)
            self.assertIn("research_enriched_report.html", index_html)


if __name__ == "__main__":
    unittest.main()
