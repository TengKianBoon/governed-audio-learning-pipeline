# Hooks

Hooks are the deterministic safeguard layer. They enforce the rules that future agents may forget.

| Event | Script | Safeguard |
|---|---|---|
| PreToolUse Edit/Write | `block_protected_paths.py` | blocks secrets, raw media, and private transcript publication |
| PreToolUse Bash | `guard_command.py` | blocks destructive commands and global FFmpeg/PATH mutation |
| PostToolUse Edit/Write | `run_checks.py` | runs the test suite |
| Stop/SubagentStop | `verify_score.py` | blocks done if score is below 80 |

The app also writes `cost_budget.json` per learning package so future paid AI/search stages have a visible budget gate.
