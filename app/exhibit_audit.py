from __future__ import annotations

import json
from pathlib import Path
import re

from .publishing import BLOCKED_EXTS, BLOCKED_PUBLIC_NAMES, DEVELOPMENT_PACKAGE_MARKERS, SYSTEM_METADATA_NAMES


PUBLIC_TEXT_EXTS = {".html", ".md", ".json", ".txt"}
PRIVATE_MARKERS = [
    "C:\\",
    "file:///C:",
    "outputs_private",
    "original_transcript.md",
    "english_transcribed.md",
    "AI Learnings Audio App\\outputs_private",
]


def _issue(severity: str, path: Path, message: str) -> dict:
    return {"severity": severity, "path": str(path), "message": message}


def _text_links(text: str) -> list[str]:
    html_links = re.findall(r"""href=["']([^"']+)["']""", text, flags=re.IGNORECASE)
    md_links = re.findall(r"""\[[^\]]+\]\(([^)]+)\)""", text)
    return html_links + md_links


def _check_link(path: Path, link: str) -> dict | None:
    if not link or link.startswith("#"):
        return None
    lowered = link.lower()
    if lowered.startswith(("http://", "https://", "mailto:")):
        return None
    if "file:///c:" in lowered or "outputs_private" in lowered:
        return _issue("blocker", path, f"Public link exposes local/private target: {link}")
    if path.suffix.lower() == ".html" and lowered.split("#", 1)[0].endswith((".json", ".md")):
        return _issue("warning", path, f"Public HTML links directly to raw machine/readme file: {link}")
    if "://" in lowered:
        return None
    local_target = (path.parent / link).resolve()
    if not local_target.exists():
        return _issue("warning", path, f"Relative link target not found: {link}")
    return None


def _check_text_file(path: Path) -> list[dict]:
    issues: list[dict] = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    for marker in PRIVATE_MARKERS:
        if marker.lower() in text.lower():
            issues.append(_issue("blocker", path, f"Private/public boundary marker found: {marker}"))
    if "Index of " in text:
        issues.append(_issue("warning", path, "Raw directory-index wording found. Use generated index.html instead."))
    for link in _text_links(text):
        link_issue = _check_link(path, link)
        if link_issue:
            issues.append(link_issue)
    if path.name == "quality_score.json":
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            issues.append(_issue("blocker", path, "Invalid quality_score.json"))
        else:
            if not payload.get("passed", False):
                findings = ", ".join(payload.get("transcript_findings", [])) or "quality gate failed"
                issues.append(_issue("warning", path, f"Package is review-safe but not public-exhibit ready: {findings}"))
    return issues


def audit_public_exhibits(public_review_root: Path, mindmap_html: Path | None = None, extra_roots: list[Path] | None = None) -> dict:
    issues: list[dict] = []
    files: list[Path] = []
    roots = [public_review_root, *(extra_roots or [])]
    for root in roots:
        if not root.exists():
            continue
        for package_dir in sorted(path for path in root.iterdir() if path.is_dir()):
            if any(marker in package_dir.name.lower() for marker in DEVELOPMENT_PACKAGE_MARKERS):
                issues.append(
                    _issue(
                        "warning",
                        package_dir,
                        "Development/sample package is present in public review output and should be removed before public sharing.",
                    )
                )
        files.extend(path for path in root.rglob("*") if path.is_file())
    if mindmap_html and mindmap_html.exists():
        files.append(mindmap_html)

    for path in sorted(files):
        lower_name = path.name.lower()
        if lower_name in BLOCKED_PUBLIC_NAMES:
            issues.append(_issue("blocker", path, "Private transcript file must not be in a public exhibit."))
        if lower_name in SYSTEM_METADATA_NAMES:
            issues.append(_issue("warning", path, "System metadata file should be removed before public publishing."))
        if path.suffix.lower() in BLOCKED_EXTS:
            issues.append(_issue("blocker", path, "Raw media file must not be in a public exhibit."))
        if path.suffix.lower() in PUBLIC_TEXT_EXTS:
            issues.extend(_check_text_file(path))

    blocker_count = sum(1 for issue in issues if issue["severity"] == "blocker")
    warning_count = sum(1 for issue in issues if issue["severity"] == "warning")
    return {
        "passed": blocker_count == 0,
        "portfolio_ready": blocker_count == 0 and warning_count == 0,
        "blockers": blocker_count,
        "warnings": warning_count,
        "files_checked": len(files),
        "issues": issues,
    }
