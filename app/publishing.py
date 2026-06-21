from __future__ import annotations

import json
import html
from pathlib import Path
import re
import shutil

from .quality import scan_text_for_private_patterns, write_quality_score
from .utils import write_text


BLOCKED_PUBLIC_NAMES = {
    "original_transcript.md",
    "english_transcribed.md",
}

SYSTEM_METADATA_NAMES = {
    "desktop.ini",
    "thumbs.db",
    ".ds_store",
}

MANAGED_PUBLIC_FILES = {
    "summary.md",
    "summary.html",
    "mindmap_ingest.md",
    "quality_score.json",
    "mindmap_delta.json",
    "source_metadata_public.json",
    "public_learning_note.md",
    "index.html",
    "public_learning_note.html",
    "mindmap_ingest.html",
    "quality_gate.html",
    "source_metadata.html",
    "research_enriched_report.md",
    "research_enriched_report.html",
    "research_sources.json",
    "research_enrichment_status.json",
}

BLOCKED_EXTS = {".m4a", ".mp3", ".aac", ".wav", ".flac", ".amr", ".3gp", ".ogg", ".opus", ".mp4", ".mkv", ".webm", ".mov"}
TEXT_SCAN_EXTS = {".md", ".json", ".txt", ".html"}
DEVELOPMENT_PACKAGE_MARKERS = {"sample", "fixture", "mock"}


class PublishingGateError(RuntimeError):
    pass


def assert_public_safe(package_dir: Path) -> None:
    for path in package_dir.rglob("*"):
        if path.is_dir():
            continue
        if path.name.lower() in BLOCKED_PUBLIC_NAMES:
            raise PublishingGateError(f"Blocked private file: {path.name}")
        if path.name.lower() in SYSTEM_METADATA_NAMES:
            continue
        if path.suffix.lower() in BLOCKED_EXTS:
            raise PublishingGateError(f"Blocked raw media file: {path.name}")
        if path.suffix.lower() in TEXT_SCAN_EXTS:
            findings = scan_text_for_private_patterns(path.read_text(encoding="utf-8", errors="ignore"))
            if findings:
                raise PublishingGateError(f"Blocked private pattern(s) in {path.name}: {', '.join(findings)}")


def _load_quality(private_package_dir: Path) -> dict:
    quality_path = private_package_dir / "quality_score.json"
    if quality_path.exists():
        return json.loads(quality_path.read_text(encoding="utf-8"))
    return write_quality_score(private_package_dir)


def _release_status(quality: dict) -> str:
    if not quality.get("passed"):
        findings_list = list(quality.get("transcript_findings", [])) + list(quality.get("summary_findings", []))
        findings = ", ".join(str(finding) for finding in findings_list) or "quality gate not passed"
        return f"Review draft: not public-exhibit ready yet. Reason: {findings}."
    return "Review draft: sanitized and complete, but still requires operator approval before public release."


