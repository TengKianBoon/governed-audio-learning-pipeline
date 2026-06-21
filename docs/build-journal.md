# Build Journal

## 2026-06-20 - Phase 0 Scaffold

- Did: created the public app repo structure, constitution, ADRs, local skills, MCP-ready tool layer, CLI fallback, provider-neutral policy, privacy gates, retry caps, cost-budget guard, and test harness.
- Why notable: the project starts with the same enterprise AI operating discipline it aims to showcase.
- Decisions: ADR-0001 through ADR-0006 accepted.
- Next: configure FFmpeg/Whisper paths and run the first real audio file through the pipeline.

## 2026-06-20 - Text Ingestion And OpenAI Quality Layer

- Did: added `.txt`/`.md` transcript ingestion, language detection, English-skip logic, OpenAI translation for Chinese/unknown text, and GPT-family high-reasoning quality summaries before mindmap evaluation.
- Why notable: the pipeline now matches the real Google Drive intake pattern from phone recorders and phone-generated transcripts.
- Decisions: ADR-0007 accepted; OpenAI is the approved MVP quality provider while raw learning data stays private.
- Next: run one real phone transcript and one real `.m4a`, then review public summaries before publishing.

## 2026-06-20 - Mini Cost Route And Summary-First Mindmap

- Did: split OpenAI settings into translation and summary models, set the daily route to `gpt-5.4-mini`, kept summary reasoning high, added `mindmap_ingest.md`, and kept mindmap updates local/free.
- Why notable: this protects cost while improving portfolio-quality learning summaries and giving the flow map cleaner placement guidance.
- Decisions: mindmap deltas come from `summary.md` plus `mindmap_ingest.md`, not raw transcripts.
- Next: run one real `.txt` transcript again and inspect the new summary, mindmap ingest suggestion, and public review package.

## 2026-06-20 - Direct Summary Cost Optimization

- Did: made full English transcript generation optional and off by default; Chinese/English source transcripts now feed directly into the English summary step.
- Why notable: routine learnings avoid a separate translation call and avoid re-ingesting a generated English transcript.
- Decisions: `english_transcribed.md` becomes a private route note when the full transcript is skipped; `summary.md` remains the main human-readable learning artifact.
- Next: run the same `.txt` transcript and compare cost budget, summary quality, and mindmap placement.

## 2026-06-20 - Deep Summary Prompt Tuning

- Did: strengthened the direct-summary prompt to require a comprehensive learning note, concept table, richer scenarios, implementation implications, quality gates, and follow-up research questions.
- Why notable: this aims to recover the depth of the earlier two-call translation-plus-summary route while preserving the lower-cost one-call summary route.
- Decisions: keep `generate_full_english_transcript: false` as the daily default; spend the saved translation budget on a more detailed summary output.
- Next: rerun the same `.txt` transcript and compare the new summary against `summary1.md` and `summary2.md`.

## 2026-06-20 - Summary Completeness Gate

- Did: added summary quality checks for substantial source transcripts: required sections, minimum depth, concept-table rows, scenario subsections, follow-up questions, and mindmap placement cues.
- Why notable: thin or incomplete summaries can no longer quietly pass as public-exhibit ready artifacts.
- Decisions: `Mindmap Ingest Suggestion` must include Category, Fits, Before, and After cues so the process-flow map receives clear placement guidance.
- Next: rerun the transcript; if the summary still fails, inspect `quality_score.json` for exact completeness findings before publishing.

## 2026-06-20 - Continuous Mindmap Update

- Did: made passed learning packages auto-apply their mindmap deltas to the private learning graph; `publish --sanitize` now refreshes public mindmap links after sanitized packages exist.
- Why notable: the Enterprise AI architecture and delivery framework map now grows over time as new knowledge feeds are processed, while public links remain gated by the sanitizer.
- Decisions: failed or incomplete packages do not auto-add to the graph; public portfolio links appear only after sanitized publishing.
- Next: use `mindmap --apply-reviewed` only as a backfill/repair command for older packages.

## 2026-06-20 - GitHub Showcase Standard

- Did: added a reusable GitHub showcase standard for every application in the portfolio.
- Why notable: future apps can be presented consistently through architecture, tests, ADRs, build journal, privacy gates, and curated public demo artifacts.
- Decisions: public profile readiness is evidence-led; only polished Level 3 projects should be pinned, while earlier public-safe work can remain visible as progress.
- Next: use this standard before publishing or pinning each new app.

## 2026-06-20 - HTML Summary and NotebookLM Handoff

- Did: added `summary.html`, web-research checklists, 5 to 10 minute podcast scripts, and a `notebooklm_package/` for each processed learning.
- Why notable: each learning can now move from transcript-derived synthesis toward vendor-verified research and multimedia learning artifacts without exposing raw private transcripts.
- Decisions: NotebookLM stays human-in-the-loop for now; the app prepares upload-ready prompts and source bundles instead of assuming stable automatic NotebookLM control.
- Next: run a fresh audio or `.txt` file, open `summary.html`, click the research checklist, and inspect the NotebookLM handoff folder before public publishing.

## 2026-06-20 - Paid Research Enrichment Gate

- Did: added `research --enrich --latest` to turn a private summary into a web-search-backed research report with citations, evidence table, richer examples, status JSON, and a research-enriched podcast script.
- Why notable: public learning can now be upgraded from transcript-derived synthesis into an evidence-backed enterprise AI architecture and delivery report.
- Decisions: enrichment is not automatic; it uses OpenAI web search only when the operator deliberately chooses to spend tokens and tool cost.
- Next: run one mock enrichment, then one real enrichment on a selected learning and inspect `research_enrichment_status.json` before publishing.

## 2026-06-21 - NotebookLM Source Export Folder

- Did: added automatic private export to `AI Learning Artifacts Gen NotebookLM`, plus `notebooklm --export --latest` for backfilling older learning packages.
- Why notable: NotebookLM now receives exactly the operator-approved source set: original transcript, Markdown summary, and HTML summary.
- Decisions: the NotebookLM source export is private and separate from public GitHub output.
- Next: process one new file and confirm a `{slug} NLM` folder appears with the three source files.
