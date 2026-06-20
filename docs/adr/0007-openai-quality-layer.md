# ADR 0007: OpenAI Quality Layer For Translation And Synthesis

## Status

Accepted

## Context

The app originally emphasized provider neutrality and local-first processing. The MVP now needs higher-quality English translation and learning synthesis so public artifacts can support Teng Kian Boon's Enterprise AI portfolio positioning.

Phone transcript inputs may arrive as Simplified Chinese or English `.txt` files. Audio/video inputs still need Whisper transcription first. After that, every learning should become English, be summarized clearly, and feed the evolving Enterprise AI learning mindmap.

## Decision

Use OpenAI as the approved quality provider for this MVP:

- Whisper remains the core transcription path for audio/video.
- Text transcript files bypass Whisper and enter language detection directly.
- English inputs skip translation.
- Daily mode skips full English transcript translation and sends the original source transcript directly into the OpenAI summary step.
- Quality summaries use `gpt-5.4-mini` with `reasoning.effort: high` and must be written in English even when the source transcript is Chinese.
- Full English transcript translation remains available through `generate_full_english_transcript: true`, but it is off by default to control cost.
- Each summary includes one concise `Mindmap Ingest Suggestion` so the local mindmap update can place the learning without another paid model call.
- API keys are supplied through `OPENAI_API_KEY`, never committed to Git.
- Generated `cost_budget.json` files track estimated token usage for cost control.

## Consequences

Positive:

- Public summaries should be far more readable and public-exhibit ready than raw transcript drafts.
- The workflow is simpler to explain: Whisper for transcription, OpenAI for English learning synthesis.
- Cost controls, retries, and human review remain visible.
- The mindmap remains a zero-cost local update based on the refined summary rather than rough transcript text.
- Avoiding the full English transcript step reduces repeated token ingestion for routine learning notes.

Tradeoffs:

- Real non-mock processing now needs an OpenAI API key.
- OpenAI API availability and account limits can block translation/summary.
- Higher-quality summaries may cost more, so per-task budgets must be monitored.
- A full English transcript is not available by default; technical readers should read `summary.md`, `mindmap_ingest.md`, and the original transcript when deeper audit is needed.

## Guardrails

- Do not store API keys in config files.
- Keep raw audio and full transcripts private.
- Do not publish sanitized artifacts until `publish --sanitize` and `exhibit --audit` pass.
- Keep `max_retries` capped at 3.
- Review `cost_budget.json` before broad batch processing.
