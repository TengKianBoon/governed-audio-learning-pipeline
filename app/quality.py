from __future__ import annotations

import json
from pathlib import Path
import re


PRIVATE_PATTERNS = [
    "api_key",
    "api key",
    "secret_key",
    "secret key",
    "secret",
    "password",
    "-----BEGIN",
    "C:\\\\",
    "C:/",
]

PRIVATE_REGEX_PATTERNS = [
    r"\bsk-[A-Za-z0-9_-]{20,}\b",
    r"\bBearer\s+[A-Za-z0-9._-]{20,}\b",
    r"\b(?:OPENAI_API_KEY|ANTHROPIC_API_KEY|GOOGLE_API_KEY)\s*[:=]\s*\S+",
    r"\b(?:api[_ -]?key|secret[_ -]?key|password)\s*[:=]\s*\S+",
]

MOJIBAKE_PATTERNS = [
    "ä¸",
    "äº",
    "åœ",
    "è¿",
    "çš",
    "æˆ",
    "å",
    "ã",
    "Ð½",
]


MOJIBAKE_PATTERNS.extend(
    [
        "å»",
        "è¿",
        "ä¿",
        "ä¸",
        "å¾",
        "å",
        "è‡",
        "æˆ",
        "ã",
        "ã‚",
        "ì",
        "Ð½",
        "Ñ‹",
        "Â»",
    ]
)


REQUIRED_SUMMARY_SECTIONS = [
    "Executive Learning",
    "Plain-English Explanation",
    "Enterprise AI Architecture and Delivery Relevance",
    "Key Concepts and Definitions",
    "Practical Scenarios",
    "Why It Matters",
    "Implementation Implications",
    "Risks, Quality Gates, and Human Review",
    "Follow-Up Research Questions",
    "Mindmap Ingest Suggestion",
    "Public Practice Note",
]

SUMMARY_SECTION_ALIASES = {
    "Enterprise AI Architecture and Delivery Relevance": ["Enterprise AI / FDE Relevance"],
    "Public Practice Note": ["Portfolio Note"],
}


def scan_text_for_private_patterns(text: str) -> list[str]:
    lowered = text.lower()
    findings = []
    for pattern in PRIVATE_PATTERNS:
        if pattern == "secret":
            # Security writing often says "secrets" generically. Only flag a likely value-bearing secret.
            continue
        needle = pattern.lower()
        if needle in lowered:
            findings.append(pattern)
    for pattern in PRIVATE_REGEX_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            findings.append(pattern)
    return findings


def transcript_quality_findings(text: str) -> list[str]:
    findings: list[str] = []
    if len(text.strip()) < 100:
        findings.append("transcript_too_short")
    for pattern in MOJIBAKE_PATTERNS:
        if pattern in text:
            findings.append("possible_mojibake_or_encoding_artifact")
            break
    ascii_letters = len(re.findall(r"[A-Za-z]", text))
    non_ascii = sum(1 for char in text if ord(char) > 127)
    if ascii_letters > 0 and non_ascii > ascii_letters * 0.15:
        findings.append("english_translation_contains_many_non_english_symbols")
    cjk_chars = len(re.findall(r"[\u3400-\u9fff]", text))
    if cjk_chars >= 3:
        findings.append("english_translation_contains_cjk_characters")
    return sorted(set(findings))


def _word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)?|[\u3400-\u9fff]", text))


def _section_names(section: str) -> list[str]:
    return [section, *SUMMARY_SECTION_ALIASES.get(section, [])]


def _section_text(text: str, section: str) -> str:
    for section_name in _section_names(section):
        pattern = rf"(?ims)^##\s+{re.escape(section_name)}\s*$\n(?P<body>.*?)(?=^##\s+|\Z)"
        match = re.search(pattern, text)
        if match:
            return match.group("body").strip()
    return ""


def _has_section(text: str, section: str) -> bool:
    return any(re.search(rf"(?im)^##\s+{re.escape(section_name)}\s*$", text) for section_name in _section_names(section))


