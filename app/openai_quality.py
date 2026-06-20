from __future__ import annotations

import json
import os
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import AppConfig
from .summary import build_summary_markdown


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"


class OpenAIQualityError(RuntimeError):
    pass


def _api_key(config: AppConfig) -> str:
    key = os.environ.get(config.openai_api_key_env, "").strip()
    if not key:
        raise OpenAIQualityError(
            f"OpenAI API key is not configured. Set {config.openai_api_key_env} in your PowerShell before real runs."
        )
    return key


def _extract_output_text(payload: dict) -> str:
    text = payload.get("output_text")
    if isinstance(text, str) and text.strip():
        return text.strip()

    parts: list[str] = []
    for item in payload.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if not isinstance(content, dict):
                continue
            content_type = content.get("type")
            if content_type in {"output_text", "text"}:
                value = content.get("text")
                if isinstance(value, str) and value.strip():
                    parts.append(value.strip())
    if parts:
        return "\n\n".join(parts).strip()

    status = payload.get("status", "unknown")
    incomplete = payload.get("incomplete_details")
    error = payload.get("error")
    output_types = [
        str(item.get("type"))
        for item in payload.get("output", [])
        if isinstance(item, dict) and item.get("type")
    ]
    if incomplete:
        raise OpenAIQualityError(
            "OpenAI response ended before producing readable text. "
            f"status={status}; incomplete_details={incomplete}; output_types={output_types}. "
            "Increase the relevant OpenAI max-output setting or lower the relevant reasoning effort."
        )
    if error:
        raise OpenAIQualityError(f"OpenAI response returned an error: {error}")
    raise OpenAIQualityError(
        "OpenAI response did not contain readable output text. "
        f"status={status}; output_types={output_types}."
    )


