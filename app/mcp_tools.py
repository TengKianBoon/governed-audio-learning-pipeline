from __future__ import annotations

from pathlib import Path
import json

from .cleanup import plan_cleanup
from .config import ensure_sandbox_dirs, load_config
from .doctor import run_doctor
from .exhibit_audit import audit_public_exhibits as run_public_exhibit_audit
from .mindmap import apply_delta, evaluate_delta, load_graph, render_mindmap_html, save_graph
from .notebooklm_export import export_notebooklm_sources
from .pipeline import process_file
from .portfolio_export import export_portfolio_public
from .providers import provider_policy
from .publishing import sanitize_all
from .quality import write_quality_score
from .research_enrichment import enrich_learning_research, latest_learning_package


def tool_schemas() -> list[dict]:
    return [
        {
            "name": "process_learning_audio",
            "description": "Process one local audio/video file or text transcript into private transcripts, OpenAI quality summary, HTML summary, podcast script, NotebookLM handoff package, cost budget, quality score, and mindmap delta.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "input_path": {"type": "string"},
                    "config_path": {"type": "string"},
                    "mock": {"type": "boolean", "default": False},
                    "mock_duration_seconds": {"type": "number"},
                    "archive_after_success": {"type": "boolean", "default": False},
                },
                "required": ["input_path"],
            },
        },
        {
            "name": "review_learning_mindmap",
            "description": "Review all private summaries and mindmap ingest suggestions against the enterprise AI mindmap without auto-publishing.",
            "input_schema": {
                "type": "object",
                "properties": {"config_path": {"type": "string"}},
            },
        },
        {
            "name": "apply_reviewed_mindmap_deltas",
            "description": "Apply add/update mindmap deltas to the private graph after human review.",
            "input_schema": {
                "type": "object",
                "properties": {"config_path": {"type": "string"}},
            },
        },
        {
            "name": "sanitize_public_outputs",
            "description": "Create sanitized public-review packages from private learning outputs.",
            "input_schema": {
                "type": "object",
                "properties": {"config_path": {"type": "string"}},
            },
        },
        {
            "name": "rescore_learning_outputs",
            "description": "Re-run quality scoring for private learning packages without retranscribing audio.",
            "input_schema": {
                "type": "object",
                "properties": {"config_path": {"type": "string"}},
            },
        },
        {
            "name": "get_learning_app_policy",
            "description": "Return retry, cost, privacy, and autonomy defaults for orchestration agents.",
            "input_schema": {
                "type": "object",
                "properties": {"config_path": {"type": "string"}},
            },
        },
        {
            "name": "doctor_check",
            "description": "Check sandbox folders, FFmpeg/FFprobe, Whisper, retry/cost policy, and readiness for real audio.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "config_path": {"type": "string"},
                    "create_sandbox": {"type": "boolean", "default": False},
                },
            },
        },
        {
            "name": "audit_public_exhibits",
            "description": "Audit generated public exhibit files and links for privacy, polish, and portfolio readiness.",
            "input_schema": {
                "type": "object",
                "properties": {"config_path": {"type": "string"}},
            },
        },
        {
            "name": "plan_workspace_cleanup",
            "description": "Dry-run cleanup planning for stale processing files, failed public packages, duplicates, and oversized archives. This never deletes files.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "config_path": {"type": "string"},
                    "processing_stale_days": {"type": "integer", "default": 14},
                    "oversized_archive_mb": {"type": "integer", "default": 500},
                },
            },
        },
        {
            "name": "enrich_learning_research",
            "description": "Use OpenAI Responses web_search to upgrade one private summary into a cited research-enriched report, HTML report, research podcast script, and NotebookLM source bundle.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "config_path": {"type": "string"},
                    "package_path": {"type": "string"},
                    "latest": {"type": "boolean", "default": False},
                    "mock": {"type": "boolean", "default": False},
                },
            },
        },
        {
            "name": "export_notebooklm_sources",
            "description": "Copy original transcript, summary.md, and summary.html into the private NotebookLM source handoff folder for one learning package.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "config_path": {"type": "string"},
                    "package_path": {"type": "string"},
                    "latest": {"type": "boolean", "default": False},
                },
            },
        },
    ]