def _topic_title(private_package_dir: Path) -> str:
    metadata_path = private_package_dir / "source_metadata.json"
    raw_name = private_package_dir.name
    if metadata_path.exists():
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            raw_name = str(metadata.get("source_filename") or raw_name)
        except json.JSONDecodeError:
            pass
    stem = Path(raw_name).stem
    cleaned = re.sub(r"[_-]+", " ", stem)
    cleaned = re.sub(r"\bvoice\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b\d{6,8}\b", "", cleaned)
    cleaned = re.sub(r"\b\d{4,6}\b", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned.title() if cleaned else "Learning Topic Under Review"


def _quality_findings_text(quality: dict) -> str:
    findings = list(quality.get("transcript_findings", [])) + list(quality.get("summary_findings", []))
    return ", ".join(str(finding) for finding in findings) or "quality gate not passed"


def _public_tone_cleanup(markdown: str) -> str:
    replacements = {
        "Enterprise AI / FDE Relevance": "Enterprise AI Architecture and Delivery Relevance",
        "Field Deployment Engineer (FDE)": "deployment engineer",
        "Field Deployment Engineer": "deployment engineer",
        "FDE work": "deployment engineering work",
        "FDEs": "deployment engineers",
        "FDE": "deployment engineering",
        "hiring reviewers care about": "enterprise AI architecture and delivery practice depends on",
        "hiring reviewers": "technical readers",
        "HR": "people operations",
        "recruiters": "technical readers",
        "recruiter": "technical reader",
        "employment": "professional practice",
        "job application": "public technical exhibit",
        "Portfolio Note": "Public Practice Note",
        "portfolio-ready": "public-exhibit ready",
        "final portfolio story": "final public learning narrative",
        "Enterprise AI learning portfolio": "Enterprise AI solution architecture and delivery framework",
        "practical FDE thinking": "practical deployment thinking",
    }
    cleaned = markdown
    for before, after in replacements.items():
        cleaned = cleaned.replace(before, after)
    return cleaned


def build_review_summary(private_package_dir: Path, quality: dict) -> str:
    approved_path = private_package_dir / "public_summary.md"
    if approved_path.exists():
        approved_summary = approved_path.read_text(encoding="utf-8")
        return (
            "# Human-Approved Public Summary\n\n"
            "Status: approved public-facing summary prepared after human review.\n\n"
            f"{approved_summary}\n"
        )
    if not quality.get("passed"):
        topic = _topic_title(private_package_dir)
        findings = _quality_findings_text(quality)
        return (
            "# Review Holding Page\n\n"
            f"## Topic Under Review\n\n{topic}\n\n"
            "## Public Summary Status\n\n"
            "A public summary has not been released yet because the transcript quality gate did not pass. "
            "The rough machine transcript and draft summary are intentionally withheld from this public-facing page.\n\n"
            f"## Quality Finding\n\n{findings}\n\n"
            "## Next Operator Actions\n\n"
            "- Re-run transcription and translation with improved language/model settings.\n"
            "- Compare the English version against the original-language transcript.\n"
            "- Write a human-approved `public_summary.md` before presenting this as public-exhibit ready work.\n"
        )
    summary_path = private_package_dir / "summary.md"
    summary = summary_path.read_text(encoding="utf-8") if summary_path.exists() else "Summary pending."
    summary = _public_tone_cleanup(summary)
    return (
        "# Draft Review Summary\n\n"
        f"Status: {_release_status(quality)}\n\n"
        "This file is safe to inspect, but it is not the final public learning narrative. "
        "Use it to decide whether the transcript should be rewritten into a polished technical learning note.\n\n"
        "## Machine-Assisted Draft\n\n"
        f"{summary}\n"
    )


def build_public_note(private_package_dir: Path, owner_name: str = "Teng Kian Boon", quality: dict | None = None) -> str:
    quality = quality or _load_quality(private_package_dir)
    reviewed_summary = build_review_summary(private_package_dir, quality)
    return (
        "# Public Learning Note\n\n"
        f"Built and reviewed by {owner_name} as part of an Enterprise AI solution architecture and delivery framework. "
        "AI tools assist transcription and structuring; the technical synthesis and public release remain operator-reviewed.\n\n"
        f"## Release Status\n\n{_release_status(quality)}\n\n"
        f"{reviewed_summary}\n\n"
        "## Publishing Status\n\nOperator review required before committing this package publicly.\n"
    )


def _page_shell(title: str, eyebrow: str, body_html: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    body {{ margin: 0; font-family: Arial, Helvetica, sans-serif; color: #17202a; background: #f7f5ef; }}
    main {{ max-width: 920px; margin: 0 auto; padding: 32px 20px 48px; }}
    header {{ border-bottom: 2px solid #17202a; padding-bottom: 16px; margin-bottom: 20px; }}
    .eyebrow {{ color: #0f766e; font-weight: 700; text-transform: uppercase; }}
    h1 {{ margin: 8px 0; font-size: 40px; line-height: 1.08; letter-spacing: 0; }}
    h2 {{ margin-top: 26px; }}
    p, li {{ line-height: 1.58; }}
    a {{ color: #1d4ed8; }}
    .back {{ display: inline-block; margin-bottom: 16px; text-decoration: none; }}
    .panel {{ background: #fff; border: 1px solid #d9e0e8; border-radius: 8px; padding: 18px; margin: 16px 0; }}
    .warn {{ border-left: 6px solid #be123c; }}
    .pass {{ border-left: 6px solid #0f766e; }}
    .muted {{ color: #5f6b7a; }}
    code {{ background: #eef2f6; padding: 2px 5px; border-radius: 4px; }}
  </style>
</head>
<body>
<main>
  <a class="back" href="index.html">Back to package overview</a>
  <header>
    <div class="eyebrow">{html.escape(eyebrow)}</div>
    <h1>{html.escape(title)}</h1>
  </header>
  {body_html}
</main>
</body>
</html>
"""


def _markdown_to_html(markdown: str) -> str:
    blocks: list[str] = []
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            blocks.append(f"<p>{html.escape(' '.join(paragraph))}</p>")
            paragraph.clear()

    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            flush_paragraph()
            continue
        if line.startswith("#"):
            flush_paragraph()
            level = min(len(line) - len(line.lstrip("#")), 3)
            text = line[level:].strip()
            blocks.append(f"<h{level}>{html.escape(text)}</h{level}>")
        elif line.startswith("- "):
            flush_paragraph()
            blocks.append(f"<p>- {html.escape(line[2:].strip())}</p>")
        else:
            paragraph.append(line)
    flush_paragraph()
    return "\n".join(blocks)


def build_public_note_html(private_package_dir: Path, owner_name: str, quality: dict) -> str:
    note = build_public_note(private_package_dir, owner_name=owner_name, quality=quality)
    return _page_shell(
        "Public Learning Note",
        "Human-readable exhibit layer",
        _markdown_to_html(note),
    )


def build_summary_review_html(private_package_dir: Path, quality: dict) -> str:
    summary = build_review_summary(private_package_dir, quality)
    body = (
        '<section class="panel">'
        "<p>This is the sanitized HTML reading layer for the learning summary. "
        "It is generated from the public-review summary, not from raw audio or full private transcripts.</p>"
        f"{_markdown_to_html(summary)}"
        "</section>"
    )
    return _page_shell("Learning Summary", "Sanitized summary layer", body)


def build_mindmap_ingest_html(private_package_dir: Path) -> str:
    ingest_path = private_package_dir / "mindmap_ingest.md"
    ingest = ingest_path.read_text(encoding="utf-8") if ingest_path.exists() else "Mindmap placement suggestion pending."
    body = (
        '<section class="panel">'
        "<p>This page explains how the learning is intended to fit into the Enterprise AI solution architecture and delivery framework map. "
        "The map update itself remains a zero-cost local step based on the reviewed summary, not the raw transcript.</p>"
        f"{_markdown_to_html(ingest)}"
        "</section>"
    )
    return _page_shell("Framework Placement", "Solution framework placement layer", body)


def build_quality_gate_html(quality: dict) -> str:
    status_class = "pass" if quality.get("passed") else "warn"
    findings = quality.get("transcript_findings", [])
    summary_findings = quality.get("summary_findings", [])
    finding_items = "".join(f"<li>{html.escape(str(finding))}</li>" for finding in findings) or "<li>No transcript findings recorded.</li>"
    summary_finding_items = (
        "".join(f"<li>{html.escape(str(finding))}</li>" for finding in summary_findings)
        or "<li>No summary findings recorded.</li>"
    )
    checks = quality.get("checks", {})
    check_items = "".join(
        f"<li>{html.escape(str(name))}: {html.escape(str(value))}</li>"
        for name, value in sorted(checks.items())
    )
    body = f"""
  <section class="panel {status_class}">
    <p><strong>Quality score:</strong> {html.escape(str(quality.get('score', 'unknown')))}</p>
    <p><strong>Passed:</strong> {html.escape(str(quality.get('passed', False)))}</p>
    <p><strong>Release meaning:</strong> {_release_status(quality)}</p>
  </section>
  <section class="panel">
    <h2>Transcript Findings</h2>
    <ul>{finding_items}</ul>
  </section>
  <section class="panel">
    <h2>Summary Findings</h2>
    <ul>{summary_finding_items}</ul>
  </section>
  <section class="panel">
    <h2>Completeness Checks</h2>
    <ul>{check_items}</ul>
  </section>
  <p class="muted">Machine-readable quality data is retained for automation, but this page is the intended public review layer.</p>
"""
    return _page_shell("Quality Gate", "Portfolio readiness check", body)


def build_source_metadata_html(public_metadata: dict) -> str:
    rows = "".join(
        f"<li><strong>{html.escape(str(key))}:</strong> {html.escape(str(value))}</li>"
        for key, value in sorted(public_metadata.items())
    )
    body = f"""
  <section class="panel">
    <p>This source context is sanitized. Raw audio, full transcripts, local paths, and fingerprints are withheld from the public package.</p>
    <ul>{rows}</ul>
  </section>
"""
    return _page_shell("Source Context", "Sanitized metadata", body)


def build_public_index(
    slug: str,
    quality: dict,
    owner_name: str = "Teng Kian Boon",
    *,
    has_research_report: bool = False,
) -> str:
    status = _release_status(quality)
    status_class = "pass" if quality.get("passed") else "warn"
    score = quality.get("score", "unknown")
    findings = quality.get("transcript_findings", [])
    summary_findings = quality.get("summary_findings", [])
    all_findings = list(findings) + list(summary_findings)
    finding_text = ", ".join(str(finding) for finding in all_findings) if all_findings else "No findings recorded."
    cards = [
        ("Learning Summary", "The sanitized summary in HTML form for normal reading.", "summary.html"),
        ("Public Learning Note", "The human-readable learning page to open first.", "public_learning_note.html"),
        ("Framework Placement", "How this learning should connect into the Enterprise AI solution architecture and delivery framework.", "mindmap_ingest.html"),
        ("Quality Gate", "Plain-language status for completeness, privacy, and transcript quality.", "quality_gate.html"),
        ("Source Context", "Sanitized source metadata with raw/private details withheld.", "source_metadata.html"),
    ]
    if has_research_report:
        cards.insert(
            1,
            (
                "Research-Enriched Report",
                "Vendor/web-evidence enriched report with citations and enterprise practice implications.",
                "research_enriched_report.html",
            ),
        )
    card_html = "\n".join(
        f"""
      <a class="card" href="{html.escape(filename)}">
        <strong>{html.escape(title)}</strong>
        <span>{html.escape(description)}</span>
      </a>"""
        for title, description, filename in cards
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(slug)} - Public Review Package</title>
  <style>
    body {{ margin: 0; font-family: Arial, Helvetica, sans-serif; color: #17202a; background: #f7f5ef; }}
    main {{ max-width: 980px; margin: 0 auto; padding: 32px 20px 48px; }}
    header {{ border-bottom: 2px solid #17202a; padding-bottom: 18px; }}
    .eyebrow {{ color: #0f766e; font-weight: 700; text-transform: uppercase; }}
    .top-nav {{ margin-bottom: 16px; }}
    .top-nav a {{ color: #1d4ed8; text-decoration: none; font-weight: 700; }}
    h1 {{ margin: 8px 0; font-size: 42px; line-height: 1.05; letter-spacing: 0; }}
    p {{ line-height: 1.55; }}
    .status {{ margin: 18px 0; padding: 14px 16px; border-radius: 8px; background: #fff; border-left: 6px solid #b45309; }}
    .status.pass {{ border-left-color: #0f766e; }}
    .status.warn {{ border-left-color: #be123c; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin-top: 18px; }}
    .card {{ min-height: 120px; padding: 16px; border: 1px solid #d9e0e8; border-radius: 8px; background: white; color: #17202a; text-decoration: none; }}
    .card strong {{ display: block; margin-bottom: 8px; font-size: 18px; }}
    .card span {{ color: #5f6b7a; }}
    footer {{ margin-top: 24px; color: #5f6b7a; border-top: 1px solid #d9e0e8; padding-top: 14px; }}
  </style>
</head>
<body>
<main>
  <nav class="top-nav" aria-label="Package navigation">
    <a href="../../mindmap/enterprise_ai_mindmap.html">Back to Enterprise AI Architecture &amp; Delivery Framework</a>
  </nav>
  <header>
    <div class="eyebrow">TKB Public Review Package</div>
    <h1>{html.escape(slug)}</h1>
    <p>Prepared by {html.escape(owner_name)} as a sanitized Enterprise AI solutions architecture artifact. Raw audio and full transcripts are withheld from public packages.</p>
  </header>
  <section class="status {status_class}">
    <strong>Release status:</strong> {html.escape(status)}<br>
    <strong>Quality score:</strong> {html.escape(str(score))}<br>
    <strong>Transcript findings:</strong> {html.escape(finding_text)}
  </section>
  <section class="grid" aria-label="Review package files">
    {card_html}
  </section>
  <footer>This page is the intended entry point. Raw JSON and Markdown files are retained only as machine-readable audit artifacts, not as the public reading path.</footer>
</main>
</body>
</html>
"""


def _safe_unlink(path: Path) -> None:
    if not path.exists():
        return
    try:
        path.chmod(0o666)
        path.unlink()
    except PermissionError:
        if path.name.lower() not in SYSTEM_METADATA_NAMES:
            raise


def _prepare_output_dir(public_review_root: Path, output: Path) -> None:
    root = public_review_root.resolve()
    target = output.resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise PublishingGateError(f"Refusing to clean path outside public review root: {target}") from exc
    output.mkdir(parents=True, exist_ok=True)
    for name in sorted(MANAGED_PUBLIC_FILES | SYSTEM_METADATA_NAMES):
        _safe_unlink(output / name)


def _is_development_package(private_package_dir: Path) -> bool:
    slug = private_package_dir.name.lower()
    if any(marker in slug for marker in DEVELOPMENT_PACKAGE_MARKERS):
        return True
    metadata_path = private_package_dir / "source_metadata.json"
    if not metadata_path.exists():
        return False
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    source_name = str(metadata.get("source_filename", "")).lower()
    return any(marker in source_name for marker in DEVELOPMENT_PACKAGE_MARKERS)


def _remove_public_development_package(public_review_root: Path, package_name: str) -> None:
    output = public_review_root / package_name
    if not output.exists():
        return
    for name in sorted(MANAGED_PUBLIC_FILES | SYSTEM_METADATA_NAMES):
        _safe_unlink(output / name)
    try:
        output.rmdir()
    except OSError:
        pass


def _remove_stale_development_packages(public_review_root: Path) -> None:
    for package in public_review_root.iterdir():
        if package.is_dir() and any(marker in package.name.lower() for marker in DEVELOPMENT_PACKAGE_MARKERS):
            _remove_public_development_package(public_review_root, package.name)


def _sanitize_public_metadata_value(value: object) -> object:
    if isinstance(value, str) and value.lower() in BLOCKED_PUBLIC_NAMES:
        return "private transcript artifact withheld"
    return value


def sanitize_package(private_package_dir: Path, public_review_root: Path, owner_name: str = "Teng Kian Boon") -> Path:
    if not private_package_dir.exists():
        raise PublishingGateError(f"Private package not found: {private_package_dir}")

    slug = private_package_dir.name
    output = public_review_root / slug
    quality = write_quality_score(private_package_dir)
    _prepare_output_dir(public_review_root, output)

    for name in ("quality_score.json", "mindmap_delta.json", "mindmap_ingest.md"):
        src = private_package_dir / name
        if src.exists():
            shutil.copy2(src, output / name)

    write_text(output / "summary.md", build_review_summary(private_package_dir, quality))
    write_text(output / "summary.html", build_summary_review_html(private_package_dir, quality))

    metadata_path = private_package_dir / "source_metadata.json"
    public_metadata = {
        "privacy": "raw source and full transcripts withheld",
    }
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        public_metadata = {
            "input_kind": metadata.get("input_kind"),
            "source_extension": metadata.get("source_extension"),
            "duration_seconds": metadata.get("duration_seconds"),
            "detected_language": metadata.get("detected_language"),
            "translation_status": metadata.get("translation_status"),
            "generate_full_english_transcript": metadata.get("generate_full_english_transcript"),
            "summary_input_artifact": _sanitize_public_metadata_value(metadata.get("summary_input_artifact")),
            "summary_provider": metadata.get("summary_provider"),
            "openai_translation_model": metadata.get("openai_translation_model"),
            "openai_translation_reasoning_effort": metadata.get("openai_translation_reasoning_effort"),
            "openai_summary_model": metadata.get("openai_summary_model") or metadata.get("openai_quality_model"),
            "openai_summary_reasoning_effort": metadata.get("openai_summary_reasoning_effort")
            or metadata.get("openai_reasoning_effort"),
            "mindmap_source": metadata.get("mindmap_source"),
            "mindmap_cost": metadata.get("mindmap_cost"),
            "processed_at": metadata.get("processed_at"),
            "privacy": "raw source and full transcripts withheld",
        }
        (output / "source_metadata_public.json").write_text(
            json.dumps(public_metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    public_note = build_public_note(private_package_dir, owner_name=owner_name, quality=quality)
    write_text(output / "public_learning_note.md", public_note)
    write_text(output / "public_learning_note.html", build_public_note_html(private_package_dir, owner_name, quality))
    write_text(output / "mindmap_ingest.html", build_mindmap_ingest_html(private_package_dir))
    write_text(output / "quality_gate.html", build_quality_gate_html(quality))
    write_text(output / "source_metadata.html", build_source_metadata_html(public_metadata))
    has_research_report = False
    research_status_path = private_package_dir / "research_enrichment_status.json"
    if research_status_path.exists():
        try:
            research_status = json.loads(research_status_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            research_status = {"passed": False}
        if research_status.get("passed") and (private_package_dir / "research_enriched_report.md").exists():
            for name in ("research_enriched_report.md", "research_enriched_report.html", "research_sources.json"):
                src = private_package_dir / name
                if src.exists():
                    shutil.copy2(src, output / name)
            public_research_status = {
                "topic": research_status.get("topic"),
                "generated_at": research_status.get("generated_at"),
                "provider": research_status.get("provider"),
                "model": research_status.get("model"),
                "reasoning_effort": research_status.get("reasoning_effort"),
                "source_count": research_status.get("source_count"),
                "word_count": research_status.get("word_count"),
                "passed": research_status.get("passed"),
                "findings": research_status.get("findings", []),
                "cost_note": research_status.get("cost_note"),
            }
            (output / "research_enrichment_status.json").write_text(
                json.dumps(public_research_status, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            has_research_report = True
    write_text(output / "index.html", build_public_index(slug, quality, owner_name=owner_name, has_research_report=has_research_report))
    assert_public_safe(output)
    return output


def sanitize_all(private_root: Path, public_review_root: Path, owner_name: str = "Teng Kian Boon") -> list[Path]:
    outputs = []
    public_review_root.mkdir(parents=True, exist_ok=True)
    for name in SYSTEM_METADATA_NAMES:
        _safe_unlink(public_review_root / name)
    _remove_stale_development_packages(public_review_root)
    learnings_dir = private_root / "learnings"
    if not learnings_dir.exists():
        return outputs
    for package in sorted(p for p in learnings_dir.iterdir() if p.is_dir()):
        if _is_development_package(package):
            _remove_public_development_package(public_review_root, package.name)
            continue
        outputs.append(sanitize_package(package, public_review_root, owner_name=owner_name))
    return outputs
