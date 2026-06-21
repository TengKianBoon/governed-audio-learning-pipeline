# Enterprise Readiness

This app is designed to be reviewed openly as an enterprise AI engineering portfolio project.

## OpenAI-Centered Quality Layer

- OpenAI is the approved quality provider for translation and learning synthesis in this MVP.
- Whisper remains the transcription path for audio/video files.
- API keys stay in environment variables, never in Git.
- Any higher-cost model upgrade, external research automation, or public publishing automation needs an ADR, budget check, privacy check, and human approval.

## Portability

- Private sandbox storage keeps raw learning data under user control.
- MCP-ready tools avoid shell-only orchestration.
- FFmpeg/Whisper are configured by path and can be managed without changing global machine state.
- Public code repo stays separate from private learning vault.

## Scalability

- Long audio uses chunking and stitching.
- Processing state is tracked by fingerprint.
- Agent work is contract-based and can be split into worktrees later.
- Research, NotebookLM handoff, and publishing are separate stages, so they can scale independently.

## Welfare And Safety

- Raw learning sources are private by default.
- Public outputs are sanitized and require human review.
- Retry cap prevents runaway loops.
- Cost budget files make token/API spend visible before batch processing.
- Failures are visible as pending/needs-review, not hidden.

## Hiring Signal

Reviewers should see:

- product judgment: useful MVP before automation theater
- architecture judgment: OpenAI quality layer with clear privacy and cost boundaries
- operational judgment: retries, gates, budgets, privacy
- learning judgment: ADRs, build journal, memory, and public-safe artifacts

## Target Level

Public positioning target: **mid-to-senior Enterprise AI builder**.

The evidence should show that Teng Kian Boon can design, operate, and improve AI-assisted systems with the judgment expected in enterprise AI solution architecture and deployment leadership:

- scope control before automation
- human checkpoints at risk boundaries
- cost and token discipline
- portability where it protects the user, without pretending provider choice is the main MVP value
- quality checks that can fail loudly
- private/public artifact separation
- clear operating runbooks
