# Enterprise AI Learning Audio App

Pipeline for turning Chinese and English voice recordings, local YouTube videos, or phone-generated `.txt` transcripts into learning artifacts:

- original-language transcript
- English markdown transcript
- OpenAI GPT quality summary and quality score
- mindmap delta review
- sanitized public-review package

The code repo is intended to be public. Raw audio, private transcripts, and source learning material stay outside the repo.

## Operator Quick Start

This repo is designed to be simple to operate while demonstrating mid-to-senior enterprise AI engineering practice: private raw-data control, OpenAI-centered quality synthesis, MCP-ready tools, explicit cost/quality gates, and human approval before public publishing.

1. Put this repo beside the private audio sandbox folder.
2. Copy `config/paths.local.example.yaml` to `config/paths.local.yaml` for machine-specific paths.
3. Keep FFmpeg portable or configured by path. Do not change global PATH just for this app.
4. Drop audio/video or `.txt`/`.md` transcripts into the private sandbox `incoming/` folder.
5. Run a safe mock test first:

```powershell
python -m app process --input ".\tests\fixtures\sample.m4a" --mock
```

6. For a real run, configure FFmpeg, Whisper, and your OpenAI API key first. For frequent use on your own Windows account, store it once as a user-level environment variable:

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

Use the one-session prompt method in `docs/real-audio-setup.md` on shared machines or when you want maximum caution.

Core operator commands:

```powershell
.\run.ps1 tools --json
.\run.ps1 doctor --create-sandbox
.\run.ps1 process --input ".\tests\fixtures\sample.m4a" --mock
.\run.ps1 process-latest
.\run.ps1 quality --rescore
.\run.ps1 mindmap --review
.\run.ps1 publish --sanitize
.\run.ps1 exhibit --audit
```

Direct Python commands remain available for debugging:

```powershell
python -m app tools --json
python -m app process --input "C:\path\to\file.m4a"
python -m app watch --folder "C:\path\to\incoming" --once
python -m app mindmap --review
python -m app publish --sanitize
python -m app exhibit --audit
python tests\score.py
```

If `python` is not recognized on this machine, use the bundled Codex Python executable:

```powershell
& "C:\Users\User\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m app process --input ".\tests\fixtures\sample.m4a" --mock
```

## Architecture

```text
incoming audio/video/text transcript
  -> stable file check
  -> if media: ffmpeg normalize + Whisper transcribe + chunk/stitch when needed
  -> if text: read transcript directly
  -> detect English vs Chinese
  -> default: OpenAI gpt-5.4-mini summarizes directly from source transcript in English
  -> optional: generate a full English transcript only when explicitly enabled
  -> mindmap ingest suggestion from the refined summary
  -> quality score + zero-cost local mindmap delta from summary-level text
  -> auto-apply passed deltas to the private learning graph
  -> private output package
  -> optional sanitized public-review package and public mindmap links
```

## Privacy Model

- Public: app code, docs, skills, architecture, safe examples.
- Private: raw audio, full transcripts, private source notes, local state.
- Curated public: sanitized summaries and learning reflections after human review.

## GitHub Exhibit Layer

The app now mirrors sanitized public-safe artifacts into:

```text
portfolio_public/
```

That folder is intended to live inside the public code repo so GitHub can show:

- the latest portfolio-safe Enterprise AI solutions framework map
- sanitized review packages
- visible progress over time through normal Git history
- mindmap snapshots under `portfolio_public/mindmap/history/`

## Public Exhibit Gate

Before sharing any generated artifact, run:

```powershell
.\run.ps1 publish --sanitize
.\run.ps1 mindmap --review
.\run.ps1 exhibit --audit
```

`passed: true` means there are no public/privacy blockers. `portfolio_ready: true` means there are also no quality warnings. A review-safe draft can be useful internally, but it should not be presented as polished public learning until the audit is clean.

After `publish --sanitize`, the repo-side exhibit mirror is refreshed automatically.

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

This project is intentionally built to signal level-7.5 engineering judgment: not just prompting, not over-engineered platform theater, but a controlled Enterprise AI solutions architecture framework with real governance.

It demonstrates:

- MCP-ready tool orchestration with CLI as a fallback
- OpenAI gpt-5.4-mini high-reasoning learning synthesis, with optional full transcript translation
- local Whisper-compatible transcription
- agent contracts before agent work
- maker/checker separation
- manual-first autonomy
- hooks and quality gates
- ADRs and build journal
- long-term memory as repo artifacts
- privacy-preserving publishing

The public story is: **Teng Kian Boon designed and operates the learning pipeline; OpenAI and Whisper assist execution under human review, cost controls, quality gates, and privacy-preserving publishing.**

See `AGENTS.md`, `docs/real-audio-setup.md`, `docs/enterprise-readiness.md`, `docs/mcp-orchestration.md`, `docs/agent-contracts.md`, `docs/git-versioning.md`, and `docs/adr/`.
