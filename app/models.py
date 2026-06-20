from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ChunkSpec:
    index: int
    start_seconds: float
    duration_seconds: float

    @property
    def end_seconds(self) -> float:
        return self.start_seconds + self.duration_seconds


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    language: str | None
    segments: list[dict]


@dataclass(frozen=True)
class ProcessingResult:
    slug: str
    private_output_dir: Path
    quality_score: int
    archived_to: Path | None
