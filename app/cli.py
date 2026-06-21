from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .config import ensure_sandbox_dirs, load_config
from .media import MediaDependencyError
from .mcp_tools import call_tool, tool_schemas
from .openai_quality import OpenAIQualityError
from .pipeline import PipelineError
from .publishing import PublishingGateError
from .notebooklm_export import NotebookLMExportError
from .research_enrichment import ResearchEnrichmentError
from .transcription import TranscriptionDependencyError
from .watcher import watch_folder


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Governed Audio Learning Pipeline")
    parser.add_argument("--config", dest="global_config", help="Optional config file path.")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--config", dest="config", help="Optional config file path.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    process = subparsers.add_parser("process", parents=[common], help="Process one audio/video file or text transcript.")
    process.add_argument("--input", required=True, help="Path to audio, video, or text transcript input.")
    process.add_argument("--mock", action="store_true", help="Run without FFmpeg/Whisper for testing.")
    process.add_argument("--mock-duration-seconds", type=float, default=None, help="Pretend duration for chunk testing.")
    process.add_argument("--archive", action="store_true", help="Move source file to archive/processed after success.")

    process_latest = subparsers.add_parser("process-latest", parents=[common], help="Process the newest supported file in incoming/.")
    process_latest.add_argument("--mock", action="store_true", help="Run without FFmpeg/Whisper for testing.")
    process_latest.add_argument("--archive", action="store_true", help="Move source file to archive/processed after success.")

    watch = subparsers.add_parser("watch", parents=[common], help="Watch/process a folder.")
    watch.add_argument("--folder", required=True, help="Folder to watch.")
    watch.add_argument("--once", action="store_true", help="Process once and exit.")
    watch.add_argument("--mock", action="store_true", help="Run without FFmpeg/Whisper for testing.")
    watch.add_argument("--no-archive", action="store_true", help="Leave successfully processed files in the watched folder.")

    mindmap = subparsers.add_parser("mindmap", parents=[common], help="Review the mindmap delta for private outputs.")
    mindmap.add_argument("--review", action="store_true", help="Create review from existing private outputs.")
    mindmap.add_argument("--apply-reviewed", action="store_true", help="Apply add/update deltas to the private mindmap graph.")

    publish = subparsers.add_parser("publish", parents=[common], help="Create sanitized public-review outputs.")
    publish.add_argument("--sanitize", action="store_true", help="Run the publishing sanitizer.")

    quality = subparsers.add_parser("quality", parents=[common], help="Run quality checks.")
    quality.add_argument("--rescore", action="store_true", help="Rescore private learning packages without retranscribing.")

    tools = subparsers.add_parser("tools", parents=[common], help="Print MCP-ready tool schemas.")
    tools.add_argument("--json", action="store_true", help="Print schemas as JSON.")

    doctor = subparsers.add_parser("doctor", parents=[common], help="Check setup readiness.")
    doctor.add_argument("--create-sandbox", action="store_true", help="Create private sandbox folders if missing.")

    exhibit = subparsers.add_parser("exhibit", parents=[common], help="Audit public exhibit readiness.")
    exhibit.add_argument("--audit", action="store_true", help="Check public links, privacy boundaries, and portfolio readiness.")

    clean = subparsers.add_parser("clean", parents=[common], help="Plan workspace cleanup safely.")
    clean.add_argument("--dry-run", action="store_true", help="Report cleanup candidates without deleting anything.")
    clean.add_argument("--processing-days", type=int, default=14, help="Report processing files at least this many days old.")
    clean.add_argument("--archive-mb", type=int, default=500, help="Report archived files at least this many MB.")

    research = subparsers.add_parser("research", parents=[common], help="Create a cited web-research enrichment report.")
    research.add_argument("--enrich", action="store_true", help="Use OpenAI web_search to enrich one learning summary.")
    research.add_argument("--latest", action="store_true", help="Enrich the newest private learning package.")
    research.add_argument("--package", dest="package_path", help="Path to a private learning package folder.")
    research.add_argument("--mock", action="store_true", help="Create a mock research report without an OpenAI call.")

    notebooklm = subparsers.add_parser("notebooklm", parents=[common], help="Prepare NotebookLM source handoff folders.")
    notebooklm.add_argument("--export", action="store_true", help="Copy source files into the NotebookLM artifacts folder.")
    notebooklm.add_argument("--latest", action="store_true", help="Export the newest private learning package.")
    notebooklm.add_argument("--package", dest="package_path", help="Path to a private learning package folder.")

    return parser


def config_path(args: argparse.Namespace) -> str | None:
    return getattr(args, "config", None) or getattr(args, "global_config", None)


def cmd_process(args: argparse.Namespace) -> int:
    result = call_tool(
        "process_learning_audio",
        {
            "input_path": args.input,
            "config_path": config_path(args),
            "mock": args.mock,
            "mock_duration_seconds": args.mock_duration_seconds,
            "archive_after_success": args.archive,
        },
    )
    print(json.dumps(result, indent=2))
    return 0


