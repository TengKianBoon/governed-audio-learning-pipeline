from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from .config import AppConfig, ensure_sandbox_dirs
from .learning_delivery import build_audio_podcast_script, build_markdown_page
from .openai_quality import OpenAIQualityError, request_responses_payload, _extract_output_text
from .utils import utc_now_iso, write_text


REQUIRED_RESEARCH_SECTIONS = [
    "Research-Enriched Executive Learning",
    "What The Web Evidence Adds",
    "Vendor Evidence and Vocabulary Upgrade",
    "Enterprise AI Practice Implications",
    "Examples and Scenarios",
    "Citations and Evidence Table",
    "What Still Needs Evidence",
    "Mindmap Delta Recommendation",
]

BLOCKED_RESEARCH_DOMAINS = [
    "reddit.com",
    "quora.com",
    "wikipedia.org",
    "medium.com",
]


class ResearchEnrichmentError(RuntimeError):
    pass


def _word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)?", text))


def _has_section(text: str, section: str) -> bool:
    return re.search(rf"(?im)^##\s+{re.escape(section)}\s*$", text) is not None


def _csv_items(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _load_metadata(package_dir: Path) -> dict:
    metadata_path = package_dir / "source_metadata.json"
    if not metadata_path.exists():
        return {}
    try:
        return json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _topic_from_package(package_dir: Path, summary_text: str) -> str:
    heading = re.search(r"(?im)^#\s+Learning Summary\s+-\s+(.+)$", summary_text)
    if heading:
        return heading.group(1).strip()
    metadata = _load_metadata(package_dir)
    source_name = metadata.get("source_filename") or package_dir.name
    cleaned = re.sub(r"[_-]+", " ", Path(str(source_name)).stem)
    cleaned = re.sub(r"\bvoice\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b\d{4,8}\b", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned.title() if cleaned else package_dir.name


def _extract_sources_from_payload(payload: dict) -> list[dict]:
    found: dict[str, dict] = {}

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            url = value.get("url")
            title = value.get("title")
            if isinstance(url, str) and url.startswith(("http://", "https://")):
                found[url] = {
                    "url": url,
                    "title": str(title or value.get("domain") or url),
                }
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(payload)
    return list(found.values())


def _append_sources(report: str, sources: list[dict]) -> str:
    if not sources:
        return report
    if re.search(r"(?im)^##\s+Sources Consulted\s*$", report):
        return report
    lines = ["", "## Sources Consulted", ""]
    for index, source in enumerate(sources, start=1):
        title = str(source.get("title") or source.get("url"))
        url = str(source.get("url"))
        lines.append(f"{index}. [{title}]({url})")
    return report.rstrip() + "\n" + "\n".join(lines) + "\n"


def _quality_findings(report: str, sources: list[dict]) -> list[str]:
    findings: list[str] = []
    if _word_count(report) < 1800:
        findings.append("research_report_too_short_for_public_use")
    for section in REQUIRED_RESEARCH_SECTIONS:
        if not _has_section(report, section):
            findings.append(f"missing_research_section:{section}")
    if len(sources) < 5:
        findings.append("research_sources_too_few")
    if "http://" not in report and "https://" not in report and not sources:
        findings.append("research_report_missing_citations")
    if len(re.findall(r"(?m)^\|.*\|\s*$", report)) < 5:
        findings.append("research_report_missing_evidence_table")
    return sorted(set(findings))


def _build_prompt(topic: str, summary_text: str, mindmap_ingest: str, config: AppConfig) -> str:
    allowed_domains = ", ".join(_csv_items(config.openai_research_allowed_domains))
    return f"""You are helping Teng Kian Boon enrich a learning summary into a research-backed Enterprise AI report.

Task:
- Use web search to upgrade the summary with current enterprise AI vendor and ecosystem evidence.
- Target model configuration is {config.openai_research_model} with {config.openai_research_reasoning_effort} reasoning.
- Produce a research-enriched summary/report in English.
- Keep the report practical, layman-readable, and technically credible.
- Preserve the original learning, but add only evidence-backed deltas.

Research focus:
- Topic: {topic}
- Framework: Enterprise AI Solution Architecture & Delivery Framework
- Vendor/evidence lens: {allowed_domains}

Quality requirements:
- Target 2,000 to 3,200 words when enough evidence is available.
- Every vendor-specific claim must be supported by a citation.
- Include better vocabulary and explain every acronym on first use.
- Define technical terms plainly with enterprise examples.
- Explain what this means in enterprise AI practice, not only what vendors say.
- Compare evidence across vendors when useful, but do not force all vendors into the report if evidence is weak.
- Mark weak or unsupported claims as "needs evidence".
- Do not expose local file paths, raw transcripts, secrets, or private source material.
- Keep tone professional and subtle; focus on architecture and delivery competence.
- Do not copy long source passages.

Return Markdown with exactly these sections:
# Research-Enriched Report - {topic}
## Research-Enriched Executive Learning
## What The Web Evidence Adds
## Vendor Evidence and Vocabulary Upgrade
## Enterprise AI Practice Implications
## Examples and Scenarios
## Citations and Evidence Table
## What Still Needs Evidence
## Mindmap Delta Recommendation
## Public Practice Note

Section details:
- Research-Enriched Executive Learning: 8 to 12 concrete bullets.
- What The Web Evidence Adds: explain the deltas versus the original summary.
- Vendor Evidence and Vocabulary Upgrade: include a table with columns "Concept", "Evidence Signal", "Enterprise Meaning", and "Source".
- Enterprise AI Practice Implications: explain architecture, governance, deployment, operating model, and cost controls.
- Examples and Scenarios: include at least 4 scenario subsections.
- Citations and Evidence Table: list source title, vendor/publisher, URL, and why it matters.
- Mindmap Delta Recommendation: one concise bullet paragraph with Category, Fits, Before, and After cues.
- Public Practice Note: explain how the enriched learning strengthens the Enterprise AI Solution Architecture & Delivery Framework.

Existing summary:
{summary_text}

Existing mindmap placement suggestion:
{mindmap_ingest}
"""


def _mock_report(topic: str) -> tuple[str, list[dict], dict]:
    sources = [
        {"title": "OpenAI API Docs", "url": "https://platform.openai.com/docs"},
        {"title": "Anthropic Docs", "url": "https://docs.anthropic.com"},
        {"title": "Microsoft Azure AI", "url": "https://azure.microsoft.com/products/ai-services"},
        {"title": "AWS AI Services", "url": "https://aws.amazon.com/ai/"},
        {"title": "Salesforce AI", "url": "https://www.salesforce.com/artificial-intelligence/"},
    ]
    depth = (
        "For enterprise AI practice, the important point is to convert vendor language into delivery controls, "
        "architecture decisions, operating responsibilities, quality gates, and human-review checkpoints. "
        "A public-ready learning report should explain the business situation, the technical mechanism, the "
        "risk boundary, and the implementation implication in plain English. "
    ) * 40
    report = f"""# Research-Enriched Report - {topic}

## Research-Enriched Executive Learning

- This mock report demonstrates the intended structure for vendor-evidence enrichment.
- Enterprise AI summaries should separate transcript-derived learning from web-verified claims.
- Citations should be attached to vendor-specific statements.
- The public layer should present practical architecture and delivery implications.
- Quality gates should block thin, uncited, or privacy-risky research notes.
- Mindmap updates should use the summary-level delta, not raw transcript material.
- The operator should approve public publishing after reviewing sources.
- NotebookLM handoff files should use this enriched report when available.

## What The Web Evidence Adds

Mock evidence adds vendor language, public-source citations, and clearer enterprise vocabulary.

{depth}

## Vendor Evidence and Vocabulary Upgrade

| Concept | Evidence Signal | Enterprise Meaning | Source |
|---|---|---|---|
| Governance | Vendor documentation emphasizes controls | Quality and risk checks must be designed into delivery | OpenAI |
| Platform operations | Cloud vendors describe managed AI services | Architecture must consider deployment and operations | AWS |
| CRM AI | Salesforce positions AI around workflow productivity | Business context affects solution design | Salesforce |

## Enterprise AI Practice Implications

The enriched report should explain architecture, governance, deployment, operating model, and cost controls.

{depth}

## Examples and Scenarios

### Scenario 1 - Quality Gate
Use citations to verify a claim before it enters a public framework.

### Scenario 2 - Vendor Vocabulary
Compare vendor terms and map them into a neutral delivery framework.

### Scenario 3 - Human Review
Keep the operator in the approval path for public release.

### Scenario 4 - NotebookLM Handoff
Use the enriched report as a better source bundle for slides, infographics, and audio.

## Citations and Evidence Table

| Source | Publisher | URL | Why It Matters |
|---|---|---|---|
| OpenAI API Docs | OpenAI | https://platform.openai.com/docs | API capability reference |
| Anthropic Docs | Anthropic | https://docs.anthropic.com | Alternative AI platform reference |
| Azure AI | Microsoft | https://azure.microsoft.com/products/ai-services | Enterprise cloud AI reference |
| AWS AI | AWS | https://aws.amazon.com/ai/ | Cloud AI deployment reference |
| Salesforce AI | Salesforce | https://www.salesforce.com/artificial-intelligence/ | Business workflow AI reference |

## What Still Needs Evidence

- Confirm current product limits before making detailed claims.
- Confirm pricing and availability before publishing cost assumptions.

## Mindmap Delta Recommendation

- Category: Synthesize/Govern; Fits after summary generation and before public publishing; Before NotebookLM handoff; After transcript and summary quality gates; relationship cues: evidence enrichment, vendor comparison, citation discipline.

## Public Practice Note

This enriched layer demonstrates controlled research, evidence handling, and public-readiness discipline.

{depth}
"""
    return report, sources, {"usage": {"mock": True}}


def enrich_learning_research(package_dir: Path, config: AppConfig, *, mock: bool = False) -> dict:
    ensure_sandbox_dirs(config)
    if not package_dir.exists():
        raise ResearchEnrichmentError(f"Learning package not found: {package_dir}")

    summary_path = package_dir / "summary.md"
    if not summary_path.exists():
        raise ResearchEnrichmentError(f"summary.md not found in package: {package_dir}")
    summary_text = summary_path.read_text(encoding="utf-8")
    mindmap_path = package_dir / "mindmap_ingest.md"
    mindmap_ingest = mindmap_path.read_text(encoding="utf-8") if mindmap_path.exists() else ""
    topic = _topic_from_package(package_dir, summary_text)

    if mock:
        report, sources, payload = _mock_report(topic)
    else:
        tools = [
            {
                "type": "web_search",
                "search_context_size": config.openai_research_search_context_size,
                "user_location": {"type": "approximate", "country": "US"},
                "filters": {
                    "allowed_domains": _csv_items(config.openai_research_allowed_domains),
                    "blocked_domains": BLOCKED_RESEARCH_DOMAINS,
                },
            }
        ]
        if config.openai_research_return_token_budget:
            tools[0]["return_token_budget"] = config.openai_research_return_token_budget
        payload = request_responses_payload(
            _build_prompt(topic, summary_text, mindmap_ingest, config),
            config,
            model=config.openai_research_model,
            reasoning_effort=config.openai_research_reasoning_effort,
            max_output_tokens=config.openai_research_max_output_tokens,
            purpose="research enrichment",
            tools=tools,
            tool_choice="required",
            include=["web_search_call.action.sources"],
        )
        try:
            report = _extract_output_text(payload)
        except OpenAIQualityError as exc:
            raise ResearchEnrichmentError(str(exc)) from exc
        sources = _extract_sources_from_payload(payload)

    report = _append_sources(report, sources)
    findings = _quality_findings(report, sources)
    status = {
        "package": str(package_dir),
        "topic": topic,
        "generated_at": utc_now_iso(),
        "provider": "openai-responses-web-search",
        "model": config.openai_research_model,
        "reasoning_effort": config.openai_research_reasoning_effort,
        "search_context_size": config.openai_research_search_context_size,
        "return_token_budget": config.openai_research_return_token_budget,
        "source_count": len(sources),
        "word_count": _word_count(report),
        "passed": not findings,
        "findings": findings,
        "usage": payload.get("usage", {}),
        "cost_note": "Paid OpenAI call: model tokens plus web_search tool usage. Check OpenAI dashboard for exact billed cost.",
    }

    write_text(package_dir / "research_enriched_report.md", report)
    write_text(package_dir / "research_enriched_report.html", build_markdown_page("Research-Enriched Report", report))
    write_text(package_dir / "research_sources.json", json.dumps(sources, ensure_ascii=False, indent=2))
    write_text(package_dir / "research_enrichment_status.json", json.dumps(status, ensure_ascii=False, indent=2))

    enriched_script = build_audio_podcast_script(report, f"research_enriched_{topic}.md")
    write_text(package_dir / "audio_podcast_script_research_enriched.md", enriched_script)
    notebooklm_dir = package_dir / "notebooklm_package"
    write_text(notebooklm_dir / "research_enriched_report.md", report)
    write_text(notebooklm_dir / "audio_podcast_script_research_enriched.md", enriched_script)
    if (notebooklm_dir / "source_bundle.md").exists():
        existing_bundle = (notebooklm_dir / "source_bundle.md").read_text(encoding="utf-8")
    else:
        existing_bundle = ""
    write_text(
        notebooklm_dir / "source_bundle.md",
        f"{existing_bundle.rstrip()}\n\n# Research-Enriched Report\n\n{report}\n",
    )

    return {
        "package": str(package_dir),
        "research_report": str(package_dir / "research_enriched_report.html"),
        "research_status": str(package_dir / "research_enrichment_status.json"),
        "source_count": len(sources),
        "word_count": status["word_count"],
        "passed": status["passed"],
        "findings": findings,
    }


def latest_learning_package(config: AppConfig) -> Path:
    ensure_sandbox_dirs(config)
    candidates = [path for path in (config.private_outputs_dir / "learnings").glob("*") if path.is_dir()]
    if not candidates:
        raise ResearchEnrichmentError("No private learning packages found.")
    return max(candidates, key=lambda path: path.stat().st_mtime)
