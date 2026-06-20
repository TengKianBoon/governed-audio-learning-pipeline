from __future__ import annotations

import unittest

from app.quality import scan_text_for_private_patterns, summary_quality_findings, transcript_quality_findings


class QualityHeuristicsTest(unittest.TestCase):
    def test_flags_mojibake_in_english_translation(self) -> None:
        findings = transcript_quality_findings("This answer contains ä¸ and åœ artifacts from encoding.")
        self.assertIn("possible_mojibake_or_encoding_artifact", findings)

    def test_flags_common_whisper_translation_artifacts(self) -> None:
        findings = transcript_quality_findings(
            "The trace was replaced by a return test å»¶è¿Ÿ Token script and then Ð½Ñ‹ repeated."
        )
        self.assertIn("possible_mojibake_or_encoding_artifact", findings)

    def test_flags_cjk_characters_in_english_translation(self) -> None:
        findings = transcript_quality_findings(
            "This English transcript still contains 延迟 保證 復发 and needs review."
        )
        self.assertIn("english_translation_contains_cjk_characters", findings)

    def test_accepts_simple_english_transcript(self) -> None:
        findings = transcript_quality_findings(
            "This is a clear English transcript about agent quality gates, regression tests, and operational learning loops."
        )
        self.assertEqual(findings, [])

    def test_allows_generic_security_word_secrets(self) -> None:
        findings = scan_text_for_private_patterns(
            "The agent should not reveal secrets, customer data, or protected records."
        )
        self.assertEqual(findings, [])

    def test_blocks_secret_like_values(self) -> None:
        findings = scan_text_for_private_patterns("OPENAI_API_KEY=" + "sk" + "-abcdefghijklmnopqrstuvwxyz123456")
        self.assertTrue(findings)

    def test_flags_thin_summary_for_substantial_source(self) -> None:
        source = "enterprise AI source transcript " * 120
        summary = """# Learning Summary - source.txt

## Executive Learning
Short.

## Public Practice Note
Too thin.
"""
        findings = summary_quality_findings(summary, source)
        self.assertIn("summary_too_brief_for_substantial_source", findings)
        self.assertIn("summary_missing_deep_concept_table", findings)
        self.assertIn("summary_missing_mindmap_ingest_suggestion", findings)

    def test_flags_mindmap_ingest_without_before_after_cues(self) -> None:
        source = "enterprise AI source transcript " * 120
        summary = "\n\n".join(
            [
                "# Learning Summary - source.txt",
                "## Executive Learning\n" + "\n".join(f"- Specific point {i}" for i in range(1, 8)),
                "## Plain-English Explanation\n### Problem\n" + ("Detailed explanation. " * 80),
                "## Enterprise AI Architecture and Delivery Relevance\n" + ("Enterprise relevance. " * 80),
                "## Key Concepts and Definitions\n| Term | Plain-English Meaning | Why It Matters |\n|---|---|---|\n"
                + "\n".join(f"| Term {i} | Meaning {i} | Matters {i} |" for i in range(1, 13)),
                "## Practical Scenarios\n"
                + "\n".join(
                    f"### Scenario {i} - Example\nSituation, application, and business value."
                    for i in range(1, 5)
                ),
                "## Why It Matters\n" + "\n".join(f"{i}. Detailed rationale." for i in range(1, 9)),
                "## Implementation Implications\n" + ("Implementation detail. " * 80),
                "## Risks, Quality Gates, and Human Review\n" + ("Risk and gate detail. " * 80),
                "## Follow-Up Research Questions\n" + "\n".join(f"{i}. What should be validated next?" for i in range(1, 7)),
                "## Mindmap Ingest Suggestion\n- Put this into the flow map near agent operations.",
                "## Public Practice Note\n" + ("Public practice relevance. " * 120),
            ]
        )
        findings = summary_quality_findings(summary, source)
        self.assertIn("mindmap_ingest_missing_category_cue", findings)
        self.assertIn("mindmap_ingest_missing_before_cue", findings)
        self.assertIn("mindmap_ingest_missing_after_cue", findings)

    def test_accepts_previous_public_summary_section_names_during_transition(self) -> None:
        source = "enterprise AI source transcript " * 120
        summary = "\n\n".join(
            [
                "# Learning Summary - source.txt",
                "## Executive Learning\n" + "\n".join(f"- Specific point {i}" for i in range(1, 8)),
                "## Plain-English Explanation\n### Problem\n" + ("Detailed explanation. " * 80),
                "## Enterprise AI / FDE Relevance\n" + ("Enterprise relevance. " * 80),
                "## Key Concepts and Definitions\n| Term | Plain-English Meaning | Why It Matters |\n|---|---|---|\n"
                + "\n".join(f"| Term {i} | Meaning {i} | Matters {i} |" for i in range(1, 13)),
                "## Practical Scenarios\n"
                + "\n".join(
                    f"### Scenario {i} - Example\nSituation, application, and business value."
                    for i in range(1, 5)
                ),
                "## Why It Matters\n" + "\n".join(f"{i}. Detailed rationale." for i in range(1, 9)),
                "## Implementation Implications\n" + ("Implementation detail. " * 80),
                "## Risks, Quality Gates, and Human Review\n" + ("Risk and gate detail. " * 80),
                "## Follow-Up Research Questions\n" + "\n".join(f"{i}. What should be validated next?" for i in range(1, 7)),
                "## Mindmap Ingest Suggestion\n- Category: Orchestrate/Govern; Fits after incident capture; Before regression publishing; After trace review.",
                "## Portfolio Note\n" + ("Public practice relevance. " * 120),
            ]
        )
        findings = summary_quality_findings(summary, source)
        self.assertNotIn("missing_summary_section:Enterprise AI Architecture and Delivery Relevance", findings)
        self.assertNotIn("missing_summary_section:Public Practice Note", findings)
        self.assertNotIn("summary_appears_truncated_missing_public_practice_note", findings)


if __name__ == "__main__":
    unittest.main()
