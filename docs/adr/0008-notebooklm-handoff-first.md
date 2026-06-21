# ADR 0008 - NotebookLM Handoff First

## Status

Accepted

## Context

The learning pipeline should eventually help convert curated summaries into deck slides, infographics, and audio explanations. NotebookLM is a strong target for this because it can work from uploaded source material and generate learning-oriented outputs, but the automation surface depends on product access, account state, and UI/API availability.

## Decision

The MVP generates a controlled `notebooklm_package/` for each learning package instead of trying to automate NotebookLM directly.

Each package includes:

- source bundle generated from the reviewed summary and mindmap placement suggestion
- 5 to 10 minute English podcast script
- deck slide prompt
- detailed infographic prompt
- audio overview prompt
- handoff instructions and human review gates

The app also generates `summary.html` and a web-research checklist so the operator can upgrade transcript-derived learning with current vendor evidence before public publishing.

## Consequences

- Public safety improves because raw audio and full transcripts stay outside the NotebookLM handoff by default.
- The workflow remains usable even if NotebookLM product controls change.
- Automation can be added later behind a human approval gate after a stable API or controlled browser flow is verified.
- GitHub readers can see the intended enterprise workflow without exposing private source material.
