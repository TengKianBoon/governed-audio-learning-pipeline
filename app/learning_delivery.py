from __future__ import annotations

import html
import re
from pathlib import Path
from urllib.parse import quote_plus

from .utils import utc_now_iso, write_text


FRAMEWORK_TITLE = "Enterprise AI Solution Architecture & Delivery Framework"

ENTERPRISE_AI_VENDOR_LENSES = [
    "OpenAI",
    "Anthropic",
    "Microsoft",
    "Google Cloud",
    "AWS",
    "Oracle",
    "SAP",
    "Salesforce",
    "ServiceNow",
    "Palantir",
    "Databricks",
    "Snowflake",
    "NVIDIA",
    "IBM",
    "Accenture",
    "Deloitte",
    "Cohere",
    "Mistral AI",
    "Hugging Face",
    "LangChain",
    "Cursor",
    "Y Combinator",
]


def _section_text(markdown: str, section: str) -> str:
    pattern = rf"(?ims)^##\s+{re.escape(section)}\s*$\n(?P<body>.*?)(?=^##\s+|\Z)"
    match = re.search(pattern, markdown)
    return match.group("body").strip() if match else ""


def _markdown_to_html(markdown: str) -> str:
    blocks: list[str] = []
    paragraph: list[str] = []
    list_items: list[str] = []

    def inline_html(text: str) -> str:
        rendered: list[str] = []
        cursor = 0
        for match in re.finditer(r"\[([^\]]+)\]\((https?://[^)]+)\)", text):
            rendered.append(html.escape(text[cursor : match.start()]))
            label = html.escape(match.group(1))
            url = html.escape(match.group(2), quote=True)
            rendered.append(f'<a href="{url}">{label}</a>')
            cursor = match.end()
        rendered.append(html.escape(text[cursor:]))
        return "".join(rendered)

    def flush_list() -> None:
        if list_items:
            blocks.append("<ul>" + "".join(list_items) + "</ul>")
            list_items.clear()

    def flush_paragraph() -> None:
        if paragraph:
            blocks.append(f"<p>{inline_html(' '.join(paragraph))}</p>")
            paragraph.clear()

    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            flush_list()
            continue
        if stripped.startswith("|") and stripped.endswith("|"):
            flush_paragraph()
            flush_list()
            cells = [inline_html(cell.strip()) for cell in stripped.strip("|").split("|")]
            blocks.append("<p>" + " | ".join(cells) + "</p>")
            continue
        if stripped.startswith("#"):
            flush_paragraph()
            flush_list()
            level = min(len(stripped) - len(stripped.lstrip("#")), 3)
            text = stripped[level:].strip()
            blocks.append(f"<h{level}>{inline_html(text)}</h{level}>")
            continue
        if stripped.startswith("- "):
            flush_paragraph()
            list_items.append(f"<li>{inline_html(stripped[2:].strip())}</li>")
            continue
        numbered = re.match(r"^\d+\.\s+(.*)$", stripped)
        if numbered:
            flush_paragraph()
            list_items.append(f"<li>{inline_html(numbered.group(1).strip())}</li>")
            continue
        flush_list()
        paragraph.append(stripped)

    flush_paragraph()
    flush_list()
    return "\n".join(blocks)


