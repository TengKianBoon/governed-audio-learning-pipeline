from __future__ import annotations

import json
from pathlib import Path

from .utils import utc_now_iso


def _read_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def update_processed_registry(state_dir: Path, fingerprint: str, slug: str, package_dir: Path) -> None:
    path = state_dir / "processed_files.json"
    registry = _read_json(path, {"processed": {}})
    registry.setdefault("processed", {})[fingerprint] = {
        "slug": slug,
        "package_dir": str(package_dir),
        "processed_at": utc_now_iso(),
    }
    path.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")


def update_learning_registry(state_dir: Path, slug: str, source_name: str, package_dir: Path, score: int) -> None:
    path = state_dir / "learning_registry.json"
    registry = _read_json(path, {"learnings": []})
    registry.setdefault("learnings", []).append(
        {
            "slug": slug,
            "source_name": source_name,
            "package_dir": str(package_dir),
            "quality_score": score,
            "created_at": utc_now_iso(),
        }
    )
    path.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")
