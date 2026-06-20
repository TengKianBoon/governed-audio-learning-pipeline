AGENT: media-transcription-agent
PHASE: MVP   MODEL: medium   ISOLATION: worktree
OBJECTIVE: Convert supported audio/video into private original and English transcripts without modifying originals.
OUTPUT FORMAT: source_metadata.json, original_transcript.md, english_transcribed.md, cost_budget.json.
ALLOW: app media/transcription modules, FFmpeg path, Whisper command, private sandbox.
FORBID: global PATH changes, raw public publishing, editing unrelated docs.
BOUNDARIES: owns app/media.py, app/transcription.py, and transcription tests.
DONE = : short audio, video extraction path, and 2-hour chunk plan tests pass.
RETRY: max 3, reflect on exact failure, escalate on 3rd fail.
DEPENDS ON: config/paths.yaml.
