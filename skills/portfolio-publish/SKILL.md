---
name: portfolio-publish
description: Create sanitized public-review learning artifacts for a portfolio. Use when copying private outputs into outputs_public_review while blocking raw audio, full transcripts, secrets, private paths, and long copyrighted excerpts.
---

# Portfolio Publish

Publish only curated outputs.

## Workflow

1. Read private learning package.
2. Run privacy scan.
3. Copy only sanitized summary, public metadata, quality score, and mindmap delta.
4. Write a public learning note that describes lessons, not full source content.
5. Require human review before committing publicly.

## Never Publish

- Raw audio/video.
- Full `original_transcript.md`.
- Full `english_transcribed.md`.
- Private absolute paths.
- Secrets or API keys.
- Long quoted source passages.
