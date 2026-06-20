from __future__ import annotations

import re


CJK_RE = re.compile(r"[\u3400-\u9fff]")
ASCII_LETTER_RE = re.compile(r"[A-Za-z]")


def detect_language(text: str, hinted_language: str | None = None) -> str:
    """Return a coarse language code for routing: en, zh, or unknown."""
    hinted = (hinted_language or "").strip().lower()
    if hinted.startswith("en"):
        return "en"
    if hinted.startswith(("zh", "cmn", "yue")):
        return "zh"

    sample = text.strip()
    if not sample:
        return "unknown"

    cjk_count = len(CJK_RE.findall(sample))
    ascii_letters = len(ASCII_LETTER_RE.findall(sample))
    if cjk_count >= 3 and cjk_count >= ascii_letters * 0.08:
        return "zh"
    if ascii_letters >= max(20, cjk_count * 3):
        return "en"
    if cjk_count:
        return "zh"
    return "unknown"


def is_english_language(language: str | None) -> bool:
    return (language or "").lower().startswith("en")
