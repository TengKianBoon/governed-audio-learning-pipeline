from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _parse_value(raw: str):
    value = raw.strip()
    if not value:
        return ""
    if value[0:1] in {"'", '"'} and value[-1:] == value[0]:
        return value[1:-1]
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def read_simple_yaml(path: Path) -> dict:
    data: dict = {}
    if not path.exists():
        return data
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, value = stripped.lstrip("\ufeff").split(":", 1)
        data[key.strip()] = _parse_value(value)
    return data


@dataclass(frozen=True)
class AppConfig:
    sandbox_root: Path
    portfolio_public_root: Path
    portfolio_owner: str
    portfolio_initials: str
    portfolio_tagline: str
    ffmpeg_path: str
    ffprobe_path: str
    whisper_command: str
    whisper_model: str
    translation_model: str
    storage_provider: str
    transcription_provider: str
    translation_provider: str
    summary_provider: str
    research_provider: str
    generate_full_english_transcript: bool
    auto_apply_mindmap_delta: bool
    openai_api_key_env: str
    openai_quality_model: str
    openai_reasoning_effort: str
    openai_max_output_tokens: int
    openai_translation_model: str
    openai_translation_reasoning_effort: str
    openai_translation_max_output_tokens: int
    openai_summary_model: str
    openai_summary_reasoning_effort: str
    openai_summary_max_output_tokens: int
    openai_request_timeout_seconds: int
    short_file_limit_seconds: int
    chunk_seconds: int
    chunk_overlap_seconds: int
    file_stability_checks: int
    file_stability_interval_seconds: int
    max_retries: int
    retry_backoff_seconds: int
    daily_token_budget: int
    per_task_token_budget: int
    budget_warning_ratio: float

    @property
    def incoming_dir(self) -> Path:
        return self.sandbox_root / "incoming"

    @property
    def processing_dir(self) -> Path:
        return self.sandbox_root / "processing"

    @property
    def private_outputs_dir(self) -> Path:
        return self.sandbox_root / "outputs_private"

    @property
    def public_review_dir(self) -> Path:
        return self.sandbox_root / "outputs_public_review"

    @property
    def processed_archive_dir(self) -> Path:
        return self.sandbox_root / "archive" / "processed"

    @property
    def failed_archive_dir(self) -> Path:
        return self.sandbox_root / "archive" / "failed"

    @property
    def state_dir(self) -> Path:
        return self.sandbox_root / "state"

    @property
    def mindmap_dir(self) -> Path:
        return self.sandbox_root / "mindmap"


def resolve_path(raw: str | Path, base: Path | None = None) -> Path:
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path
    return (base or repo_root()).joinpath(path).resolve()


def resolve_executable(value: str, fallback_name: str) -> str:
    root = repo_root()
    local_candidates = (
        root / ".venv" / "Scripts" / f"{fallback_name}.exe",
        root / ".venv" / "Scripts" / fallback_name,
        root / ".venv" / "bin" / fallback_name,
    )
    if value:
        configured = Path(value).expanduser()
        try:
            if configured.exists():
                return str(configured)
        except OSError:
            return str(configured)
        repo_relative = root / configured
        try:
            if repo_relative.exists():
                return str(repo_relative)
        except OSError:
            return str(repo_relative)
        if not any(separator in value for separator in ("\\", "/")):
            for candidate in local_candidates:
                if candidate.exists():
                    return str(candidate)
        found = shutil.which(value)
        if found:
            return found
        return value
    found = shutil.which(fallback_name)
    if found:
        return found
    for candidate in local_candidates:
        if candidate.exists():
            return str(candidate)
    return ""


