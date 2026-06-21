from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

from app.mindmap import apply_delta, render_mindmap_html
from app.summary import extract_keywords


class MindmapFlowTest(unittest.TestCase):
    def test_extract_keywords_filters_low_value_words(self) -> None:
        keywords = extract_keywords("this is from your whole bottom number change agent orchestration quality")
        self.assertIn("agent", keywords)
        self.assertIn("orchestration", keywords)
        self.assertNotIn("this", keywords)
        self.assertNotIn("bottom", keywords)

    def test_render_mindmap_html_uses_flow_layout_and_clickable_links(self) -> None:
        graph = {
            "updated_at": "2026-06-20T00:00:00+00:00",
            "nodes": [
                {
                    "id": "agent",
                    "label": "agent",
                    "private_links": [r"C:\Private\agent"],
                    "public_links": [r"C:\Sandbox\outputs_public_review\agent-package"],
                },
                {"id": "this", "label": "this", "private_links": [], "public_links": []},
            ],
            "edges": [],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "mindmap.html"
            render_mindmap_html(graph, output)
            html = output.read_text(encoding="utf-8")

        self.assertIn("Enterprise AI Solution Architecture &amp; Delivery Framework", html)
        self.assertIn("Application Design", html)
        self.assertIn("Agentic System Improvement", html)
        self.assertIn("Agent Package", html)
        self.assertIn("../outputs_public_review/agent-package/index.html", html)
        self.assertNotIn("Review package 1", html)
        self.assertNotIn("C:\\Private", html)
        self.assertNotIn("Private evidence", html)
        self.assertIn("Filtered weak terms</span><strong>1</strong>", html)

    def test_apply_delta_skips_low_value_concepts(self) -> None:
        graph = {"nodes": [], "edges": [], "updated_at": None}
        updated = apply_delta(
            graph,
            {"concepts": ["agent", "this", "sample-4f34cc3b"]},
            private_link=r"C:\Private\agent",
        )
        labels = {node["label"] for node in updated["nodes"]}
        self.assertEqual(labels, {"agent"})

    def test_render_mindmap_html_hides_sample_package_links(self) -> None:
        graph = {
            "updated_at": "2026-06-20T00:00:00+00:00",
            "nodes": [
                {
                    "id": "agent",
                    "label": "agent",
                    "private_links": [r"C:\Private\sample", r"C:\Private\real"],
                    "public_links": [
                        r"C:\Sandbox\outputs_public_review\20260619-sample-4f34cc3b",
                        r"C:\Sandbox\outputs_public_review\20260619-voice-real-learning",
                    ],
                },
            ],
            "edges": [],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "mindmap" / "enterprise_ai_mindmap.html"
            render_mindmap_html(graph, output)
            html = output.read_text(encoding="utf-8")

        self.assertNotIn("20260619-sample-4f34cc3b", html)
        self.assertIn("20260619-voice-real-learning", html)
        self.assertIn("2026-06-19 - Voice Real Learning", html)

    def test_render_mindmap_html_labels_public_links_newest_first(self) -> None:
        graph = {
            "updated_at": "2026-06-20T00:00:00+00:00",
            "nodes": [
                {
                    "id": "quality",
                    "label": "quality",
                    "private_links": [r"C:\Private\older", r"C:\Private\newer"],
                    "public_links": [
                        r"C:\Sandbox\outputs_public_review\20260619-voice-first-run-f9683fe1",
                        r"C:\Sandbox\outputs_public_review\20260620-voice-improved-summary-ee977839",
                    ],
                },
            ],
            "edges": [],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "mindmap" / "enterprise_ai_mindmap.html"
            render_mindmap_html(graph, output)
            html = output.read_text(encoding="utf-8")

        latest = "Latest reviewed package: 2026-06-20 - Voice Improved Summary"
        earlier = "Earlier evidence: 2026-06-19 - Voice First Run"
        self.assertIn(latest, html)
        self.assertIn(earlier, html)
        self.assertLess(html.index(latest), html.index(earlier))

    def test_render_mindmap_html_hides_failed_quality_public_packages(self) -> None:
        graph = {
            "updated_at": "2026-06-20T00:00:00+00:00",
            "nodes": [
                {
                    "id": "quality",
                    "label": "quality",
                    "private_links": [r"C:\Private\older", r"C:\Private\newer"],
                    "public_links": [
                        r"C:\Sandbox\outputs_public_review\20260619-voice-failed-f9683fe1",
                        r"C:\Sandbox\outputs_public_review\20260620-voice-passed-ee977839",
                    ],
                },
            ],
            "edges": [],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "mindmap" / "enterprise_ai_mindmap.html"
            failed_dir = Path(temp_dir) / "outputs_public_review" / "20260619-voice-failed-f9683fe1"
            passed_dir = Path(temp_dir) / "outputs_public_review" / "20260620-voice-passed-ee977839"
            failed_dir.mkdir(parents=True)
            passed_dir.mkdir(parents=True)
            (failed_dir / "quality_score.json").write_text(json.dumps({"passed": False}), encoding="utf-8")
            (passed_dir / "quality_score.json").write_text(json.dumps({"passed": True}), encoding="utf-8")

            render_mindmap_html(graph, output)
            html = output.read_text(encoding="utf-8")

        self.assertNotIn("20260619-voice-failed-f9683fe1", html)
        self.assertIn("20260620-voice-passed-ee977839", html)


if __name__ == "__main__":
    unittest.main()
