# Learning Lifecycle And Cleanup Policy

This project should grow like a curated knowledge system, not like a folder that keeps every intermediate file forever.

## Principles

- Keep the mindmap as the durable learning layer.
- Keep raw audio, full transcripts, and machine drafts private.
- Add only useful deltas to the public flow map.
- Preserve enough evidence to audit why a learning was added.
- Clean with a dry-run first; never silently delete learning evidence.

## Lifecycle Stages

1. Intake
   - New audio, video, or transcript lands in `incoming/`.
   - The app fingerprints the source so exact repeats can be detected.

2. Processing
   - Audio/video is normalized and transcribed.
   - Text transcripts skip Whisper and go directly to language detection.
   - The summary step produces the human-readable learning note and `mindmap_ingest.md`.

3. Delta Review
   - The mindmap update uses `summary.md` plus `mindmap_ingest.md`, not the raw transcript.
   - Exact or near-duplicate learnings should reinforce existing topics instead of creating new topics.
   - New concepts should be added only when they improve coverage, accuracy, or operational clarity.

4. Public Exhibit
   - Only quality-passed, sanitized packages are linked from the public flow map.
   - Failed packages may remain privately for troubleshooting, but they should not be exposed as public evidence.

5. Retention And Cleanup
   - Keep the latest public flow map and versioned snapshots.
   - Keep the private graph and registries permanently unless deliberately migrated.
   - Move processed source files to `archive/processed/` after successful runs when `--archive` is used.
   - Remove development/sample packages from public outputs automatically.
   - Review failed packages weekly; rerun, fix, or archive them.

## Recommended Retention Defaults

- `incoming/`: empty after processing.
- `processing/`: safe to clean after successful publish; keep recent failed run logs for 14 days.
- `archive/processed/`: keep locally for 30 to 90 days, then move to cold storage or delete after confirming the summary and mindmap entry are good.
- `outputs_private/learnings/`: keep high-quality packages; compress or move older private packages after 90 days if public summaries and graph evidence are sufficient.
- `outputs_public_review/`: keep only quality-passed public packages plus any intentionally retained historical package. Remove failed or sample packages from public review output.
- `portfolio_public/mindmap/history/`: keep weekly or milestone snapshots, not every single publish forever.

## Duplicate And Delta Rules

- Exact duplicate file fingerprint: do not create a new learning package unless forced.
- Same topic, no new insight: add evidence count or `last_seen`, but do not add a new public concept.
- Same topic, better explanation: update the existing concept with the newer package as latest evidence.
- Conflicting claim: mark as `needs_review`; do not auto-overwrite the mindmap.
- Truly new concept: add a new node, link it to the relevant process stage, and record the source package.

## Automation Backlog

- Use `clean --dry-run` to report removable processing files, failed packages, stale public outputs, duplicate private packages, and large archive files.
- Add `clean --apply` only after the dry-run report is trusted and reviewed.
- Add semantic duplicate scoring against prior summaries.
- Add graph fields for `confidence`, `evidence_count`, `last_seen`, and `status`.
- Add monthly mindmap compaction: merge weak topics into stronger canonical concepts.

## Dry-Run Command

```powershell
powershell -ExecutionPolicy Bypass -File .\run.ps1 clean --dry-run
```

Optional stricter review:

```powershell
powershell -ExecutionPolicy Bypass -File .\run.ps1 clean --dry-run --processing-days 1 --archive-mb 100
```

The command prints JSON only. It does not delete or move files.
