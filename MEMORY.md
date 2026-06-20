# Project Memory

## Current Defaults

- App code is public-ready.
- Raw audio and full transcripts remain private.
- MVP is privacy-preserving with manual-triggered runs.
- FFmpeg is configured by path and never globally installed by this app.
- Whisper is the default transcription engine for audio/video.
- `.txt` and `.md` phone transcript drops are supported inputs.
- OpenAI gpt-5.4-mini is the approved daily learning-summary layer.
- Daily mode skips full English transcript translation and summarizes directly from the original source transcript in English.
- Full English transcript translation is optional and off by default.
- Mindmap updates remain zero-cost and use `summary.md` plus `mindmap_ingest.md`, not raw transcripts.
- Chunking is included for long seminars.
- Retry cap is 3 by default.
- Cost guard records rough token estimates per learning package before batch OpenAI use.
- MCP-ready tools are the primary orchestration interface; CLI is a beginner fallback.
- Public positioning target is level 7.5/10 enterprise AI builder: TKB as owner/operator, AI as governed toolchain.

## Important Decisions

- ADR-0001: Public code, private raw learning vault.
- ADR-0002: FFmpeg portable/configured, no global PATH mutation.
- ADR-0003: Manual-first agentic build and human gates.
- ADR-0004: Retry and token budget controls.
- ADR-0005: MCP-first interface, CLI as fallback.
- ADR-0006: Provider-neutral portable architecture.
- ADR-0007: OpenAI quality layer for translation and synthesis.

## Open Items

- Locate or configure the FFmpeg and FFprobe executable paths.
- Set `OPENAI_API_KEY` in PowerShell before real non-mock quality runs.
- Grant write access to the private audio sandbox if folders should be created automatically.
- Add real sample files after privacy review.
- Initialize Git locally when `.git` metadata writes are allowed.
