from __future__ import annotations

import sys
import unittest

from app.cost_guard import budget_report, estimate_tokens
from app.resilience import RetryExhausted, RetryPolicy, run_command_with_retries


class ResilienceCostTest(unittest.TestCase):
    def test_retry_cap_exhausts(self) -> None:
        with self.assertRaises(RetryExhausted) as ctx:
            run_command_with_retries(
                [sys.executable, "-c", "import sys; sys.exit(7)"],
                policy=RetryPolicy(max_retries=2, backoff_seconds=0),
                failure_label="intentional failure",
            )
        self.assertIn("after 2 attempt", str(ctx.exception))

    def test_token_budget_warns_near_limit(self) -> None:
        text = "enterprise AI " * 200
        report = budget_report(
            original_text=text,
            english_text=text,
            summary_input_text=text,
            per_task_budget=max(1, estimate_tokens(text)),
            warning_ratio=0.5,
        )
        self.assertEqual(report["budget_status"], "warn")

    def test_direct_summary_route_skips_translation_billable_tokens(self) -> None:
        original = "企业人工智能 " * 100
        summary = "Enterprise AI summary " * 100
        report = budget_report(
            original_text=original,
            english_text="Full English transcript intentionally skipped.",
            summary_input_text=original,
            summary_text=summary,
            translation_was_run=False,
            per_task_budget=100000,
            warning_ratio=0.8,
        )
        self.assertEqual(report["estimated_translation_billable_tokens"], 0)
        self.assertGreater(report["estimated_summary_billable_tokens"], 0)

    def test_full_translation_route_counts_translation_billable_tokens(self) -> None:
        text = "enterprise AI " * 100
        report = budget_report(
            original_text=text,
            english_text=text,
            summary_input_text=text,
            summary_text=text,
            translation_was_run=True,
            per_task_budget=100000,
            warning_ratio=0.8,
        )
        self.assertGreater(report["estimated_translation_billable_tokens"], 0)


if __name__ == "__main__":
    unittest.main()