def cmd_process_latest(args: argparse.Namespace) -> int:
    config = load_config(config_path(args))
    ensure_sandbox_dirs(config)
    from .media import is_supported_input

    candidates = [path for path in config.incoming_dir.iterdir() if path.is_file() and is_supported_input(path)]
    if not candidates:
        print(json.dumps({"error": f"No supported audio/video/text files found in {config.incoming_dir}"}, indent=2))
        return 1
    newest = max(candidates, key=lambda path: path.stat().st_mtime)
    result = call_tool(
        "process_learning_audio",
        {
            "input_path": str(newest),
            "config_path": config_path(args),
            "mock": args.mock,
            "archive_after_success": args.archive,
        },
    )
    result["input_path"] = str(newest)
    print(json.dumps(result, indent=2))
    return 0


def cmd_watch(args: argparse.Namespace) -> int:
    config = load_config(config_path(args))
    ensure_sandbox_dirs(config)
    watch_folder(Path(args.folder), config, once=args.once, mock=args.mock, archive_after_success=not args.no_archive)
    return 0


def cmd_mindmap(args: argparse.Namespace) -> int:
    print(json.dumps(call_tool("review_learning_mindmap", {"config_path": config_path(args)}), indent=2))
    if args.apply_reviewed:
        print(json.dumps(call_tool("apply_reviewed_mindmap_deltas", {"config_path": config_path(args)}), indent=2))
    return 0


def cmd_publish(args: argparse.Namespace) -> int:
    print(json.dumps(call_tool("sanitize_public_outputs", {"config_path": config_path(args)}), indent=2))
    return 0


def cmd_quality(args: argparse.Namespace) -> int:
    if args.rescore:
        print(json.dumps(call_tool("rescore_learning_outputs", {"config_path": config_path(args)}), indent=2))
        return 0
    print(json.dumps({"error": "Choose --rescore"}, indent=2))
    return 1


def cmd_tools(args: argparse.Namespace) -> int:
    payload = tool_schemas()
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        for tool in payload:
            print(f"{tool['name']}: {tool['description']}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    print(
        json.dumps(
            call_tool(
                "doctor_check",
                {"config_path": config_path(args), "create_sandbox": args.create_sandbox},
            ),
            indent=2,
        )
    )
    return 0


def cmd_exhibit(args: argparse.Namespace) -> int:
    if args.audit:
        print(json.dumps(call_tool("audit_public_exhibits", {"config_path": config_path(args)}), indent=2))
        return 0
    print(json.dumps({"error": "Choose --audit"}, indent=2))
    return 1


def cmd_clean(args: argparse.Namespace) -> int:
    if args.dry_run:
        print(
            json.dumps(
                call_tool(
                    "plan_workspace_cleanup",
                    {
                        "config_path": config_path(args),
                        "processing_stale_days": args.processing_days,
                        "oversized_archive_mb": args.archive_mb,
                    },
                ),
                indent=2,
            )
        )
        return 0
    print(json.dumps({"error": "Choose --dry-run. Cleanup apply mode is intentionally not enabled yet."}, indent=2))
    return 1


def cmd_research(args: argparse.Namespace) -> int:
    if args.enrich:
        payload = {
            "config_path": config_path(args),
            "mock": args.mock,
        }
        if args.package_path:
            payload["package_path"] = args.package_path
        if args.latest:
            payload["latest"] = True
        print(json.dumps(call_tool("enrich_learning_research", payload), indent=2))
        return 0
    print(json.dumps({"error": "Choose --enrich with --latest or --package <folder>."}, indent=2))
    return 1


def cmd_notebooklm(args: argparse.Namespace) -> int:
    if args.export:
        payload = {"config_path": config_path(args)}
        if args.package_path:
            payload["package_path"] = args.package_path
        if args.latest:
            payload["latest"] = True
        print(json.dumps(call_tool("export_notebooklm_sources", payload), indent=2))
        return 0
    print(json.dumps({"error": "Choose --export with --latest or --package <folder>."}, indent=2))
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "process":
            return cmd_process(args)
        if args.command == "process-latest":
            return cmd_process_latest(args)
        if args.command == "watch":
            return cmd_watch(args)
        if args.command == "mindmap":
            return cmd_mindmap(args)
        if args.command == "publish":
            return cmd_publish(args)
        if args.command == "quality":
            return cmd_quality(args)
        if args.command == "tools":
            return cmd_tools(args)
        if args.command == "doctor":
            return cmd_doctor(args)
        if args.command == "exhibit":
            return cmd_exhibit(args)
        if args.command == "clean":
            return cmd_clean(args)
        if args.command == "research":
            return cmd_research(args)
        if args.command == "notebooklm":
            return cmd_notebooklm(args)
    except PermissionError as exc:
        print(
            json.dumps(
                {
                    "error": "permission_denied",
                    "message": str(exc),
                    "beginner_hint": "Run this command in your own PowerShell, and make sure the private audio sandbox folder is not locked by another app.",
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1
    except (
        PipelineError,
        MediaDependencyError,
        TranscriptionDependencyError,
        PublishingGateError,
        NotebookLMExportError,
        OpenAIQualityError,
        ResearchEnrichmentError,
    ) as exc:
        print(json.dumps({"error": exc.__class__.__name__, "message": str(exc)}, indent=2), file=sys.stderr)
        return 1
    parser.error("Unknown command")
    return 2
