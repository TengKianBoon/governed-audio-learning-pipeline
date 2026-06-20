from __future__ import annotations

import json
from pathlib import Path


def estimate_tokens(text: str) -> int:
    # Practical rough estimate for mixed English/Chinese text without tokenizer dependency.
    ascii_chars = sum(1 for char in text if ord(char) < 128)
    non_ascii_chars = len(text) - ascii_chars
    return max(1, ascii_chars // 4 + non_ascii_chars)


def budget_report(
    *,
    original_text: str,
    english_text: str,
    summary_input_text: str = "",
    summary_text: str = "",
    translation_was_run: bool = False,
    per_task_budget: int,
    warning_ratio: float,
    paid_provider: str = "none",
) -> dict:
    original_tokens = estimate_tokens(original_text)
    english_tokens = estimate_tokens(english_text)
    summary_input_tokens = estimate_tokens(summary_input_text or english_text or original_text)
    summary_tokens = estimate_tokens(summary_text) if summary_text else 0
    translation_billable_tokens = original_tokens + english_tokens if translation_was_run else 0
    summary_billable_tokens = summary_input_tokens + summary_tokens
    total = translation_billable_tokens + summary_billable_tokens
    warning_threshold = int(per_task_budget * warning_ratio)
    return {
        "estimated_original_tokens": original_tokens,
        "estimated_english_tokens": english_tokens,
        "estimated_summary_input_tokens": summary_input_tokens,
        "estimated_summary_tokens": summary_tokens,
        "estimated_translation_billable_tokens": translation_billable_tokens,
        "estimated_summary_billable_tokens": summary_billable_tokens,
        "estimated_total_tokens": total,
        "per_task_budget": per_task_budget,
        "warning_threshold": warning_threshold,
        "budget_status": "warn" if total >= warning_threshold else "ok",
        "paid_provider": paid_provider,
        "cost_policy": (
            "OpenAI quality calls are budgeted per task. Daily route summarizes directly from source text; "
            "full English translation is charged only when explicitly enabled. Stop and review when budget_status is warn."
        ),
    }


def write_budget_report(path: Path, report: dict) -> None:
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
