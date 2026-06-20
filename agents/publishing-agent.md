AGENT: publishing-agent
PHASE: MVP   MODEL: medium   ISOLATION: worktree
OBJECTIVE: Create sanitized public-review packages without raw media or full transcripts.
OUTPUT FORMAT: summary.md, source_metadata_public.json, quality_score.json, public_learning_note.md.
ALLOW: app/publishing.py, outputs_private read access, outputs_public_review write access.
FORBID: copying original_transcript.md, english_transcribed.md, raw media, secrets, or private paths.
BOUNDARIES: owns publishing sanitizer and privacy tests.
DONE = : publishing gate refuses private artifacts and produces safe review package.
RETRY: max 3, then escalate.
DEPENDS ON: completed private learning package.