def process_learning_audio(arguments: dict) -> dict:
    config = load_config(arguments.get("config_path"))
    result = process_file(
        arguments["input_path"],
        config,
        mock=bool(arguments.get("mock", False)),
        mock_duration_seconds=arguments.get("mock_duration_seconds"),
        archive_after_success=bool(arguments.get("archive_after_success", False)),
    )
    return {
        "slug": result.slug,
        "private_output_dir": str(result.private_output_dir),
        "quality_score": result.quality_score,
        "archived_to": str(result.archived_to) if result.archived_to else None,
    }


def review_learning_mindmap(arguments: dict) -> dict:
    config = load_config(arguments.get("config_path"))
    ensure_sandbox_dirs(config)
    graph = load_graph(config.mindmap_dir / "graph.json")
    reviews = []
    for summary in sorted((config.private_outputs_dir / "learnings").glob("*/summary.md")):
        package_dir = summary.parent
        mindmap_ingest = package_dir / "mindmap_ingest.md"
        mindmap_text = summary.read_text(encoding="utf-8")
        if mindmap_ingest.exists():
            mindmap_text = f"{mindmap_text}\n\n{mindmap_ingest.read_text(encoding='utf-8')}"
        reviews.append(evaluate_delta(mindmap_text, package_dir.name, graph))
    review_path = config.private_outputs_dir / "mindmap_review.json"
    review_path.write_text(__import__("json").dumps(reviews, ensure_ascii=False, indent=2), encoding="utf-8")
    render_mindmap_html(
        graph,
        config.mindmap_dir / "enterprise_ai_mindmap.html",
        owner_name=config.portfolio_owner,
        owner_initials=config.portfolio_initials,
        tagline=config.portfolio_tagline,
    )
    export_result = export_portfolio_public(config)
    return {
        "review_path": str(review_path),
        "review_count": len(reviews),
        "portfolio_export_root": export_result["portfolio_root"],
    }


def _apply_mindmap_deltas(config) -> dict:
    ensure_sandbox_dirs(config)
    graph_path = config.mindmap_dir / "graph.json"
    graph = load_graph(graph_path)
    applied = 0
    for delta_path in sorted((config.private_outputs_dir / "learnings").glob("*/mindmap_delta.json")):
        delta = json.loads(delta_path.read_text(encoding="utf-8"))
        if delta.get("recommendation") not in {"add", "update"}:
            continue
        package_dir = delta_path.parent
        public_dir = config.public_review_dir / package_dir.name
        public_link = str(public_dir) if public_dir.exists() else None
        graph = apply_delta(graph, delta, private_link=str(package_dir), public_link=public_link)
        applied += 1
    save_graph(graph_path, graph)
    render_mindmap_html(
        graph,
        config.mindmap_dir / "enterprise_ai_mindmap.html",
        owner_name=config.portfolio_owner,
        owner_initials=config.portfolio_initials,
        tagline=config.portfolio_tagline,
    )
    return {
        "applied_deltas": applied,
        "graph_path": str(graph_path),
        "mindmap_html": str(config.mindmap_dir / "enterprise_ai_mindmap.html"),
        "node_count": len(graph.get("nodes", [])),
    }


def apply_reviewed_mindmap_deltas(arguments: dict) -> dict:
    config = load_config(arguments.get("config_path"))
    result = _apply_mindmap_deltas(config)
    export_result = export_portfolio_public(config)
    result["portfolio_export_root"] = export_result["portfolio_root"]
    return result


def sanitize_public_outputs(arguments: dict) -> dict:
    config = load_config(arguments.get("config_path"))
    ensure_sandbox_dirs(config)
    outputs = sanitize_all(config.private_outputs_dir, config.public_review_dir, owner_name=config.portfolio_owner)
    mindmap_apply_result = _apply_mindmap_deltas(config)
    export_result = export_portfolio_public(config)
    return {
        "public_review_outputs": [str(path) for path in outputs],
        "mindmap_applied_deltas": mindmap_apply_result["applied_deltas"],
        "mindmap_node_count": mindmap_apply_result["node_count"],
        "portfolio_export_root": export_result["portfolio_root"],
        "portfolio_package_count": export_result["package_count"],
    }


