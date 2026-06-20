---
name: quality-gate
description: Score and verify Enterprise AI Learning Audio App outputs. Use when checking source metadata, transcript completeness, English transcript quality, mindmap delta, privacy gates, and score threshold before marking work done.
---

# Quality Gate

The verifier checks the maker's output.

## Required Checks

1. `source_metadata.json` exists.
2. `original_transcript.md` exists in private output.
3. `english_transcribed.md` exists in private output.
4. `summary.md` exists.
5. `mindmap_delta.json` exists.
6. `cost_budget.json` exists and is reviewed before paid AI/search work.
7. Publishing gate blocks private artifacts.
8. Score is at least 80.

## Guardrails

- Maker cannot self-approve.
- Failing checks produce exact evidence.
- Retry max 3, then escalate.
- Token and cost budgets are explicit; do not hide projected spend.
