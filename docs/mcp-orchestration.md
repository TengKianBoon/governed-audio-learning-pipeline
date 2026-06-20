# MCP-Oriented Orchestration

The app is designed MCP-first. The CLI remains as a beginner fallback.

## Tools

- `process_learning_audio`: process one file into private learning artifacts.
- `review_learning_mindmap`: compare English transcripts against the graph.
- `apply_reviewed_mindmap_deltas`: apply add/update deltas after human review.
- `sanitize_public_outputs`: create public-review outputs after privacy checks.
- `get_learning_app_policy`: expose retry, token budget, privacy, and autonomy defaults.
- `doctor_check`: check folders, dependencies, and readiness before real audio.

## Control Rules

- Agents should call tools through `app.mcp_tools.call_tool()` or a real MCP server adapter.
- Shell commands are for setup and human fallback, not the primary orchestration route.
- Paid AI/search tools must read `get_learning_app_policy` and each package `cost_budget.json` first.
- Human review is required before public publishing.

## Local Check

```powershell
python -m app tools --json
```

If Python is not on PATH, use the bundled Codex Python path shown in `README.md`.
