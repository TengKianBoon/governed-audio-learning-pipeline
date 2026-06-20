---
name: translate-transcript
description: Translate original-language learning transcripts into English markdown for the Enterprise AI Learning Audio App. Use when converting Chinese/English transcripts into english_transcribed.md while preserving technical terms and uncertainty notes.
---

# Translate Transcript

Translate after original-language transcription is saved.

## Workflow

1. Preserve original technical terms, vendor names, and product names.
2. Translate meaning, not word-by-word phrasing.
3. Keep timestamps when available.
4. If translation quality is uncertain, add a short `needs_review` note in the quality file.
5. Write `english_transcribed.md`.

## Guardrails

- Do not publish the full translated transcript automatically.
- Do not remove ambiguity; mark unclear words explicitly.
- Prefer local/free translation first; paid APIs are optional later.
