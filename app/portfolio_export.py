from __future__ import annotations

from pathlib import Path
import shutil

from .config import AppConfig
from .publishing import DEVELOPMENT_PACKAGE_MARKERS, MANAGED_PUBLIC_FILES, SYSTEM_METADATA_NAMES
from .utils import utc_now_iso


PORTFOLIO_ROOT_FILES = {"index.html"}


def _safe_remove(path: Path) -> None:
    if not path.exists():
        return
    if path.is_dir():
        shutil.rmtree(path)
        return
    try:
        path.chmod(0o666)
    except OSError:
        pass
    path.unlink()


def _copy_file(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def _is_development_package(path: Path) -> bool:
    slug = path.name.lower()
    return any(marker in slug for marker in DEVELOPMENT_PACKAGE_MARKERS)


def build_portfolio_index(config: AppConfig, package_dirs: list[Path]) -> str:
    cards = []
    for package_dir in package_dirs:
        note_page = package_dir / "public_learning_note.html"
        quality_page = package_dir / "quality_gate.html"
        cards.append(
            f"""
      <a class="card" href="outputs_public_review/{package_dir.name}/index.html">
        <strong>{package_dir.name}</strong>
        <span>Sanitized exhibit package for GitHub-safe review.</span>
        <small>Primary note: outputs_public_review/{package_dir.name}/{note_page.name}</small>
        <small>Quality gate: outputs_public_review/{package_dir.name}/{quality_page.name}</small>
      </a>"""
        )
    card_html = "\n".join(cards) or '<p class="empty">No public exhibit packages have been published yet.</p>'
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{config.portfolio_owner} Portfolio Exhibit</title>
  <style>
    body {{ margin: 0; font-family: Arial, Helvetica, sans-serif; color: #17202a; background: #f7f5ef; }}
    main {{ max-width: 1080px; margin: 0 auto; padding: 36px 22px 48px; }}
    header {{ border-bottom: 2px solid #17202a; padding-bottom: 18px; margin-bottom: 22px; }}
    .eyebrow {{ color: #0f766e; font-weight: 700; text-transform: uppercase; }}
    h1 {{ margin: 8px 0; font-size: 44px; line-height: 1.05; letter-spacing: 0; }}
    p {{ line-height: 1.6; }}
    a {{ color: #1d4ed8; }}
    .hero-links {{ display: flex; gap: 14px; flex-wrap: wrap; margin-top: 18px; }}
    .hero-links a {{ text-decoration: none; padding: 10px 14px; border: 1px solid #d9e0e8; border-radius: 8px; background: white; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; margin-top: 24px; }}
    .card {{ display: grid; gap: 8px; min-height: 160px; padding: 18px; border: 1px solid #d9e0e8; border-radius: 8px; background: white; text-decoration: none; color: #17202a; }}
    .card span, .card small {{ color: #5f6b7a; }}
    .empty {{ color: #5f6b7a; }}
  </style>
</head>
<body>
<main>
  <header>
    <div class="eyebrow">{config.portfolio_initials} Portfolio Exhibit</div>
    <h1>Enterprise AI Solutions Architecturing and Framework</h1>
    <p>Built by {config.portfolio_owner}. This GitHub-safe portfolio layer mirrors sanitized solution-architecture packages and the latest public framework map, while keeping raw audio and full transcripts outside the repository.</p>
    <div class="hero-links">
      <a href="mindmap/enterprise_ai_mindmap.html">Open solutions framework map</a>
      <a href="mindmap/history/">Open framework history folder</a>
    </div>
  </header>
  <section class="grid">
    {card_html}
  </section>
</main>
</body>
</html>
"""


def export_portfolio_public(config: AppConfig) -> dict:
    root = config.portfolio_public_root
    outputs_target = root / "outputs_public_review"
    mindmap_target = root / "mindmap"
    history_target = mindmap_target / "history"
    outputs_target.mkdir(parents=True, exist_ok=True)
    mindmap_target.mkdir(parents=True, exist_ok=True)
    history_target.mkdir(parents=True, exist_ok=True)

    for name in SYSTEM_METADATA_NAMES:
        _safe_remove(root / name)
        _safe_remove(outputs_target / name)
        _safe_remove(mindmap_target / name)
        _safe_remove(history_target / name)

    public_packages = [
        path
        for path in sorted(config.public_review_dir.iterdir())
        if path.is_dir() and not _is_development_package(path)
    ] if config.public_review_dir.exists() else []
    package_names = {path.name for path in public_packages}

    for existing in sorted(outputs_target.iterdir()) if outputs_target.exists() else []:
        if existing.is_dir() and existing.name not in package_names:
            _safe_remove(existing)

    exported_packages: list[Path] = []
    for package_dir in public_packages:
        target_dir = outputs_target / package_dir.name
        target_dir.mkdir(parents=True, exist_ok=True)
        for existing in sorted(target_dir.iterdir()) if target_dir.exists() else []:
            if existing.name.lower() in SYSTEM_METADATA_NAMES:
                _safe_remove(existing)
            elif existing.name not in MANAGED_PUBLIC_FILES:
                _safe_remove(existing)
        for filename in sorted(MANAGED_PUBLIC_FILES):
            source_file = package_dir / filename
            target_file = target_dir / filename
            if source_file.exists():
                _copy_file(source_file, target_file)
            else:
                _safe_remove(target_file)
        exported_packages.append(target_dir)

    mindmap_source = config.mindmap_dir / "enterprise_ai_mindmap.html"
    if mindmap_source.exists():
        _copy_file(mindmap_source, mindmap_target / "enterprise_ai_mindmap.html")
        snapshot_name = f"enterprise_ai_mindmap-{utc_now_iso().replace(':', '').replace('-', '')}.html"
        _copy_file(mindmap_source, history_target / snapshot_name)

    index_html = build_portfolio_index(config, exported_packages)
    (root / "index.html").write_text(index_html, encoding="utf-8")
    return {
        "portfolio_root": str(root),
        "package_count": len(exported_packages),
        "mindmap_exported": mindmap_source.exists(),
    }
