---
name: enterprise-ai-research
description: Prepare cited enterprise AI vendor research from an English transcript. Use when comparing learning notes against vendors such as OpenAI, Anthropic, Palantir, Oracle, SAP, Salesforce, Microsoft, AWS, Google Cloud, Databricks, Snowflake, LangChain, Cursor, and related enterprise AI providers.
---

# Enterprise AI Research

This is a post-MVP skill. Use only after the transcript pipeline works.

## Workflow

1. Extract claims, vendors, products, architectures, and use cases from `english_transcribed.md`.
2. Read `cost_budget.json` and stay inside the approved token/API budget.
3. Search official or primary sources first.
4. Record citations and source dates.
5. Mark uncited claims as `needs_evidence`.
6. Produce `research_report.md` with sections for vendor relevance, architecture implications, and career relevance.

## Guardrails

- Do not invent vendor capabilities.
- Do not treat Y Combinator as a vendor; treat it as an ecosystem/source.
- Never state high-stakes claims without citation and date.
- Stop after 3 failed attempts and escalate instead of looping.
- Treat vendors as research subjects unless an ADR approves them as providers. ADR-0007 approves OpenAI for translation and learning synthesis in this MVP.
