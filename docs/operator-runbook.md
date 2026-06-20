# Operator Runbook

This runbook is intentionally easy to follow, but it is not positioned as a beginner project. It documents an operator-safe workflow for a public Enterprise AI learning portfolio.

## Positioning

Target public signal: **level 7.5/10 enterprise AI builder**.

What this should demonstrate:

- Practical system design, not just prompt usage.
- Local-first privacy control over raw learning data.
- OpenAI-centered quality synthesis with clear cost controls.
- MCP-ready orchestration instead of shell-only automation.
- Human-in-the-loop gates for publishing and portfolio quality.
- Retry, cost, quality, and privacy controls from day one.
- Build-in-public evidence through ADRs, tests, score gates, and sanitized artifacts.

For duplicate handling, retention, and cleanup policy, see `docs/learning-lifecycle.md`.

## Operating Workflow

1. Open the app code folder:

```powershell
cd "C:\Leon G Drive\A Daily Routine\AI Learnings\enterprise-ai-learning-audio-app"
```

2. Check readiness:

```powershell
.\run.ps1 doctor --create-sandbox
```

Expected:

```text
ready_for_mock: true
ready_for_real_audio: true
```

3. Set the OpenAI API key.

Persistent setup for frequent use on your own secured Windows account:

```powershell
.\scripts\set-openai-key-user.ps1
```

Maximum-caution one-session mode:

```powershell
$secureKey = Read-Host "Paste OpenAI API key" -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToCoTaskMemUnicode($secureKey)
try {
  $env:OPENAI_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringUni($ptr)
} finally {
  [Runtime.InteropServices.Marshal]::ZeroFreeCoTaskMemUnicode($ptr)
}
Remove-Variable secureKey, ptr -ErrorAction SilentlyContinue
```

Keep the key out of `config/paths.local.yaml`, screenshots, chat messages, and Git.

To remove a saved key later:

```powershell
.\scripts\clear-openai-key-user.ps1
```

4. Place one audio/video file or phone transcript file in the private sandbox:

```text
C:\Leon G Drive\A Daily Routine\AI Learnings Audio App\incoming
```

Supported text transcript files:

```text
.txt, .md
```

Supported media files still include Samsung/Xiaomi-style `.m4a` and YouTube `.mp4`.

5. Process the newest incoming file:

```powershell
.\run.ps1 process-latest
```

6. Re-run quality scoring when templates or quality rules change:

```powershell
.\run.ps1 quality --rescore
```

7. Review private artifacts:

```text
C:\Leon G Drive\A Daily Routine\AI Learnings Audio App\outputs_private\learnings
```

8. Create sanitized public-review outputs:

```powershell
.\run.ps1 publish --sanitize
```

This now also refreshes the GitHub-safe exhibit mirror inside the repo:

```text
portfolio_public/
```

It also refreshes public mindmap links for sanitized packages. The private graph is already updated automatically after a learning package passes quality.

9. Optional: review or backfill mindmap updates:

```powershell
.\run.ps1 mindmap --review
.\run.ps1 mindmap --apply-reviewed
```

10. Audit the public exhibit:

```powershell
.\run.ps1 exhibit --audit
```

Expected for public sharing:

```text
passed: true
portfolio_ready: true
blockers: 0
warnings: 0
```

If `passed` is false, do not share because a privacy or public-safety blocker exists.
If `portfolio_ready` is false, the files may be review-safe but still show quality warnings.

11. Open the mindmap:

```powershell
explorer "C:\Leon G Drive\A Daily Routine\AI Learnings Audio App\mindmap"
```

12. Optional cleanup planning:

```powershell
powershell -ExecutionPolicy Bypass -File .\run.ps1 clean --dry-run
```

This reports cleanup candidates only. It does not delete files.

12. Open the repo-side public exhibit:

```powershell
explorer "C:\Leon G Drive\A Daily Routine\AI Learnings\enterprise-ai-learning-audio-app\portfolio_public"
```

## Quality Gates

Do not publish if:

- `quality_score.json` says `passed: false`.
- `transcript_findings` is not empty.
- `cost_budget.json` says `budget_status: warn` and a paid AI/search stage is planned.
- The output includes raw audio, full transcripts, private paths, copyrighted long excerpts, or secrets.
- The summary does not reflect your own understanding.
- `.\run.ps1 exhibit --audit` reports blockers or warnings.

## Senior-Level Review Checklist

Before sharing publicly, confirm the artifact shows:

- What the learning is about.
- Why it matters for Enterprise AI, solution architecture, deployment engineering, or AI operations.
- Whether the input was audio/video or a phone-generated transcript.
- Whether Chinese content was translated to English before summary.
- What changed in your operating model.
- Which claims are evidence-backed and which still need research.
- How it fits the mindmap.
- What you would do next as an implementation or architecture improvement.

## Language For Public Portfolio

Use:

```text
Built by Teng Kian Boon.
OpenAI-assisted, human-reviewed.
Private raw data, public curated learning.
```

Avoid:

```text
Made by ChatGPT.
Fully automated without review.
Raw transcript dump.
```

The goal is not to hide AI use. The goal is to show that AI is part of a governed engineering system that you designed, operated, and improved.