def _clean_title(value: str) -> str:
    cleaned = re.sub(r"[_-]+", " ", Path(value).stem)
    cleaned = re.sub(r"\bvoice\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b\d{6,8}\b", "", cleaned)
    cleaned = re.sub(r"\b\d{4,6}\b", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned.title() if cleaned else "Enterprise AI Learning Topic"


def _summary_title(summary_text: str, source_name: str) -> str:
    first_heading = re.search(r"(?im)^#\s+Learning Summary\s+-\s+(.+)$", summary_text)
    if first_heading:
        return _clean_title(first_heading.group(1))
    return _clean_title(source_name)


def _plain_text(markdown: str) -> str:
    text = re.sub(r"(?m)^#{1,6}\s+", "", markdown)
    text = re.sub(r"(?m)^\s*[-*]\s+", "", text)
    text = re.sub(r"(?m)^\s*\d+\.\s+", "", text)
    text = re.sub(r"\|", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _search_url(query: str) -> str:
    return f"https://www.google.com/search?q={quote_plus(query)}"


def _core_research_queries(topic: str) -> list[str]:
    return [
        f"{topic} enterprise AI solution architecture best practices current vendor documentation",
        f"{topic} AI governance quality gates cost controls human review enterprise deployment",
        f"{topic} agent orchestration workflow memory evaluation MCP enterprise architecture",
    ]


def build_web_research_queries(topic: str, summary_text: str) -> str:
    focus = _plain_text(_section_text(summary_text, "Mindmap Ingest Suggestion"))[:240]
    core_queries = _core_research_queries(topic)
    vendor_queries = [
        f"{vendor} enterprise AI {topic} architecture deployment governance"
        for vendor in ENTERPRISE_AI_VENDOR_LENSES
    ]
    query_lines = "\n".join(f"- [{query}]({_search_url(query)})" for query in core_queries)
    vendor_lines = "\n".join(f"- [{query}]({_search_url(query)})" for query in vendor_queries)
    vendor_text = ", ".join(ENTERPRISE_AI_VENDOR_LENSES)
    return f"""# Web Research Upgrade - {topic}

## Purpose

Use this research checklist only when the operator wants to upgrade the learning from transcript-derived synthesis into a better-evidenced public technical note.

## Current Learning Focus

{focus or "Focus should be confirmed from the summary and mindmap ingest suggestion."}

## Core Search Buttons

{query_lines}

## Vendor Landscape Lenses

These vendor lenses are not endorsements and not automatic claims. They are prompts for comparing current public documentation, product positioning, architecture patterns, governance controls, and deployment trade-offs across major enterprise AI providers and ecosystems: {vendor_text}.

{vendor_lines}

## Evidence Rules

- Prefer official vendor documentation, engineering blogs, product docs, research papers, and dated release notes.
- Capture source title, URL, publisher, and publication or access date.
- Mark unsupported claims as `needs evidence` instead of treating them as facts.
- Compare the vendor evidence against the existing summary; add only meaningful deltas to the framework map.
- Avoid copying long passages. Summarize in your own words and cite the source.
"""


def build_summary_html(summary_text: str, source_name: str, slug: str) -> str:
    topic = _summary_title(summary_text, source_name)
    research_query = _core_research_queries(topic)[0]
    body = _markdown_to_html(summary_text)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(topic)} - Learning Summary</title>
  <style>
    body {{ margin: 0; font-family: Arial, Helvetica, sans-serif; color: #17202a; background: #f7f5ef; }}
    main {{ max-width: 980px; margin: 0 auto; padding: 32px 20px 52px; }}
    header {{ border-bottom: 2px solid #17202a; padding-bottom: 18px; margin-bottom: 20px; }}
    .eyebrow {{ color: #0f766e; font-weight: 700; text-transform: uppercase; }}
    h1 {{ margin: 8px 0; font-size: 42px; line-height: 1.06; letter-spacing: 0; }}
    h2 {{ margin-top: 30px; }}
    h3 {{ margin-top: 22px; }}
    p, li {{ line-height: 1.58; }}
    a {{ color: #1d4ed8; }}
    .actions {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 18px; }}
    .button {{ display: inline-block; padding: 10px 14px; border-radius: 8px; border: 1px solid #0f766e; background: #0f766e; color: #fff; text-decoration: none; font-weight: 700; }}
    .button.secondary {{ background: #fff; color: #0f766e; }}
    .panel {{ background: #fff; border: 1px solid #d9e0e8; border-radius: 8px; padding: 18px; margin: 16px 0 22px; }}
    .note {{ border-left: 6px solid #b45309; background: #fff8eb; }}
    .summary {{ background: #fff; border: 1px solid #d9e0e8; border-radius: 8px; padding: 22px; }}
    .muted {{ color: #5f6b7a; }}
  </style>
</head>
<body>
<main>
  <header>
    <div class="eyebrow">TKB Enterprise AI Learning System</div>
    <h1>{html.escape(topic)}</h1>
    <p class="muted">Part of the {html.escape(FRAMEWORK_TITLE)}. Generated for operator review from source package <code>{html.escape(slug)}</code>.</p>
    <div class="actions">
      <a class="button" href="{html.escape(_search_url(research_query))}">Web-search this topic</a>
      <a class="button secondary" href="web_research_queries.html">Open research checklist</a>
      <a class="button secondary" href="audio_podcast_script.md">Open podcast script</a>
      <a class="button secondary" href="notebooklm_package/notebooklm_handoff.md">NotebookLM handoff</a>
    </div>
  </header>
  <section class="panel note">
    <p><strong>Research checkpoint:</strong> this summary is a learning synthesis. Use the web-search checklist when you want stronger vendor verification, fresher vocabulary, layman examples, and cited deltas before public promotion.</p>
  </section>
  <section class="summary">
    {body}
  </section>
</main>
</body>
</html>
"""


def _script_source_notes(summary_text: str) -> str:
    sections = [
        "Executive Learning",
        "Plain-English Explanation",
        "Enterprise AI Architecture and Delivery Relevance",
        "Practical Scenarios",
        "Why It Matters",
        "Risks, Quality Gates, and Human Review",
        "Mindmap Ingest Suggestion",
    ]
    notes = []
    for section in sections:
        text = _section_text(summary_text, section)
        if text:
            notes.append(f"## Source Notes - {section}\n\n{text.strip()}")
    return "\n\n".join(notes) if notes else summary_text


def build_audio_podcast_script(summary_text: str, source_name: str) -> str:
    topic = _summary_title(summary_text, source_name)
    notes = _script_source_notes(summary_text)
    plain_notes = _plain_text(notes)
    excerpt = plain_notes[:6500].strip()
    return f"""# Audio Podcast Script - {topic}

## Target

- Duration: 5 to 10 minutes.
- Language: English.
- Audience: enterprise AI learners, solution architects, delivery leads, and technically curious operators.
- Tone: calm, practical, beginner-friendly, but still architecturally serious.

## Script

Welcome. In this episode, we are unpacking one learning inside the {FRAMEWORK_TITLE}: **{topic}**.

The core idea is simple: enterprise AI work is not only about building a model or connecting an application to a chatbot. It is about designing a repeatable delivery system. That system needs a way to capture knowledge, turn messy source material into clean understanding, compare new learning against what is already known, and decide what should become part of the operating framework.

Let us start with the plain-English version. A learning artifact begins as something raw: an audio note, a meeting recording, a phone transcript, or a rough idea captured during the day. Raw material is useful, but it is not yet reliable knowledge. To make it useful, the system converts it into a structured summary, checks whether it is understandable, extracts the enterprise AI concepts, and places the learning into a broader architecture and delivery map.

Why does this matter? In enterprise environments, knowledge becomes valuable only when it can be reused by teams. A one-time note is helpful to the person who made it. A structured learning flow is useful to a delivery team, a platform team, and future reviewers. It shows what was learned, why it matters, where it belongs, and what still needs evidence.

The first practical lesson is that transcription is only the start. Speech-to-text output can be noisy, especially when the original audio mixes Chinese, English, acronyms, and technical phrases. The summary layer should not blindly publish the transcript. It should reconstruct the intended meaning carefully, explain technical terms, define acronyms, and mark uncertain claims for follow-up research. That turns a rough capture into a learning asset.

The second lesson is that architecture needs placement. A new idea should not float as an isolated page. It should connect to a stage in the framework: capture, transcribe, orchestrate, govern, synthesize, or publish. It should also say what comes before and after. For example, a quality-gate idea might come after transcription cleanup and before public publishing. A workflow orchestration idea might fit after source ingestion and before evaluation. These relationships are what make the map useful over time.

The third lesson is governance. Enterprise AI systems need checks for privacy, cost, quality, and human review. Private raw audio and full transcripts should remain protected. Public artifacts should be sanitized. Costly model calls should be deliberate. Repeated failures should stop after a fixed retry limit. Human approval should remain part of public release, especially when claims are technical or vendor-related.

The fourth lesson is evidence. A transcript can explain an idea, but a public technical note becomes stronger when it is compared with current vendor documentation and public references. This does not mean turning the system into a vendor advertisement. It means using vendor evidence to validate vocabulary, discover missing patterns, and distinguish proven practices from ideas that still need testing.

For a practical scenario, imagine a team is learning about agent improvement loops. The raw idea might be: an agent should improve after every task. The structured enterprise version is more precise: the agent needs telemetry, evaluation criteria, retry limits, memory boundaries, regression tests, and a human approval checkpoint. Without those controls, self-improvement can become uncontrolled drift. With those controls, it becomes disciplined learning.

Another scenario is a delivery team preparing public learning artifacts. The team should not publish raw notes directly. It should create a summary, check the quality score, prepare a public review package, and only then decide whether the learning belongs in the shared framework. This protects privacy while still showing real progress.

The key takeaway is that a learning system can become an architecture system. Every audio note or transcript is a small input. The value comes from the pipeline that turns those inputs into definitions, examples, decisions, quality gates, and relationships. Over time, the framework becomes richer without becoming chaotic.

Here is the operational discipline to remember. Capture the source. Preserve private evidence. Generate a clear English summary. Add a concise mindmap placement suggestion. Check quality. Research when needed. Publish only reviewed outputs. Then update the framework map so the next learning has a stronger base to build on.

In short, this learning is about making enterprise AI knowledge compound. The goal is not only to collect notes. The goal is to build a trustworthy, evolving delivery framework that explains what was learned, how it applies, and why it matters in real implementation work.

## Source Notes For NotebookLM

{excerpt}
"""


def build_notebooklm_handoff(topic: str) -> str:
    return f"""# NotebookLM Handoff - {topic}

## Current Automation Position

This package is prepared for NotebookLM upload. Full automatic NotebookLM generation is intentionally not enabled yet because the workflow depends on NotebookLM product access, user account state, and UI/API availability. Treat this as a controlled human-in-the-loop handoff.

## Files To Upload

1. `source_bundle.md`
2. `audio_podcast_script.md`
3. `deck_slides_prompt.md`
4. `infographic_prompt.md`
5. `audio_overview_prompt.md`

Do not upload raw audio, private transcripts, local file paths, API keys, or unreviewed private notes unless you deliberately approve that for a private notebook.

## Requested NotebookLM Outputs

1. English deck slides for executive and technical review.
2. Detailed English infographic explaining the architecture and delivery flow.
3. English audio overview or podcast-style explanation.

## Human Review Gate

Before publishing any NotebookLM output, confirm:

- No private local paths or raw transcript snippets are exposed.
- Vendor claims are either cited or marked as needing evidence.
- Technical terms are explained in plain English.
- The output supports the {FRAMEWORK_TITLE} rather than generic AI hype.
"""


def _deck_prompt(topic: str) -> str:
    return f"""# Deck Slides Prompt - {topic}

Create an English slide deck for the topic `{topic}` as part of the {FRAMEWORK_TITLE}.

Requirements:
- 8 to 12 slides.
- Explain the problem, architecture pattern, delivery flow, quality gates, risks, and operating model.
- Use plain English definitions for acronyms and technical terms.
- Include one slide with a process flow.
- Include one slide with governance and human-review checkpoints.
- Include one slide with follow-up research questions.
- Avoid private local paths, raw transcript excerpts, or unsupported vendor claims.
"""


def _infographic_prompt(topic: str) -> str:
    return f"""# Infographic Prompt - {topic}

Create a detailed English infographic for `{topic}`.

Show:
- Capture -> summarize -> research -> govern -> framework update -> publish flow.
- Where this learning fits in the enterprise AI architecture and delivery framework.
- Key terms with short layman definitions.
- Risks and quality gates.
- Human-in-the-loop decision points.
- A clear distinction between transcript-derived learning and vendor-verified evidence.
"""


def _audio_prompt(topic: str) -> str:
    return f"""# Audio Overview Prompt - {topic}

Use `audio_podcast_script.md` as the preferred script backbone.

Generate a 5 to 10 minute English audio overview that:
- Explains the learning in beginner-friendly language.
- Keeps the tone professional and practical.
- Defines technical terms before using them deeply.
- Gives enterprise delivery examples.
- Avoids private source details and unsupported vendor claims.
"""


def build_source_bundle(summary_text: str, mindmap_ingest: str, topic: str) -> str:
    return f"""# Source Bundle - {topic}

## Framework

{FRAMEWORK_TITLE}

## Reviewed Summary

{summary_text}

## Mindmap Placement

{mindmap_ingest}

## Research Upgrade Reminder

Use `web_research_queries.md` before making vendor-specific public claims.
"""


def write_learning_delivery_artifacts(
    package_dir: Path,
    *,
    summary_text: str,
    source_name: str,
    slug: str,
    mindmap_ingest_suggestion: str,
) -> dict:
    topic = _summary_title(summary_text, source_name)
    research_markdown = build_web_research_queries(topic, summary_text)
    podcast_script = build_audio_podcast_script(summary_text, source_name)
    notebooklm_dir = package_dir / "notebooklm_package"

    write_text(package_dir / "summary.html", build_summary_html(summary_text, source_name, slug))
    write_text(package_dir / "web_research_queries.md", research_markdown)
    write_text(package_dir / "web_research_queries.html", _page_from_markdown("Web Research Checklist", research_markdown))
    write_text(package_dir / "audio_podcast_script.md", podcast_script)
    write_text(notebooklm_dir / "notebooklm_handoff.md", build_notebooklm_handoff(topic))
    write_text(notebooklm_dir / "source_bundle.md", build_source_bundle(summary_text, mindmap_ingest_suggestion, topic))
    write_text(notebooklm_dir / "audio_podcast_script.md", podcast_script)
    write_text(notebooklm_dir / "deck_slides_prompt.md", _deck_prompt(topic))
    write_text(notebooklm_dir / "infographic_prompt.md", _infographic_prompt(topic))
    write_text(notebooklm_dir / "audio_overview_prompt.md", _audio_prompt(topic))

    return {
        "summary_html": "summary.html",
        "web_research_queries": "web_research_queries.md",
        "web_research_queries_html": "web_research_queries.html",
        "audio_podcast_script": "audio_podcast_script.md",
        "notebooklm_package": "notebooklm_package",
        "notebooklm_handoff": "notebooklm_package/notebooklm_handoff.md",
        "delivery_generated_at": utc_now_iso(),
        "notebooklm_automation": "handoff_package_only_until_official_api_or_stable_browser_flow_is_approved",
    }


def _page_from_markdown(title: str, markdown: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    body {{ margin: 0; font-family: Arial, Helvetica, sans-serif; color: #17202a; background: #f7f5ef; }}
    main {{ max-width: 920px; margin: 0 auto; padding: 32px 20px 48px; }}
    h1 {{ font-size: 38px; line-height: 1.08; letter-spacing: 0; }}
    p, li {{ line-height: 1.58; }}
    a {{ color: #1d4ed8; }}
    section {{ background: #fff; border: 1px solid #d9e0e8; border-radius: 8px; padding: 20px; }}
  </style>
</head>
<body>
<main>
  <section>
    {_markdown_to_html(markdown)}
  </section>
</main>
</body>
</html>
"""


def build_markdown_page(title: str, markdown: str) -> str:
    return _page_from_markdown(title, markdown)
