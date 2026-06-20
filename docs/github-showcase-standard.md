# GitHub Showcase Standard

This standard is the default public-presentation pattern for every application developed in this portfolio. The goal is to make real proficiency visible through working software, clear architecture, safe publishing, and honest iteration history.

## Positioning

Each application should answer four questions quickly:

- What enterprise problem does this solve?
- What architecture and delivery decisions did Teng Kian Boon make?
- What proof shows the app works and is controlled?
- What is safe for the public to inspect?

The tone should be competent, practical, and evidence-led. Avoid inflated claims. Show the work.

## Public Repo Minimum

Every public app repo should include:

- `README.md`: problem, solution, architecture, run steps, current status, roadmap.
- `AGENTS.md` or `CLAUDE.md`: operating rules, safety constraints, definition of done.
- `docs/adr/`: short architecture decision records for lasting choices.
- `docs/build-journal.md`: chronological progress notes.
- `docs/operator-runbook.md`: beginner-safe operating steps.
- `tests/`: automated checks for the core workflow.
- `.gitignore`: blocks secrets, local config, raw inputs, private outputs, and system files.
- public-safe demo artifacts or screenshots, with raw/private data withheld.

## Showcase Levels

Use these levels to decide what belongs on GitHub and what should be pinned on the profile.

| Level | Label | Meaning |
| --- | --- | --- |
| 0 | Local prototype | Runs locally, not yet public-safe. |
| 1 | Public-safe repo | Code/docs can be public; no private data or secrets. |
| 2 | Portfolio-ready | Has tests, audit, architecture docs, and public-safe demo output. |
| 3 | Profile-pinned | Strong enough to represent current professional positioning. |

Do not pin Level 0 or Level 1 projects. Level 2 can be public. Level 3 should be pinned only when the README, demo artifact, and test/audit story are polished.

## Evidence To Show

Each project should visibly demonstrate at least five of these:

- architecture diagram or framework map
- MCP-ready or API-first interface
- cost/retry controls
- privacy and publishing gates
- test suite and audit command
- human-in-the-loop checkpoints
- clear provider choices and tradeoffs
- versioned build journal
- ADR discipline
- public-safe demo package
- cleanup and lifecycle policy
- roadmap with next professional improvements

## Publishing Gate

Before public sharing:

1. Run tests.
2. Run the app-specific public audit.
3. Check `git status --short`.
4. Confirm no raw audio, private transcripts, `.env`, local config, API keys, or `desktop.ini`.
5. Open the public demo page locally and click through at least two layers.
6. Commit only public-safe code, docs, tests, and curated artifacts.

## Profile Strategy

The GitHub profile should eventually point to:

- one profile README with a short portfolio map
- pinned repos for the strongest 3 to 6 applications
- each pinned repo showing a distinct capability area

Recommended capability buckets:

- Enterprise AI solution architecture
- AI workflow automation
- MCP / tool orchestration
- data and document automation
- quality gates and governance
- portfolio/public publishing systems

## This Project's Current Role

This app should be positioned as the first flagship system:

**Enterprise AI Solutions Architecturing and Framework**

It demonstrates local transcription, OpenAI-assisted synthesis, quality gates, cost controls, privacy-preserving publishing, MCP-ready orchestration, and an evolving public solutions framework map.
