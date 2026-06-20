---
name: transcribe-audio
description: Transcribe local phone recordings or video-derived audio for the Enterprise AI Learning Audio App. Use when processing .m4a, .mp3, .wav, .mp4, or long seminar files into original-language transcript markdown with timestamps and privacy-safe metadata.
---

# Transcribe Audio

Use the app CLI or media/transcription modules; do not overwrite originals.

## Workflow

1. Confirm the input extension is supported.
2. Probe duration with FFprobe when available.
3. Normalize with FFmpeg to mono 16kHz wav under `processing/`.
4. If duration is over 20 minutes, chunk into 10-minute parts with 10-15 second overlap.
5. Run Whisper transcription on each unit.
6. Stitch chunks with timestamps.
7. Write `original_transcript.md` and `source_metadata.json`.

## Guardrails

- Keep raw audio and full transcript in private output only.
- Mark dependency failures as `pending`, never fabricate transcript text.
- Retry max 3, then escalate.