def rescore_learning_outputs(arguments: dict) -> dict:
    config = load_config(arguments.get("config_path"))
    ensure_sandbox_dirs(config)
    results = []
    learnings_dir = config.private_outputs_dir / "learnings"
    for package_dir in sorted(path for path in learnings_dir.glob("*") if path.is_dir()):
        score = write_quality_score(package_dir)
        results.append(
            {
                "package": str(package_dir),
                "score": score["score"],
                "passed": score["passed"],
                "transcript_findings": score.get("transcript_findings", []),
            }
        )
    return {"rescored": len(results), "results": results}


def get_learning_app_policy(arguments: dict | None = None) -> dict:
    arguments = arguments or {}
    config = load_config(arguments.get("config_path"))
    return {
        "max_retries": config.max_retries,
        "retry_backoff_seconds": config.retry_backoff_seconds,
        "daily_token_budget": config.daily_token_budget,
        "per_task_token_budget": config.per_task_token_budget,
        "budget_warning_ratio": config.budget_warning_ratio,
        "privacy_model": "public code, private raw data, sanitized public-review outputs",
        "autonomy": "manual-first with human publishing and merge gates",
        "providers": provider_policy(config),
    }


def doctor_check(arguments: dict | None = None) -> dict:
    arguments = arguments or {}
    config = load_config(arguments.get("config_path"))
    return run_doctor(config, create_sandbox=bool(arguments.get("create_sandbox", False)))


def audit_public_exhibits(arguments: dict | None = None) -> dict:
    arguments = arguments or {}
    config = load_config(arguments.get("config_path"))
    ensure_sandbox_dirs(config)
    return run_public_exhibit_audit(
        config.public_review_dir,
        config.mindmap_dir / "enterprise_ai_mindmap.html",
        [config.portfolio_public_root],
    )


def plan_workspace_cleanup(arguments: dict | None = None) -> dict:
    arguments = arguments or {}
    config = load_config(arguments.get("config_path"))
    ensure_sandbox_dirs(config)
    return plan_cleanup(
        config,
        processing_stale_days=int(arguments.get("processing_stale_days", 14)),
        oversized_archive_mb=int(arguments.get("oversized_archive_mb", 500)),
    )


def enrich_learning_research_tool(arguments: dict | None = None) -> dict:
    arguments = arguments or {}
    config = load_config(arguments.get("config_path"))
    ensure_sandbox_dirs(config)
    package_arg = arguments.get("package_path")
    if package_arg:
        package_dir = Path(str(package_arg)).expanduser().resolve()
    else:
        package_dir = latest_learning_package(config)
    return enrich_learning_research(package_dir, config, mock=bool(arguments.get("mock", False)))


def export_notebooklm_sources_tool(arguments: dict | None = None) -> dict:
    arguments = arguments or {}
    config = load_config(arguments.get("config_path"))
    ensure_sandbox_dirs(config)
    package_arg = arguments.get("package_path")
    if package_arg:
        package_dir = Path(str(package_arg)).expanduser().resolve()
    else:
        package_dir = latest_learning_package(config)
    return export_notebooklm_sources(package_dir, config)


TOOLS = {
    "process_learning_audio": process_learning_audio,
    "review_learning_mindmap": review_learning_mindmap,
    "apply_reviewed_mindmap_deltas": apply_reviewed_mindmap_deltas,
    "sanitize_public_outputs": sanitize_public_outputs,
    "rescore_learning_outputs": rescore_learning_outputs,
    "get_learning_app_policy": get_learning_app_policy,
    "doctor_check": doctor_check,
    "audit_public_exhibits": audit_public_exhibits,
    "plan_workspace_cleanup": plan_workspace_cleanup,
    "enrich_learning_research": enrich_learning_research_tool,
    "export_notebooklm_sources": export_notebooklm_sources_tool,
}


def call_tool(name: str, arguments: dict | None = None) -> dict:
    if name not in TOOLS:
        raise KeyError(f"Unknown tool: {name}")
    return TOOLS[name](arguments or {})
