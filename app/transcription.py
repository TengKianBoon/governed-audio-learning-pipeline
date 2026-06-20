from __future__ import annotations

import json
import os
from pathlib import Path
import shlex
import subprocess

from .config import AppConfig
from .models import TranscriptionResult
from .resilience import RetryExhausted, RetryPolicy, run_command_with_retries


class TranscriptionDependencyError(RuntimeError):
    pass


def _command_parts(command: str) -> list[str]:
    if not command:
        return []
    path = Path(command).expanduser()
    if path.exists():
        return [str(path)]
    return shlex.split(command)


def mock_transcribe(audio_path: Path, task: str, index: int | None = None) -> TranscriptionResult:
    label = f" chunk {index + 1}" if index is not None else ""
    if task == "translate":
        text = (
            f"Mock English transcript for{label} {audio_path.stem}. "
            "Key ideas: enterprise AI, agent orchestration, quality gates, and learning workflows."
        )
        return TranscriptionResult(text=text, language="en", segments=[])
    text = (
        f"Mock original-language transcript for{label} {audio_path.stem}. "
        "This placeholder proves the private pipeline without using external tools."
    )
    return TranscriptionResult(text=text, language="zh", segments=[])


def run_whisper(
    audio_path: Path,
    output_dir: Path,
    config: AppConfig,
    task: str,
    model: str,
    index: int | None = None,
    mock: bool = False,
) -> TranscriptionResult:
    if mock:
        return mock_transcribe(audio_path, task=task, index=index)

    command = _command_parts(config.whisper_command)
    if not command:
        raise TranscriptionDependencyError("Whisper command is not configured.")

    output_dir.mkdir(parents=True, exist_ok=True)
    args = [
        *command,
        str(audio_path),
        "--task",
        task,
        "--model",
        model,
        "--output_format",
        "json",
        "--output_dir",
        str(output_dir),
        "--verbose",
        "False",
    ]
    try:
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        completed = run_command_with_retries(
            args,
            policy=RetryPolicy(config.max_retries, config.retry_backoff_seconds),
            failure_label=f"Whisper {task}",
            env=env,
        )
    except RetryExhausted as exc:
        raise TranscriptionDependencyError(str(exc)) from exc

    log_prefix = f"whisper_{task}_{index if index is not None else 0}"
    (output_dir / f"{log_prefix}.stdout.log").write_text(completed.stdout or "", encoding="utf-8")
    (output_dir / f"{log_prefix}.stderr.log").write_text(completed.stderr or "", encoding="utf-8")

    json_files = sorted(output_dir.glob(f"{audio_path.stem}*.json"))
    if not json_files:
        json_files = sorted(
            path
            for path in output_dir.glob("*.json")
            if path.stat().st_mtime >= audio_path.stat().st_mtime
        )
    if not json_files:
        txt_files = sorted(output_dir.glob(f"{audio_path.stem}*.txt"))
        if not txt_files:
            txt_files = sorted(
                path
                for path in output_dir.glob("*.txt")
                if path.stat().st_mtime >= audio_path.stat().st_mtime
            )
        if txt_files:
            return TranscriptionResult(text=txt_files[-1].read_text(encoding="utf-8"), language=None, segments=[])
        available = ", ".join(path.name for path in sorted(output_dir.glob("*"))) or "none"
        raise TranscriptionDependencyError(
            "Whisper completed but did not produce a readable output file. "
            f"Checked {output_dir}. Available files: {available}"
        )

    payload = json.loads(json_files[-1].read_text(encoding="utf-8"))
    return TranscriptionResult(
        text=str(payload.get("text", "")).strip(),
        language=payload.get("language"),
        segments=list(payload.get("segments", [])),
    )
