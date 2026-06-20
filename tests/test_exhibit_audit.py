from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from app.exhibit_audit import audit_public_exhibits


class ExhibitAuditTest(unittest.TestCase):
    def test_blocks_private_paths_in_public_html(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "public"
            root.mkdir()
            package = root / "package"
            package.mkdir()
            (package / "index.html").write_text(
                '<a href="file:///C:/Private/outputs_private/package">bad</a>',
                encoding="utf-8",
            )

            result = audit_public_exhibits(root)

        self.assertFalse(result["passed"])
        self.assertGreaterEqual(result["blockers"], 1)

    def test_warns_when_quality_gate_is_review_safe_but_not_portfolio_ready(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "public"
            package = root / "package"
            package.mkdir(parents=True)
            (package / "quality_score.json").write_text(
                json.dumps(
                    {
                        "passed": False,
                        "score": 80,
                        "transcript_findings": ["english_translation_contains_cjk_characters"],
                    }
                ),
                encoding="utf-8",
            )

            result = audit_public_exhibits(root)

        self.assertTrue(result["passed"])
        self.assertFalse(result["portfolio_ready"])
        self.assertEqual(result["warnings"], 1)

    def test_warns_when_development_sample_package_is_public(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "public"
            package = root / "20260619-sample-4f34cc3b"
            package.mkdir(parents=True)
            (package / "index.html").write_text("sample", encoding="utf-8")

            result = audit_public_exhibits(root)

        self.assertTrue(result["passed"])
        self.assertFalse(result["portfolio_ready"])
        self.assertEqual(result["warnings"], 1)

    def test_warns_when_public_html_links_to_raw_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "public"
            package = root / "package"
            package.mkdir(parents=True)
            (package / "index.html").write_text('<a href="mindmap_delta.json">Delta</a>', encoding="utf-8")
            (package / "mindmap_delta.json").write_text("{}", encoding="utf-8")

            result = audit_public_exhibits(root)

        self.assertTrue(result["passed"])
        self.assertFalse(result["portfolio_ready"])
        self.assertEqual(result["warnings"], 1)


if __name__ == "__main__":
    unittest.main()
