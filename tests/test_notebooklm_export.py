from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from app.config import load_config
from app.notebooklm_export import export_notebooklm_sources


class NotebookLMExportTest(unittest.TestCase):
    def make_config(self, temp_dir: str):
        config_path = Path(temp_dir) / "paths.test.yaml"
        config_path.write_text(
            "\n".join(
                [
                    f'sandbox_root: "{Path(temp_dir) / "sandbox"}"',
                    f'portfolio_public_root: "{Path(temp_dir) / "portfolio_public"}"',
                    f'notebooklm_artifacts_root: "{Path(temp_dir) / "notebooklm_artifacts"}"',
                ]
            ),
            encoding="utf-8",
        )
        return load_config(config_path)

    def test_export_notebooklm_sources_copies_requested_private_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            package = Path(temp_dir) / "outputs_private" / "learnings" / "20260620-test-learning"
            package.mkdir(parents=True)
            (package / "original_transcript.md").write_text("# Original\n\nRaw source.", encoding="utf-8")
            (package / "summary.md").write_text("# Summary\n\nReviewed learning.", encoding="utf-8")
            (package / "summary.html").write_text("<html><body>Reviewed learning.</body></html>", encoding="utf-8")
            config = self.make_config(temp_dir)

            result = export_notebooklm_sources(package, config)
            export_dir = Path(result["notebooklm_export_dir"])

            self.assertEqual(export_dir.name, "20260620-test-learning NLM")
            self.assertTrue((export_dir / "original_transcript.md").exists())
            self.assertTrue((export_dir / "summary.md").exists())
            self.assertTrue((export_dir / "summary.html").exists())
            self.assertTrue((export_dir / "README_for_NotebookLM.md").exists())


if __name__ == "__main__":
    unittest.main()
