# Git Versioning

This project is designed as a public code repo, separate from private raw learning data.

## App Code Repo

Run these inside `enterprise-ai-learning-audio-app` when your environment allows Git metadata writes:

```powershell
git init -b main
git add .
git commit -m "chore: scaffold enterprise ai learning audio app"
```

Publish this repo publicly only after checking:

```powershell
git status --short
git diff --cached --name-only
```

Do not commit:

- raw audio or video
- `outputs_private/`
- full transcripts
- `.env`
- `config/paths.local.yaml`

## Learning Portfolio Repo

The app now maintains a GitHub-safe mirror inside this repo:

```text
portfolio_public/
```

Use that folder as the versioned exhibit layer for sanitized learning outputs and the evolving Enterprise AI solutions framework map.

Recommended Git workflow:

```powershell
.\run.ps1 publish --sanitize
.\run.ps1 mindmap --review
.\run.ps1 exhibit --audit
git add portfolio_public README.md docs
git commit -m "docs: refresh portfolio exhibit"
```

If you later split learnings into a separate curated repo, use `portfolio_public/` as the source, not `outputs_private/`.

## Private Raw Vault

Keep the audio sandbox private:

```text
C:\Leon G Drive\A Daily Routine\AI Learnings Audio App
```

Do not initialize this folder as a public repo.
