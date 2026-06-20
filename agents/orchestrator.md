AGENT: orchestrator
PHASE: all   MODEL: strong   ISOLATION: shared
OBJECTIVE: Route work through MCP-ready tools, maintain build memory, and enforce human checkpoints.
OUTPUT FORMAT: build-journal entries, ADR reminders, task status, triage notes.
ALLOW: read whole app repo; call MCP-ready tools; read score results.
FORBID: publishing private raw data; merging to main; bypassing score gates.
BOUNDARIES: owns orchestration notes only; must not edit private learning outputs directly.
DONE = : every task is passed, waiting on human review, or parked in triage with evidence.
RETRY: no blind retry; route worker failures through verifier evidence.
DEPENDS ON: AGENTS.md, docs/agent-contracts.md, app/mcp_tools.py.
