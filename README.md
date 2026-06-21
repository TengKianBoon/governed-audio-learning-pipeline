# Governed Audio Learning Pipeline

Local-first pipeline that turns spoken content - Chinese or English voice recordings, local video files, or phone-generated `.txt`/`.md` transcripts - into governed knowledge artifacts:

- original-language transcript
- optional English markdown transcript
- OpenAI quality summary and quality score
- HTML learning summary with a web-research upgrade button
- 5 to 10 minute English podcast script
- NotebookLM handoff package for slides, infographics, and audio overview generation
- private NotebookLM source folder containing `original_transcript.md`, `summary.md`, and `summary.html`
- concept-map / framework-map delta review
- sanitized, public-safe review package

The code repository is intended to be public. Raw audio, full transcripts, and private source material stay outside the repo. Inputs are limited to content the operator has the right to process: own voice notes, permitted talks and lectures, and self-generated transcripts.

## What It Demonstrates

Mid-to-senior enterprise AI engineering practice in a small, operable system: private raw-data control, an OpenAI-centered quality layer, MCP-ready tools, explicit cost and quality gates, and human approval before anything is published.

## Operator Quick Start

1. Place this repo beside the private audio sandbox folder.
2. Copy `config/paths.local.example.yaml` to `config/paths.local.yaml` for machine-specific paths.
3. Keep FFmpeg portable or configured by path. Do not change the global PATH just for this app.
4. Drop audio/video or `.txt`/`.md` transcripts into the private sandbox `incoming/` folder.
5. Run a safe mock test first:

```powershell
python -m app process --input ".\tests\fixtures\sample.m4a" --mock
```

6. For a real run, configure FFmpeg, Whisper, and your OpenAI API key first. For frequent use on your own Windows account, store the key once as a user-level environment variable:

```powershell
.\scripts\set-openai-key-user.ps1
```

Then run:

```powershell
python -m app process --input "C:\path\to\recording.m4a"
```

To remove the saved key later:

```powershell
.\scripts\clear-openai-key-user.ps1
```

Core operator commands:

```powershell
.\run.ps1 tools --json
.\run.ps1 doctor --create-sandbox
.\run.ps1 process --input ".\tests\fixtures\sample.m4a" --mock
.\run.ps1 process-latest
.\run.ps1 quality --rescore
.\run.ps1 mindmap --review
.\run.ps1 research --enrich --latest
.\run.ps1 notebooklm --export --latest
.\run.ps1 publish --sanitize
.\run.ps1 exhibit --audit
```

## Architecture

```text
incoming audio/video/text transcript
  -> stable file check
  -> if media: ffmpeg normalize + Whisper transcribe + chunk/stitch when needed
  -> if text: read transcript directly
  -> detect English vs Chinese
  -> default: configured OpenAI quality model summarizes directly from source transcript in English
  -> optional: generate a full English transcript only when explicitly enabled
  -> mindmap ingest suggestion from the refined summary
  -> summary.html + web research checklist + podcast script + NotebookLM handoff package
  -> optional paid research enrichment with OpenAI web_search, citations, and richer enterprise examples
  -> private NotebookLM source export folder
  -> quality score + zero-cost local mindmap delta from summary-level text
  -> auto-apply passed deltas to the private learning graph
  -> private output package
  -> optional sanitized public-review package and public framework-map links
```

## Privacy Model

- Public: app code, docs, skills, architecture, safe examples.
- Private: raw audio, full transcripts, private source notes, local state.
- Curated public: sanitized summaries and learning reflections after human review.
- NotebookLM handoff: generated from reviewed summaries by default; raw transcripts are not uploaded unless deliberately approved for a private notebook.
- NotebookLM source export: private folder under `AI Learning Artifacts Gen NotebookLM`; not part of public GitHub output.

## GitHub Exhibit Layer

The app mirrors sanitized public-safe artifacts into:

```text
portfolio_public/
```

That folder is intended to live inside the public code repo so GitHub can show:

- the latest portfolio-safe Enterprise AI architecture and delivery framework map
- sanitized review packages
- visible progress over time through normal Git history
- current framework map and curated package history through normal Git commits

## Public Exhibit Gate

Before sharing any generated artifact, run:

```powershell
.\run.ps1 publish --sanitize
.\run.ps1 mindmap --review
.\run.ps1 exhibit --audit
```

`passed: true` means there are no public/privacy blockers. `portfolio_ready: true` means there are also no quality warnings. A review-safe draft can be useful internally, but it should not be presented as polished public learning until the audit is clean.

## Optional Research Enrichment

Daily processing keeps cost controlled by producing the transcript-derived summary first. When a learning is important enough for deeper evidence, run:

```powershell
.\run.ps1 research --enrich --latest
```

This is a paid OpenAI step. It uses the Responses `web_search` tool with configured enterprise AI vendor domains, medium search context by default, citation capture, and a report quality gate. It produces:

- `research_enriched_report.md`
- `research_enriched_report.html`
- `research_sources.json`
- `research_enrichment_status.json`
- `audio_podcast_script_research_enriched.md`

Only passed research reports are copied into sanitized public-review packages. The default research setting is intentionally budget-aware: `openai_research_search_context_size: "medium"` and `openai_research_max_output_tokens: 9000`. Raise them only for rare, high-effort research where extra latency, cost, and rate-limit risk are acceptable.

If the research command returns an OpenAI `429` rate-limit message, wait five minutes and rerun the same command. This means the account's tokens-per-minute window is still busy, not that the learning failed.

## Cross-App Showcase Standard

Every application developed in this portfolio should follow the same public-readiness pattern:

- public-safe code repo
- clear problem/solution/architecture story
- ADRs and build journal
- beginner-safe runbook
- test and audit commands
- privacy gate before publishing
- curated demo artifacts only

See `docs/github-showcase-standard.md` for the reusable checklist and maturity levels.

## Portfolio Positioning

This project signals applied enterprise AI engineering judgment: not just prompting, not platform theater, but a controlled Enterprise AI solution architecture and delivery framework with real governance.

It demonstrates:

- MCP-ready tool orchestration with CLI as a fallback
- configurable OpenAI high-reasoning learning synthesis, with optional full transcript translation
- local Whisper-compatible transcription
- agent contracts before agent work
- maker/checker separation
- manual-first autonomy
- hooks and quality gates
- ADRs and build journal
- long-term memory as repo artifacts
- privacy-preserving publishing

The public story is: **the operator designs and runs the pipeline; OpenAI and Whisper assist execution under human review, cost controls, quality gates, and privacy-preserving publishing.**

See `AGENTS.md`, `docs/real-audio-setup.md`, `docs/enterprise-readiness.md`, `docs/mcp-orchestration.md`, `docs/agent-contracts.md`, `docs/git-versioning.md`, and `docs/adr/`.
