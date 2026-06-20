---
name: mindmap-curation
description: Curate enterprise AI learning notes into the project mindmap. Use when comparing a new english_transcribed.md against mindmap/graph.json, scoring overlap/novelty, and recommending add/update/skip actions.
---

# Mindmap Curation

Compare each new learning against the existing graph before updating it.

## Workflow

1. Extract concepts, vendors, products, methods, and architecture patterns.
2. Compare against existing nodes by normalized labels.
3. Score overlap and novelty.
4. Recommend `add`, `update`, or `skip`.
5. Link the node to private artifacts and public-review artifacts separately.

## Guardrails

- Do not auto-add low-confidence claims.
- Keep private links out of public HTML.
- Human review is required before public publishing.
