from __future__ import annotations

from pathlib import Path
import os
import shutil
import subprocess

from .config import AppConfig, ensure_sandbox_dirs
from .providers import provider_policy


def _exists_executable(value: str) -> bool:
    if not value:
        return False
    try:
        if Path(value).expanduser().exists():
            return True
    except OSError:
        return False
    return shutil.which(value) is not None


def _check_command(command: str) -> bool:
    if not command:
        return False
    command_path = Path(command).expanduser()
    try:
        if command_path.exists():
            return True
    except OSError:
        return False
    parts = command.split()
    return bool(parts and _exists_executable(parts[0]))


def _next_step(
    *,
    ready_for_mock: bool,
    ready_for_real_audio: bool,
    ready_for_openai_quality: bool,
    ready_for_text_transcript: bool,
) -> str:
    if ready_for_real_audio and ready_for_openai_quality:
        return "Run one real .m4a or .txt file."
    if ready_for_text_transcript and not ready_for_real_audio:
        return "Run one .txt transcript now. Configure ffmpeg_path and ffprobe_path later for audio/video runs."
    if ready_for_real_audio and not ready_for_openai_quality:
        return "Set OPENAI_API_KEY. For frequent use, run .\\scripts\\set-openai-key-user.ps1 once."
    if ready_for_mock and not ready_for_real_audio:
        return "Configure ffmpeg_path, ffprobe_path, and Whisper before real audio/video runs."
    return "Run .\\run.ps1 doctor --create-sandbox to create required private sandbox folders."


def run_doctor(config: AppConfig, *, create_sandbox: bool = False) -> dict:
    if create_sandbox:
        ensure_sandbox_dirs(config)

    sandbox_checks = {
        "sandbox_root": config.sandbox_root.exists(),
        "incoming": config.incoming_dir.exists(),
        "processing": config.processing_dir.exists(),
        "outputs_private": config.private_outputs_dir.exists(),
        "outputs_public_review": config.public_review_dir.exists(),
        "archive_processed": config.processed_archive_dir.exists(),
        "archive_failed": config.failed_archive_dir.exists(),
    }
    dependency_checks = {
        "ffmpeg": _exists_executable(config.ffmpeg_path),
        "ffprobe": _exists_executable(config.ffprobe_path),
        "whisper_command": _check_command(config.whisper_command),
        "openai_api_key_env": bool(os.environ.get(config.openai_api_key_env, "").strip()),
    }
    policy = {
        "max_retries": config.max_retries,
        "per_task_token_budget": config.per_task_token_budget,
        "daily_token_budget": config.daily_token_budget,
        "openai_translation_model": config.openai_translation_model,
        "openai_translation_reasoning_effort": config.openai_translation_reasoning_effort,
        "openai_summary_model": config.openai_summary_model,
        "openai_summary_reasoning_effort": config.openai_summary_reasoning_effort,
        "generate_full_english_transcript": config.generate_full_english_transcript,
        "summary_route": "direct from source transcript unless full English transcript is enabled",
        "mindmap_cost": "zero; local update from summary and mindmap_ingest.md",
        "approved_provider": provider_policy(config)["architecture_positioning"]["current_default"],
        "privacy_model": "public code, private raw data, sanitized public-review outputs",
    }

    ready_for_mock = all(sandbox_checks.values())
    ready_for_real_audio = ready_for_mock and dependency_checks["ffmpeg"] and dependency_checks["ffprobe"] and dependency_checks["whisper_command"]
    ready_for_openai_quality = ready_for_mock and dependency_checks["openai_api_key_env"]
    ready_for_text_transcript = ready_for_mock and ready_for_openai_quality
    return {
        "sandbox": str(config.sandbox_root),
        "sandbox_checks": sandbox_checks,
        "dependency_checks": dependency_checks,
        "policy": policy,
        "ready_for_mock": ready_for_mock,
        "ready_for_real_audio": ready_for_real_audio,
        "ready_for_openai_quality": ready_for_openai_quality,
        "ready_for_text_transcript": ready_for_text_transcript,
        "next_step": _next_step(
            ready_for_mock=ready_for_mock,
            ready_for_real_audio=ready_for_real_audio,
            ready_for_openai_quality=ready_for_openai_quality,
            ready_for_text_transcript=ready_for_text_transcript,
        ),
    }
