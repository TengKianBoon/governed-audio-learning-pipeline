from __future__ import annotations

import json
from pathlib import Path
import subprocess
import time

from .config import AppConfig
from .models import ChunkSpec
from .resilience import RetryExhausted, RetryPolicy, run_command_with_retries


SUPPORTED_AUDIO_EXTS = {".m4a", ".mp3", ".aac", ".wav", ".flac", ".amr", ".3gp", ".ogg", ".opus"}
SUPPORTED_VIDEO_EXTS = {".mp4", ".mkv", ".webm", ".mov"}
SUPPORTED_MEDIA_EXTS = SUPPORTED_AUDIO_EXTS | SUPPORTED_VIDEO_EXTS
SUPPORTED_TEXT_EXTS = {".txt", ".md"}
SUPPORTED_INPUT_EXTS = SUPPORTED_MEDIA_EXTS | SUPPORTED_TEXT_EXTS


class MediaDependencyError(RuntimeError):
    pass


def is_supported_media(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_MEDIA_EXTS


def is_supported_text(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_TEXT_EXTS


def is_supported_input(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_INPUT_EXTS


def is_video(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_VIDEO_EXTS


def wait_until_stable(path: Path, checks: int, interval_seconds: int) -> bool:
    previous = None
    stable_count = 0
    while stable_count < checks:
        current = path.stat().st_size
        if current == previous:
            stable_count += 1
        else:
            stable_count = 0
        previous = current
        if stable_count < checks:
            time.sleep(interval_seconds)
    return True


def probe_duration_seconds(path: Path, config: AppConfig) -> float | None:
    if not config.ffprobe_path:
        return None
    command = [
        config.ffprobe_path,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        return None
    try:
        payload = json.loads(completed.stdout)
        return float(payload["format"]["duration"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None


def require_ffmpeg(config: AppConfig) -> str:
    if not config.ffmpeg_path:
        raise MediaDependencyError(
            "FFmpeg is not configured. Set ffmpeg_path in config/paths.local.yaml or install a portable copy."
        )
    return config.ffmpeg_path


def normalize_to_wav(input_path: Path, output_path: Path, config: AppConfig) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        require_ffmpeg(config),
        "-y",
        "-i",
        str(input_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        str(output_path),
    ]
    try:
        run_command_with_retries(
            command,
            policy=RetryPolicy(config.max_retries, config.retry_backoff_seconds),
            failure_label="FFmpeg normalization",
        )
    except RetryExhausted as exc:
        raise MediaDependencyError(str(exc)) from exc
    return output_path


def build_chunk_plan(
    duration_seconds: float | None,
    short_limit_seconds: int = 1200,
    chunk_seconds: int = 600,
    overlap_seconds: int = 15,
) -> list[ChunkSpec]:
    if duration_seconds is None or duration_seconds <= short_limit_seconds:
        return [ChunkSpec(index=0, start_seconds=0, duration_seconds=duration_seconds or 0)]

    chunks: list[ChunkSpec] = []
    base_start = 0
    index = 0
    while base_start < duration_seconds:
        start = max(0, base_start - (overlap_seconds if index else 0))
        end = min(duration_seconds, base_start + chunk_seconds + overlap_seconds)
        chunks.append(ChunkSpec(index=index, start_seconds=start, duration_seconds=end - start))
        base_start += chunk_seconds
        index += 1
    return chunks


def split_wav(normalized_wav: Path, chunks_dir: Path, chunks: list[ChunkSpec], config: AppConfig) -> list[Path]:
    if len(chunks) == 1:
        return [normalized_wav]

    chunks_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for spec in chunks:
        output = chunks_dir / f"chunk_{spec.index:03d}.wav"
        command = [
            require_ffmpeg(config),
            "-y",
            "-ss",
            f"{spec.start_seconds:.3f}",
            "-t",
            f"{spec.duration_seconds:.3f}",
            "-i",
            str(normalized_wav),
            "-acodec",
            "copy",
            str(output),
        ]
        try:
            run_command_with_retries(
                command,
                policy=RetryPolicy(config.max_retries, config.retry_backoff_seconds),
                failure_label=f"FFmpeg chunk {spec.index}",
            )
        except RetryExhausted as exc:
            raise MediaDependencyError(str(exc)) from exc
        outputs.append(output)
    return outputs
