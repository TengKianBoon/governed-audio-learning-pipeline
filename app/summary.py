from __future__ import annotations

import re


ENTERPRISE_TERMS = [
    "agent",
    "orchestration",
    "workflow",
    "workflows",
    "quality",
    "guardrail",
    "guardrails",
    "mcp",
    "hook",
    "hooks",
    "memory",
    "enterprise",
    "architecture",
    "transcription",
    "transcript",
    "translation",
    "chunk",
    "stitching",
    "mindmap",
    "vendor",
    "provider",
    "privacy",
    "cost",
    "retry",
    "human review",
    "portfolio",
    "notebooklm",
    "research",
    "governance",
]

STOPWORDS = {
    "about",
    "after",
    "again",
    "also",
    "because",
    "before",
    "being",
    "bottom",
    "change",
    "could",
    "every",
    "from",
    "have",
    "into",
    "ideas",
    "learn",
    "like",
    "mock",
    "mode",
    "more",
    "much",
    "need",
    "number",
    "only",
    "other",
    "over",
    "real",
    "some",
    "than",
    "that",
    "their",
    "then",
    "there",
    "these",
    "this",
    "time",
    "tools",
    "want",
    "what",
    "when",
    "where",
    "which",
    "while",
    "whole",
    "with",
    "would",
    "your",
}


def is_meaningful_keyword(word: str) -> bool:
    key = word.strip().lower()
    if not key or key in STOPWORDS:
        return False
    if len(key) < 4:
        return False
    if re.fullmatch(r"[a-z]-[a-z]+", key):
        return False
    if re.search(r"[0-9a-f]{6,}", key):
        return False
    if re.fullmatch(r"\d+", key):
        return False
    return True


def extract_keywords(text: str, limit: int = 12) -> list[str]:
    lowered = text.lower()
    hits = [term for term in ENTERPRISE_TERMS if term in lowered]
    words = re.findall(r"[A-Za-z][A-Za-z0-9-]{3,}", text)
    frequent: dict[str, int] = {}
    for word in words:
        key = word.lower()
        if not is_meaningful_keyword(key):
            continue
        frequent[key] = frequent.get(key, 0) + 1
    ranked = [
        word
        for word, count in sorted(frequent.items(), key=lambda item: (-item[1], item[0]))
        if count > 1 or len(word) >= 7
    ]
    merged: list[str] = []
    for item in hits + ranked:
        if is_meaningful_keyword(item) and item not in merged:
            merged.append(item)
        if len(merged) >= limit:
            break
    return merged


def build_summary_markdown(english_text: str, source_name: str) -> str:
    paragraphs = [p.strip() for p in english_text.splitlines() if p.strip()]
    preview = " ".join(paragraphs)[:900].strip()
    keywords = extract_keywords(english_text)
    keyword_text = ", ".join(keywords) if keywords else "needs review"
    return (
        f"# Learning Summary - {source_name}\n\n"
        f"## Short Summary\n\n{preview or 'Pending transcript content.'}\n\n"
        f"## Keywords\n\n{keyword_text}\n\n"
        "## Public Practice Note\n\n"
        "This summary is safe to review, but public sharing still requires the publishing gate.\n"
    )
