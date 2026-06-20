from __future__ import annotations

import json
from pathlib import Path
import shutil

from .config import AppConfig, ensure_sandbox_dirs, load_config
from .cost_guard import budget_report, write_budget_report
from .language import detect_language, is_english_language
from .media import (
    build_chunk_plan,
    is_supported_input,
    is_supported_media,
    is_supported_text,
    normalize_to_wav,
    probe_duration_seconds,
    split_wav,
)
from .mindmap import apply_delta, evaluate_delta, load_graph, render_mindmap_html, save_graph
from .models import ProcessingResult, TranscriptionResult
from .openai_quality import build_quality_summary, extract_mindmap_ingest_suggestion, translate_to_english
from .quality import write_quality_score
from .registry import update_learning_registry, update_processed_registry
from .stitch import stitch_results
from .transcription import run_whisper
from .utils import fingerprint_file, slugify, utc_now_iso, write_text


class PipelineError(RuntimeError):
    pass


def _create_slug(input_path: Path, fingerprint: str) -> str:
    date_prefix = utc_now_iso()[:10].replace("-", "")
    return f"{date_prefix}-{slugify(input_path.stem)}-{fingerprint[:8]}"


def _mock_wav(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"MOCK-WAV")
    return path


def _archive_input(input_path: Path, config: AppConfig) -> Path:
    target = config.processed_archive_dir / input_path.name
    if target.exists():
        target = config.processed_archive_dir / f"{input_path.stem}-{utc_now_iso().replace(':', '')}{input_path.suffix}"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(input_path), str(target))
    return target


def _read_transcript_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-16", "gb18030", "big5"):
        try:
            return path.read_text(encoding=encoding).strip()
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace").strip()


def _mock_wav_chunks(config: AppConfig, slug: str, chunks: list) -> list[Path]:
    return [_mock_wav(config.processing_dir / "chunks" / slug / f"chunk_{chunk.index:03d}.wav") for chunk in chunks]


def _process_media_source(
    source: Path,
    slug: str,
    config: AppConfig,
    *,
    mock: bool,
    mock_duration_seconds: float | None,
) -> tuple[str, str, str, float | None, int, str]:
    duration = mock_duration_seconds if mock_duration_seconds is not None else probe_duration_seconds(source, config)
    normalized = config.processing_dir / "normalized_audio" / f"{slug}.wav"
    if mock:
        _mock_wav(normalized)
    else:
        normalize_to_wav(source, normalized, config)

    chunks = build_chunk_plan(
        duration,
        short_limit_seconds=config.short_file_limit_seconds,
        chunk_seconds=config.chunk_seconds,
        overlap_seconds=config.chunk_overlap_seconds,
    )
    if mock and len(chunks) > 1:
        chunk_files = _mock_wav_chunks(config, slug, chunks)
    else:
        chunk_files = split_wav(normalized, config.processing_dir / "chunks" / slug, chunks, config)

    original_results: list[TranscriptionResult] = []
    for index, chunk_path in enumerate(chunk_files):
        original_results.append(
            run_whisper(
                chunk_path,
                config.processing_dir / "chunk_transcripts" / slug / "original",
                config,
                task="transcribe",
                model=config.whisper_model,
                index=index,
                mock=mock,
            )
        )

    original_transcript = stitch_results(original_results, chunks)
    hinted_language = next((result.language for result in original_results if result.language), None)
    detected_language = detect_language(original_transcript, hinted_language)
    if is_english_language(detected_language):
        return original_transcript, original_transcript, detected_language, duration, len(chunks), "skipped_source_is_english"
    if not config.generate_full_english_transcript:
        return (
            original_transcript,
            _skipped_english_transcript_note(detected_language),
            detected_language,
            duration,
            len(chunks),
            "skipped_full_translation_summary_direct",
        )

    english_transcript = translate_to_english(
        original_transcript,
        source_name=source.name,
        config=config,
        mock=mock,
    )
    return original_transcript, english_transcript, detected_language, duration, len(chunks), "openai_translated_to_english"


