from __future__ import annotations

from pathlib import Path
import shutil

from .config import AppConfig, ensure_sandbox_dirs
from .utils import write_text


NOTEBOOKLM_SOURCE_FILES = (
    "original_transcript.md",
    "summary.md",
    "summary.html",
)


class NotebookLMExportError(RuntimeError):
    pass


def notebooklm_export_dir(package_dir: Path, config: AppConfig) -> Path:
    return config.notebooklm_artifacts_root / f"{package_dir.name} NLM"


def export_notebooklm_sources(package_dir: Path, config: AppConfig) -> dict:
    ensure_sandbox_dirs(config)
    if not package_dir.exists():
        raise NotebookLMExportError(f"Learning package not found: {package_dir}")

    missing = [name for name in NOTEBOOKLM_SOURCE_FILES if not (package_dir / name).exists()]
    if missing:
        raise NotebookLMExportError(
            f"Cannot export NotebookLM sources because file(s) are missing: {', '.join(missing)}"
        )

    target = notebooklm_export_dir(package_dir, config)
    target.mkdir(parents=True, exist_ok=True)
    copied = []
    for name in NOTEBOOKLM_SOURCE_FILES:
        source = package_dir / name
        destination = target / name
        shutil.copy2(source, destination)
        copied.append(str(destination))

    write_text(
        target / "README_for_NotebookLM.md",
        (
            "# NotebookLM Source Folder\n\n"
            "Upload these files to NotebookLM as source material for artifact generation:\n\n"
            "- `original_transcript.md`\n"
            "- `summary.md`\n"
            "- `summary.html`\n\n"
            "These files are private learning sources. Do not publish this folder directly. "
            "Use the sanitized public-review package for public sharing.\n"
        ),
    )

    return {
        "notebooklm_export_dir": str(target),
        "copied_files": copied,
        "source_count": len(copied),
        "privacy": "private NotebookLM source handoff; not public output",
    }
