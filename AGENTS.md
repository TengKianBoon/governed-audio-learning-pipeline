# AGENTS.md - Project Constitution

This file is the standing context for agents working on the Enterprise AI Learning Audio App.

## What This Is

A privacy-preserving learning pipeline that turns Chinese/English audio, local video files, and phone-generated text transcripts into private transcripts, English learning notes, OpenAI quality summaries, and a growing enterprise AI mindmap.

## Non-Negotiable Rules

1. Public code, private raw learning data.
2. Never overwrite original audio or video files.
3. Never publish raw audio, full private transcripts, secrets, or copyrighted long excerpts.
4. FFmpeg is configured by path or portable copy; do not change global PATH without human approval.
5. Prefer MCP-ready tools over shell commands for orchestration.
6. OpenAI is the approved quality provider for this MVP; keep keys private, costs budgeted, and provider-specific choices documented.
7. Manual-first autonomy: the human approves public publishing and merge-to-main.
8. Maker cannot verify its own work; verifier/score gate must check outputs.
9. Retry max is 3 with reflect-before-retry; then escalate.
10. Token/cost budgets are explicit; OpenAI quality calls must stay within configured per-task and daily budgets.
11. Fail visible, never silent-wrong: mark outputs as pending or needs-review instead of inventing results.
12. For any public-facing app, follow `docs/github-showcase-standard.md`: clear architecture story, tests, audit, privacy gate, build journal, and curated demo artifacts.

## Definition Of Done

- `python -m unittest discover -s tests` passes.
- `python tests/score.py` reports `SCORE >= 80`.
- New public artifacts pass the publishing gate.
- Any new decision with lasting impact has an ADR or build-journal note.

## Beginner Guardrail

If one audio file cannot be processed end to end, do not add another agent or automation layer.

## Portfolio Posture

This should read publicly as a mid-to-senior Enterprise AI solutions architecturing and framework project by Teng Kian Boon: OpenAI-assisted, human-reviewed, cost-aware, and privacy-preserving. Do not frame the project as "made by ChatGPT" or as an unreviewed automation demo.
