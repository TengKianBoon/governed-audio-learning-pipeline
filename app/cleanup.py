from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path

from .config import AppConfig


DEVELOPMENT_MARKERS = {"sample", "fixture", "mock"}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _age_days(path: Path, now: datetime) -> float:
    modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return round((now - modified).total_seconds() / 86400, 2)


def _safe_read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _file_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0


def _dir_size(path: Path) -> int:
    total = 0
    for item in path.rglob("*"):
        if item.is_file():
            total += _file_size(item)
    return total


def _candidate(
    *,
    category: str,
    action: str,
    path: Path,
    reason: str,
    size_bytes: int,
    age_days: float | None = None,
    safety: str = "review_before_delete",
    extra: dict | None = None,
) -> dict:
    payload = {
        "category": category,
        "action": action,
        "path": str(path),
        "reason": reason,
        "size_bytes": size_bytes,
        "safety": safety,
    }
    if age_days is not None:
        payload["age_days"] = age_days
    if extra:
        payload.update(extra)
    return payload


def _stale_processing_candidates(config: AppConfig, now: datetime, stale_days: int) -> list[dict]:
    if not config.processing_dir.exists():
        return []
    candidates = []
    for path in sorted(item for item in config.processing_dir.rglob("*") if item.is_file()):
        age = _age_days(path, now)
        if age >= stale_days:
            candidates.append(
                _candidate(
                    category="stale_processing_file",
                    action="delete_processing_intermediate_after_review",
                    path=path,
                    reason=f"Processing intermediate older than {stale_days} day(s).",
                    size_bytes=_file_size(path),
                    age_days=age,
                    safety="safe_after_successful_publish_or_rerun_not_needed",
                )
            )
    return candidates


def _public_package_candidates(config: AppConfig, now: datetime) -> list[dict]:
    if not config.public_review_dir.exists():
        return []
    candidates = []
    for package in sorted(path for path in config.public_review_dir.iterdir() if path.is_dir()):
        lower_name = package.name.lower()
        quality = _safe_read_json(package / "quality_score.json")
        age = _age_days(package, now)
        size = _dir_size(package)
        if any(marker in lower_name for marker in DEVELOPMENT_MARKERS):
            candidates.append(
                _candidate(
                    category="development_public_package",
                    action="remove_from_public_review_output",
                    path=package,
                    reason="Development/sample package should not remain in public review output.",
                    size_bytes=size,
                    age_days=age,
                    safety="safe_if_private_source_not_needed_for_demo",
                )
            )
            continue
        if quality and not quality.get("passed", False):
            findings = ", ".join(quality.get("transcript_findings", []) + quality.get("summary_findings", []))
            candidates.append(
                _candidate(
                    category="failed_public_package",
                    action="remove_public_link_or_rerun_before_public_use",
                    path=package,
                    reason=f"Public package quality gate did not pass: {findings or 'quality gate failed'}.",
                    size_bytes=size,
                    age_days=age,
                    safety="keep_private_package_until_issue_is_resolved",
                    extra={"score": quality.get("score"), "passed": False},
                )
            )
        elif not quality:
            candidates.append(
                _candidate(
                    category="unscored_public_package",
                    action="rescore_or_remove_public_review_package",
                    path=package,
                    reason="Public package has no quality_score.json, so it cannot be trusted as public evidence.",
                    size_bytes=size,
                    age_days=age,
                    safety="review_before_delete",
                )
            )
    return candidates


def _package_score(package: Path) -> int:
    quality = _safe_read_json(package / "quality_score.json")
    try:
        return int(quality.get("score", 0))
    except (TypeError, ValueError):
        return 0


def _package_processed_at(package: Path) -> str:
    metadata = _safe_read_json(package / "source_metadata.json")
    return str(metadata.get("processed_at") or "")


def _duplicate_private_package_candidates(config: AppConfig) -> list[dict]:
    learnings_dir = config.private_outputs_dir / "learnings"
    if not learnings_dir.exists():
        return []
    by_fingerprint: dict[str, list[Path]] = defaultdict(list)
    for package in sorted(path for path in learnings_dir.iterdir() if path.is_dir()):
        metadata = _safe_read_json(package / "source_metadata.json")
        fingerprint = str(metadata.get("fingerprint_sha256") or "").strip()
        if fingerprint:
            by_fingerprint[fingerprint].append(package)

    candidates = []
    for fingerprint, packages in sorted(by_fingerprint.items()):
        if len(packages) < 2:
            continue
        keeper = sorted(packages, key=lambda path: (_package_score(path), _package_processed_at(path), path.name), reverse=True)[0]
        for package in packages:
            if package == keeper:
                continue
            candidates.append(
                _candidate(
                    category="duplicate_private_package",
                    action="review_duplicate_private_learning_package",
                    path=package,
                    reason="Same source fingerprint as another private package; keep the highest-quality/latest package.",
                    size_bytes=_dir_size(package),
                    safety="manual_review_required_before_delete",
                    extra={
                        "fingerprint_sha256": fingerprint,
                        "suggested_keeper": str(keeper),
                        "score": _package_score(package),
                        "keeper_score": _package_score(keeper),
                    },
                )
            )
    return candidates


def _oversized_archive_candidates(config: AppConfig, oversized_archive_mb: int) -> list[dict]:
    threshold = oversized_archive_mb * 1024 * 1024
    candidates = []
    for archive_dir in (config.processed_archive_dir, config.failed_archive_dir):
        if not archive_dir.exists():
            continue
        for path in sorted(item for item in archive_dir.rglob("*") if item.is_file()):
            size = _file_size(path)
            if size >= threshold:
                candidates.append(
                    _candidate(
                        category="oversized_archive_file",
                        action="move_to_cold_storage_or_delete_after_confirmation",
                        path=path,
                        reason=f"Archived source file is at least {oversized_archive_mb} MB.",
                        size_bytes=size,
                        safety="confirm_summary_and_mindmap_before_removal",
                    )
                )
    return candidates


def plan_cleanup(
    config: AppConfig,
    *,
    processing_stale_days: int = 14,
    oversized_archive_mb: int = 500,
) -> dict:
    now = _utc_now()
    candidates: list[dict] = []
    candidates.extend(_stale_processing_candidates(config, now, processing_stale_days))
    candidates.extend(_public_package_candidates(config, now))
    candidates.extend(_duplicate_private_package_candidates(config))
    candidates.extend(_oversized_archive_candidates(config, oversized_archive_mb))

    by_category: dict[str, int] = defaultdict(int)
    for item in candidates:
        by_category[str(item["category"])] += 1

    return {
        "mode": "dry_run",
        "applies_changes": False,
        "generated_at": now.isoformat(),
        "policy": {
            "processing_stale_days": processing_stale_days,
            "oversized_archive_mb": oversized_archive_mb,
            "delete_requires_future_apply_step": True,
        },
        "summary": {
            "candidate_count": len(candidates),
            "reclaimable_bytes_estimate": sum(int(item.get("size_bytes", 0)) for item in candidates),
            "by_category": dict(sorted(by_category.items())),
        },
        "candidates": candidates,
        "next_step": "Review this dry-run report. Do not delete anything until the candidate list looks correct.",
    }
