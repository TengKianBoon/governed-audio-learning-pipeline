from __future__ import annotations

import json
import sys


BLOCKED_FRAGMENTS = [
    ".env",
    "outputs_private",
    "original_transcript.md",
    "english_transcribed.md",
]

BLOCKED_EXTS = (".m4a", ".mp3", ".aac", ".wav", ".amr", ".3gp", ".ogg", ".opus", ".mp4", ".mkv", ".webm", ".mov")


def main() -> int:
    payload = sys.stdin.read()
    candidates = [payload]
    try:
        data = json.loads(payload) if payload.strip() else {}
        candidates.extend(str(value) for value in data.values())
    except json.JSONDecodeError:
        pass

    haystack = "\n".join(candidates).lower()
    for fragment in BLOCKED_FRAGMENTS:
        if fragment.lower() in haystack:
            print(f"Blocked protected/private path fragment: {fragment}", file=sys.stderr)
            return 2
    if any(ext in haystack for ext in BLOCKED_EXTS):
        print("Blocked raw media write/publication attempt.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