def _process_text_source(source: Path, config: AppConfig, *, mock: bool) -> tuple[str, str, str, None, int, str]:
    original_transcript = _read_transcript_text(source)
    if not original_transcript:
        raise PipelineError(f"Text input is empty: {source}")
    detected_language = detect_language(original_transcript)
    if is_english_language(detected_language):
        return original_transcript, original_transcript, detected_language, None, 0, "skipped_source_is_english"
    if not config.generate_full_english_transcript:
        return (
            original_transcript,
            _skipped_english_transcript_note(detected_language),
            detected_language,
            None,
            0,
            "skipped_full_translation_summary_direct",
        )
    english_transcript = translate_to_english(
        original_transcript,
        source_name=source.name,
        config=config,
        mock=mock,
    )
    return original_transcript, english_transcript, detected_language, None, 0, "openai_translated_to_english"


def _skipped_english_transcript_note(detected_language: str) -> str:
    return (
        "A full English transcript was intentionally not generated for this learning package. "
        "The daily cost-saving route keeps the original-language transcript private and sends that source text "
        "directly into the OpenAI summary step, which produces the English learning summary and mindmap ingest "
        "suggestion. Use original_transcript.md for evidence, summary.md for human reading, and mindmap_ingest.md "
        f"for flow-map placement. Detected source language: {detected_language}."
    )


def _summary_input_text(
    *,
    original_transcript: str,
    english_transcript: str,
    translation_status: str,
) -> tuple[str, str]:
    if translation_status == "skipped_full_translation_summary_direct":
        return original_transcript, "original_transcript.md"
    return english_transcript, "english_transcribed.md"