def _request_responses(
    prompt: str,
    config: AppConfig,
    *,
    model: str,
    reasoning_effort: str,
    max_output_tokens: int,
    purpose: str,
) -> str:
    request_body = {
        "model": model,
        "input": prompt,
        "reasoning": {"effort": reasoning_effort},
        "max_output_tokens": max_output_tokens,
        "store": False,
    }
    data = json.dumps(request_body).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {_api_key(config)}",
        "Content-Type": "application/json",
    }

    attempts = max(1, config.max_retries)
    last_error = ""
    for attempt in range(1, attempts + 1):
        request = Request(OPENAI_RESPONSES_URL, data=data, headers=headers, method="POST")
        try:
            with urlopen(request, timeout=config.openai_request_timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
                return _extract_output_text(payload)
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            last_error = f"HTTP {exc.code}: {detail[:800]}"
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = str(exc)
        if attempt < attempts:
            time.sleep(config.retry_backoff_seconds * attempt)
    raise OpenAIQualityError(
        f"OpenAI Responses API failed during {purpose} after {attempts} attempt(s). {last_error}"
    )


def extract_mindmap_ingest_suggestion(summary_text: str) -> str:
    marker = "## Mindmap Ingest Suggestion"
    if marker not in summary_text:
        return (
            "- Fit this learning into the Synthesize stage after transcript cleanup and before public publishing; "
            "review categories manually because the summary did not include a dedicated mindmap placement suggestion."
        )
    after_marker = summary_text.split(marker, 1)[1].strip()
    for next_marker in ("\n## ", "\n# "):
        if next_marker in after_marker:
            after_marker = after_marker.split(next_marker, 1)[0].strip()
    return after_marker or (
        "- Fit this learning into the Synthesize stage after summary generation and before public publishing; "
        "review exact categories manually."
    )


def translate_to_english(
    original_text: str,
    *,
    source_name: str,
    config: AppConfig,
    mock: bool = False,
) -> str:
    if mock:
        return (
            f"Mock English translation for {source_name}. "
            "Key ideas: enterprise AI, agent improvement loops, governance, quality checks, and portfolio learning."
        )
    prompt = f"""You are translating a learning transcript for Teng Kian Boon.

Task:
- Translate the transcript into natural, clear English.
- Preserve the speaker's meaning, examples, and sequence of ideas.
- Correct obvious speech-to-text artifacts only when the intended meaning is clear.
- Do not add new claims that are not in the transcript.
- Return English only, in clean paragraphs.

Source file: {source_name}

Transcript:
{original_text}
"""
    return _request_responses(
        prompt,
        config,
        model=config.openai_translation_model,
        reasoning_effort=config.openai_translation_reasoning_effort,
        max_output_tokens=config.openai_translation_max_output_tokens,
        purpose="translation",
    )


def build_quality_summary(
    source_text: str,
    *,
    source_name: str,
    source_language: str = "en",
    config: AppConfig,
    mock: bool = False,
) -> str:
    if mock:
        return build_summary_markdown(source_text, source_name)

    prompt = f"""You are helping Teng Kian Boon curate an Enterprise AI solutions architecturing and framework.

Create a high-quality public-review learning summary from the source transcript below.
The source transcript may be English, Simplified Chinese, Traditional Chinese, or a mixed speech-to-text transcript.
If the source is not English, understand it directly and produce the final learning summary in English.
Do not output a full translated transcript unless a short translated phrase is needed as an example.

Audience:
- Enterprise AI practitioners, solution architects, platform engineers, and technical delivery leaders.
- Smart non-specialists who need layman explanations without losing technical precision.

Quality requirements:
- Prefer depth over brevity. This should be a comprehensive learning note, not an executive brief.
- Target roughly 2,500 to 4,000 English words when the source has enough substance.
- Do not submit an incomplete answer. Every required section must be present and fully filled.
- If the response budget feels tight, reduce repetition but never omit sections, tables, scenarios, quality gates, or the Public Practice Note.
- Explain the learning clearly, comprehensively, accurately, and completely.
- Define every acronym on first use.
- Define technical terms in plain English.
- Include practical examples and scenarios.
- Explain why each tool, process, harness, quality gate, or architecture idea matters.
- Separate confirmed source-transcript learnings from items that need follow-up research.
- Keep the tone professional, delivery-ready, and suitable for public technical sharing by Teng Kian Boon.
- Do not expose private local paths, raw transcript dumps, secrets, or unsupported vendor claims.
- All final output must be English.
- If the transcript is noisy, reconstruct the likely intended meaning carefully and mark uncertain claims as needing follow-up research.
- Do not collapse detailed source ideas into generic statements. Preserve named concepts, mechanisms, sequence, trade-offs, and enterprise implications.

Return Markdown with exactly these sections:
# Learning Summary - {source_name}
## Executive Learning
## Plain-English Explanation
## Enterprise AI Architecture and Delivery Relevance
## Key Concepts and Definitions
## Practical Scenarios
## Why It Matters
## Implementation Implications
## Risks, Quality Gates, and Human Review
## Follow-Up Research Questions
## Mindmap Ingest Suggestion
## Public Practice Note

Section depth requirements:
- "Executive Learning": include 6 to 10 specific bullets. Separate confirmed transcript ideas from derived implications when useful.
- "Plain-English Explanation": use nested subsections with `###` headings. Explain the core problem, the proposed loop, and why the loop improves learning over time.
- "Enterprise AI Architecture and Delivery Relevance": include separate paragraphs for enterprise architecture, deployment engineering, and delivery-team operations.
- "Key Concepts and Definitions": use a Markdown table with columns "Term", "Plain-English Meaning", and "Why It Matters". Include at least 12 terms when the source has enough substance.
- "Practical Scenarios": include at least 4 scenarios using `### Scenario 1 - ...`, `### Scenario 2 - ...`, and so on. For each, describe the situation, how the learning applies, and why the business value matters.
- "Why It Matters": include 8 to 12 numbered points with clear rationale, not only short bullets.
- "Implementation Implications": split into confirmed implementation patterns and derived enterprise implementation implications.
- "Risks, Quality Gates, and Human Review": split into transcript-confirmed risks, transcript-confirmed quality gates, additional enterprise-strength gates, and the role of human review.
- "Follow-Up Research Questions": include 8 to 12 concrete questions that would strengthen enterprise adoption.
- "Public Practice Note": explain how this learning demonstrates disciplined enterprise AI architecture, development, deployment, and operating practice by Teng Kian Boon. Avoid overt career-positioning language; keep the note focused on technical judgment and operating discipline.

For "Mindmap Ingest Suggestion":
- Write exactly one concise bullet-style paragraph.
- State where this learning fits in the Enterprise AI learning process flow.
- Explicitly include: categories/stages, where it fits, what process step comes before it, what process step comes after it, and relationship cues for the mindmap.
- Use the words "Category", "Fits", "Before", and "After" inside the paragraph so the app can verify the placement guidance.
- Keep it under 90 words.

Detected source language: {source_language}

Source transcript:
{source_text}
"""
    return _request_responses(
        prompt,
        config,
        model=config.openai_summary_model,
        reasoning_effort=config.openai_summary_reasoning_effort,
        max_output_tokens=config.openai_summary_max_output_tokens,
        purpose="summary",
    )