def summary_quality_findings(summary_text: str, source_text: str = "") -> list[str]:
    findings: list[str] = []
    stripped = summary_text.strip()
    if len(stripped) < 200:
        findings.append("summary_too_short")

    source_is_substantial = len(source_text.strip()) >= 2000
    if not source_is_substantial:
        return sorted(set(findings))

    for section in REQUIRED_SUMMARY_SECTIONS:
        if not _has_section(summary_text, section):
            findings.append(f"missing_summary_section:{section}")

    if not _has_section(summary_text, "Public Practice Note"):
        findings.append("summary_appears_truncated_missing_public_practice_note")

    if _word_count(summary_text) < 1800:
        findings.append("summary_too_brief_for_substantial_source")

    table_rows = len(re.findall(r"(?m)^\|.*\|\s*$", summary_text))
    if table_rows < 8:
        findings.append("summary_missing_deep_concept_table")

    scenario_headings = len(re.findall(r"(?im)^###\s+Scenario\s+\d+", summary_text))
    if scenario_headings < 4:
        findings.append("summary_missing_scenario_subsections")

    why_body = _section_text(summary_text, "Why It Matters")
    why_points = len(re.findall(r"(?m)^\s*\d+\.\s+", why_body))
    if why_points < 6:
        findings.append("summary_why_it_matters_too_thin")

    follow_up_body = _section_text(summary_text, "Follow-Up Research Questions")
    follow_up_questions = len(re.findall(r"(?m)^\s*(?:\d+\.|-)\s+.*\?", follow_up_body))
    if follow_up_questions < 6:
        findings.append("summary_follow_up_questions_too_thin")

    mindmap_body = _section_text(summary_text, "Mindmap Ingest Suggestion")
    if not mindmap_body:
        findings.append("summary_missing_mindmap_ingest_suggestion")
    else:
        lowered_mindmap = mindmap_body.lower()
        for cue in ("category", "fits", "before", "after"):
            if cue not in lowered_mindmap:
                findings.append(f"mindmap_ingest_missing_{cue}_cue")
        if len(mindmap_body.splitlines()) > 4:
            findings.append("mindmap_ingest_not_concise")

    cjk_chars = len(re.findall(r"[\u3400-\u9fff]", summary_text))
    if cjk_chars >= 3:
        findings.append("summary_contains_cjk_characters")

    return sorted(set(findings))


def score_private_learning_package(package_dir: Path) -> dict:
    checks = {
        "source_metadata": (package_dir / "source_metadata.json").exists(),
        "original_transcript": (package_dir / "original_transcript.md").exists(),
        "english_transcript": (package_dir / "english_transcribed.md").exists(),
        "summary": (package_dir / "summary.md").exists(),
        "mindmap_ingest": (package_dir / "mindmap_ingest.md").exists(),
        "mindmap_delta": (package_dir / "mindmap_delta.json").exists(),
        "cost_budget": (package_dir / "cost_budget.json").exists(),
    }
    score = 0
    score += 15 if checks["source_metadata"] else 0
    score += 20 if checks["original_transcript"] else 0
    score += 25 if checks["english_transcript"] else 0
    score += 15 if checks["summary"] else 0
    score += 10 if checks["mindmap_delta"] else 0
    score += 5 if checks["cost_budget"] else 0

    privacy_findings: list[str] = []
    for name in ("summary.md", "mindmap_ingest.md", "mindmap_delta.json"):
        path = package_dir / name
        if path.exists():
            privacy_findings.extend(scan_text_for_private_patterns(path.read_text(encoding="utf-8")))
    privacy_clear = not privacy_findings
    score += 10 if privacy_clear else 0

    transcript_findings: list[str] = []
    english_path = package_dir / "english_transcribed.md"
    if english_path.exists():
        transcript_findings = transcript_quality_findings(english_path.read_text(encoding="utf-8"))
    transcript_quality_clear = not transcript_findings
    if not transcript_quality_clear:
        score = max(0, score - 20)

    summary_findings: list[str] = []
    summary_path = package_dir / "summary.md"
    original_path = package_dir / "original_transcript.md"
    if summary_path.exists():
        source_text = original_path.read_text(encoding="utf-8", errors="ignore") if original_path.exists() else ""
        summary_findings = summary_quality_findings(summary_path.read_text(encoding="utf-8"), source_text)
    summary_quality_clear = not summary_findings
    if not summary_quality_clear:
        score = max(0, score - 20)

    return {
        "score": score,
        "passed": score >= 80 and transcript_quality_clear and summary_quality_clear,
        "checks": checks,
        "privacy_clear": privacy_clear,
        "privacy_findings": sorted(set(privacy_findings)),
        "transcript_quality_clear": transcript_quality_clear,
        "transcript_findings": transcript_findings,
        "summary_quality_clear": summary_quality_clear,
        "summary_findings": summary_findings,
    }


def write_quality_score(package_dir: Path) -> dict:
    result = score_private_learning_package(package_dir)
    (package_dir / "quality_score.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