def process_file(
    input_path: str | Path,
    config: AppConfig | None = None,
    *,
    mock: bool = False,
    mock_duration_seconds: float | None = None,
    archive_after_success: bool = False,
) -> ProcessingResult:
    config = config or load_config()
    ensure_sandbox_dirs(config)

    source = Path(input_path).expanduser().resolve()
    if not source.exists():
        raise PipelineError(f"Input file not found: {source}")
    if not is_supported_input(source):
        raise PipelineError(f"Unsupported input extension: {source.suffix}")

    fingerprint = fingerprint_file(source)
    slug = _create_slug(source, fingerprint)
    package_dir = config.private_outputs_dir / "learnings" / slug
    package_dir.mkdir(parents=True, exist_ok=True)

    if is_supported_media(source):
        input_kind = "audio_video"
        original_transcript, english_transcript, detected_language, duration, chunk_count, translation_status = (
            _process_media_source(
                source,
                slug,
                config,
                mock=mock,
                mock_duration_seconds=mock_duration_seconds,
            )
        )
    elif is_supported_text(source):
        input_kind = "text_transcript"
        original_transcript, english_transcript, detected_language, duration, chunk_count, translation_status = (
            _process_text_source(source, config, mock=mock)
        )
    else:
        raise PipelineError(f"Unsupported input extension: {source.suffix}")

    summary_input_text, summary_input_artifact = _summary_input_text(
        original_transcript=original_transcript,
        english_transcript=english_transcript,
        translation_status=translation_status,
    )

    summary_text = build_quality_summary(
        summary_input_text,
        source_name=source.name,
        source_language=detected_language,
        config=config,
        mock=mock,
    )
    mindmap_ingest_suggestion = extract_mindmap_ingest_suggestion(summary_text)

    metadata = {
        "source_filename": source.name,
        "source_extension": source.suffix.lower(),
        "input_kind": input_kind,
        "fingerprint_sha256": fingerprint,
        "duration_seconds": duration,
        "chunk_count": chunk_count,
        "detected_language": detected_language,
        "translation_status": translation_status,
        "transcription_provider": config.transcription_provider,
        "translation_provider": config.translation_provider,
        "summary_provider": config.summary_provider,
        "generate_full_english_transcript": config.generate_full_english_transcript,
        "auto_apply_mindmap_delta": config.auto_apply_mindmap_delta,
        "summary_input_artifact": summary_input_artifact,
        "openai_translation_model": config.openai_translation_model,
        "openai_translation_reasoning_effort": config.openai_translation_reasoning_effort,
        "openai_summary_model": config.openai_summary_model,
        "openai_summary_reasoning_effort": config.openai_summary_reasoning_effort,
        "openai_quality_model": config.openai_summary_model,
        "openai_reasoning_effort": config.openai_summary_reasoning_effort,
        "mindmap_source": "summary.md + mindmap_ingest.md",
        "mindmap_cost": "zero; local rule-based update from summary-level text",
        "processed_at": utc_now_iso(),
        "privacy": "private raw source and full transcripts",
    }
    (package_dir / "source_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    write_text(package_dir / "original_transcript.md", f"# Original Transcript\n\n{original_transcript}")
    write_text(package_dir / "english_transcribed.md", f"# English Transcript\n\n{english_transcript}")
    write_text(package_dir / "summary.md", summary_text)
    write_text(package_dir / "mindmap_ingest.md", f"# Mindmap Ingest Suggestion\n\n{mindmap_ingest_suggestion}\n")
    write_budget_report(
        package_dir / "cost_budget.json",
        budget_report(
            original_text=original_transcript,
            english_text=english_transcript,
            summary_input_text=summary_input_text,
            summary_text=summary_text,
            translation_was_run=translation_status == "openai_translated_to_english",
            per_task_budget=config.per_task_token_budget,
            warning_ratio=config.budget_warning_ratio,
            paid_provider=(
                f"{config.summary_provider} direct summary; "
                f"full translation {'enabled' if config.generate_full_english_transcript else 'skipped'}; "
                "mindmap update is local/free"
            ),
        ),
    )

    graph_path = config.mindmap_dir / "graph.json"
    graph = load_graph(graph_path)
    mindmap_input = f"{summary_text}\n\n{mindmap_ingest_suggestion}"
    delta = evaluate_delta(mindmap_input, slug, graph)
    delta["mindmap_ingest_suggestion"] = mindmap_ingest_suggestion
    delta["mindmap_source"] = "summary.md + mindmap_ingest.md"
    delta["mindmap_cost"] = "zero; local rule-based update from summary-level text"
    (package_dir / "mindmap_delta.json").write_text(json.dumps(delta, ensure_ascii=False, indent=2), encoding="utf-8")

    quality = write_quality_score(package_dir)
    if (
        config.auto_apply_mindmap_delta
        and quality.get("passed")
        and delta.get("recommendation") in {"add", "update"}
    ):
        graph = apply_delta(graph, delta, private_link=str(package_dir))
        delta["auto_applied_private_graph"] = True
        (package_dir / "mindmap_delta.json").write_text(json.dumps(delta, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        delta["auto_applied_private_graph"] = False
        (package_dir / "mindmap_delta.json").write_text(json.dumps(delta, ensure_ascii=False, indent=2), encoding="utf-8")
    save_graph(graph_path, graph)
    render_mindmap_html(
        graph,
        config.mindmap_dir / "enterprise_ai_mindmap.html",
        owner_name=config.portfolio_owner,
        owner_initials=config.portfolio_initials,
        tagline=config.portfolio_tagline,
    )
    update_processed_registry(config.state_dir, fingerprint, slug, package_dir)
    update_learning_registry(config.state_dir, slug, source.name, package_dir, int(quality["score"]))

    archived_to = _archive_input(source, config) if archive_after_success else None
    return ProcessingResult(slug=slug, private_output_dir=package_dir, quality_score=int(quality["score"]), archived_to=archived_to)