def load_config(config_path: str | Path | None = None) -> AppConfig:
    root = repo_root()
    merged = read_simple_yaml(root / "config" / "paths.yaml")
    merged.update(read_simple_yaml(root / "config" / "paths.local.yaml"))
    if config_path:
        merged.update(read_simple_yaml(Path(config_path)))

    sandbox_root = resolve_path(str(merged.get("sandbox_root", "local_sandbox")), root)
    legacy_quality_model = str(merged.get("openai_quality_model", "gpt-5.4-mini"))
    legacy_reasoning_effort = str(merged.get("openai_reasoning_effort", "high"))
    legacy_max_output_tokens = int(merged.get("openai_max_output_tokens", 12000))

    translation_model_name = str(merged.get("openai_translation_model", legacy_quality_model))
    translation_reasoning_effort = str(merged.get("openai_translation_reasoning_effort", "low"))
    translation_max_output_tokens = int(merged.get("openai_translation_max_output_tokens", 6000))
    summary_model_name = str(merged.get("openai_summary_model", legacy_quality_model))
    summary_reasoning_effort = str(merged.get("openai_summary_reasoning_effort", legacy_reasoning_effort))
    summary_max_output_tokens = int(merged.get("openai_summary_max_output_tokens", legacy_max_output_tokens))

    return AppConfig(
        sandbox_root=sandbox_root,
        portfolio_public_root=resolve_path(str(merged.get("portfolio_public_root", "portfolio_public")), root),
        portfolio_owner=str(merged.get("portfolio_owner", "Teng Kian Boon")),
        portfolio_initials=str(merged.get("portfolio_initials", "TKB")),
        portfolio_tagline=str(
            merged.get(
                "portfolio_tagline",
                "Enterprise AI solutions architecturing and framework built with OpenAI-assisted synthesis, operator review, cost controls, and privacy-preserving publishing.",
            )
        ),
        ffmpeg_path=resolve_executable(str(merged.get("ffmpeg_path", "")), "ffmpeg"),
        ffprobe_path=resolve_executable(str(merged.get("ffprobe_path", "")), "ffprobe"),
        whisper_command=resolve_executable(str(merged.get("whisper_command", "")), "whisper"),
        whisper_model=str(merged.get("whisper_model", "small")),
        translation_model=str(merged.get("translation_model", "medium")),
        storage_provider=str(merged.get("storage_provider", "local-filesystem")),
        transcription_provider=str(merged.get("transcription_provider", "local-whisper-compatible-cli")),
        translation_provider=str(merged.get("translation_provider", "openai-responses")),
        summary_provider=str(merged.get("summary_provider", "openai-responses")),
        research_provider=str(merged.get("research_provider", "none-until-approved")),
        generate_full_english_transcript=bool(merged.get("generate_full_english_transcript", False)),
        auto_apply_mindmap_delta=bool(merged.get("auto_apply_mindmap_delta", True)),
        openai_api_key_env=str(merged.get("openai_api_key_env", "OPENAI_API_KEY")),
        openai_quality_model=summary_model_name,
        openai_reasoning_effort=summary_reasoning_effort,
        openai_max_output_tokens=summary_max_output_tokens,
        openai_translation_model=translation_model_name,
        openai_translation_reasoning_effort=translation_reasoning_effort,
        openai_translation_max_output_tokens=translation_max_output_tokens,
        openai_summary_model=summary_model_name,
        openai_summary_reasoning_effort=summary_reasoning_effort,
        openai_summary_max_output_tokens=summary_max_output_tokens,
        openai_request_timeout_seconds=int(merged.get("openai_request_timeout_seconds", 180)),
        short_file_limit_seconds=int(merged.get("short_file_limit_seconds", 1200)),
        chunk_seconds=int(merged.get("chunk_seconds", 600)),
        chunk_overlap_seconds=int(merged.get("chunk_overlap_seconds", 15)),
        file_stability_checks=int(merged.get("file_stability_checks", 2)),
        file_stability_interval_seconds=int(merged.get("file_stability_interval_seconds", 2)),
        max_retries=int(merged.get("max_retries", 3)),
        retry_backoff_seconds=int(merged.get("retry_backoff_seconds", 1)),
        daily_token_budget=int(merged.get("daily_token_budget", 100000)),
        per_task_token_budget=int(merged.get("per_task_token_budget", 20000)),
        budget_warning_ratio=float(merged.get("budget_warning_ratio", 0.8)),
    )


def ensure_sandbox_dirs(config: AppConfig) -> None:
    for path in (
        config.incoming_dir,
        config.processing_dir / "normalized_audio",
        config.processing_dir / "chunks",
        config.processing_dir / "chunk_transcripts",
        config.private_outputs_dir / "learnings",
        config.public_review_dir,
        config.processed_archive_dir,
        config.failed_archive_dir,
        config.state_dir,
        config.mindmap_dir,
        config.portfolio_public_root,
    ):
        path.mkdir(parents=True, exist_ok=True)
