from __future__ import annotations

import re

from .models import ChunkSpec, TranscriptionResult
from .utils import format_seconds


def _words(text: str) -> list[str]:
    return re.findall(r"[\w']+", text.lower(), flags=re.UNICODE)


def remove_boundary_duplicate(previous: str, current: str, max_words: int = 24) -> str:
    previous_words = _words(previous)
    current_words = _words(current)
    if not previous_words or not current_words:
        return current.strip()

    limit = min(max_words, len(previous_words), len(current_words))
    for size in range(limit, 3, -1):
        if previous_words[-size:] == current_words[:size]:
            pattern = r"^(\W*\w+\W*){" + str(size) + r"}"
            return re.sub(pattern, "", current, count=1, flags=re.UNICODE).strip()
    return current.strip()


def stitch_results(results: list[TranscriptionResult], chunks: list[ChunkSpec]) -> str:
    if len(results) == 1:
        return results[0].text.strip() + "\n"

    sections: list[str] = []
    accumulated = ""
    for result, chunk in zip(results, chunks):
        cleaned = remove_boundary_duplicate(accumulated, result.text)
        sections.append(f"## Chunk {chunk.index + 1:03d} [{format_seconds(chunk.start_seconds)}]\n\n{cleaned}")
        accumulated = f"{accumulated}\n{cleaned}".strip()
    return "\n\n".join(sections).strip() + "\n"
