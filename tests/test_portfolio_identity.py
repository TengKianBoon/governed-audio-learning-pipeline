from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from app.mindmap import render_mindmap_html
from app.publishing import build_public_note


class PortfolioIdentityTest(unittest.TestCase):
    def test_mindmap_html_centers_tkb_as_builder(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "mindmap.html"
            render_mindmap_html({"nodes": [], "edges": [], "updated_at": None}, output)
            html = output.read_text(encoding="utf-8")
            self.assertIn("Built by Teng Kian Boon", html)
            self.assertIn("TKB Enterprise AI Architecture &amp; Delivery Framework", html)
            self.assertIn("AI tools assist synthesis and formatting", html)

    def test_public_note_centers_tkb_and_operator_review_without_hiring_language(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            package = Path(temp_dir) / "package"
            package.mkdir()
            (package / "summary.md").write_text("# Summary\n\nLearning content.", encoding="utf-8")
            note = build_public_note(package)
            self.assertIn("Built and reviewed by Teng Kian Boon", note)
            self.assertIn("Enterprise AI solution architecture and delivery framework", note)
            self.assertIn("operator-reviewed", note)
            self.assertNotIn("hiring", note.lower())
            self.assertNotIn("FDE", note)


if __name__ == "__main__":
    unittest.main()
