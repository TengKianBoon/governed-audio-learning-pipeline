# ADR 0009 - Research Enrichment As A Paid Gate

## Status

Accepted

## Context

Daily learning capture should stay cost controlled. However, selected summaries need stronger public value: vendor/web evidence, current vocabulary, citations, examples, and enterprise practice implications.

## Decision

Research enrichment is a separate operator-triggered command:

```powershell
.\run.ps1 research --enrich --latest
```

The command uses OpenAI Responses `web_search` with configured enterprise AI vendor domains, medium search context by default, and source capture. It generates a research-enriched Markdown report, HTML report, source metadata, status JSON, and a research-enriched podcast script.

The report is copied into sanitized public-review output only when the research quality gate passes.

## Consequences

- Normal audio/text processing remains lower cost.
- Important learnings can be upgraded into citation-backed public reports.
- Vendor claims are less likely to become unsupported public statements.
- The operator can control when to spend tokens and web-search tool cost.
- If a research report is thin, uncited, or incomplete, it remains private until corrected.
- Medium search context and a 9,000-token output cap reduce rate-limit spikes; higher settings can be used only for rare high-effort reports.
