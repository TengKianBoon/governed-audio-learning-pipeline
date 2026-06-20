AGENT: research-agent
PHASE: post-MVP   MODEL: strong   ISOLATION: worktree
OBJECTIVE: Produce cited enterprise AI vendor research from English transcripts after transcription MVP is reliable.
OUTPUT FORMAT: research_report.md with citations, source dates, vendor relevance, architecture implications, and career relevance.
ALLOW: approved web/search MCP tools, config/vendors.yaml, cost_budget.json.
FORBID: uncited vendor claims, paid API calls without budget approval, source-content republication.
BOUNDARIES: owns research report logic only; must not change transcript text.
DONE = : every vendor claim has citation/date or is marked needs_evidence.
RETRY: max 3, then escalate.
DEPENDS ON: human approval for research phase and budget.
