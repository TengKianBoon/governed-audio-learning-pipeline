from __future__ import annotations

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def file_exists(relative: str) -> bool:
    return (ROOT / relative).exists()


def main() -> int:
    checks = {
        "constitution": file_exists("AGENTS.md"),
        "adr_privacy": file_exists("docs/adr/0001-public-code-private-raw.md"),
        "adr_retries_cost": file_exists("docs/adr/0004-retry-and-cost-controls.md"),
        "adr_mcp": file_exists("docs/adr/0005-mcp-first-interface.md"),
        "adr_portability": file_exists("docs/adr/0006-provider-neutral-portable-architecture.md"),
        "adr_openai_quality": file_exists("docs/adr/0007-openai-quality-layer.md"),
        "hooks": file_exists(".claude/hooks/verify_score.py"),
        "skills": file_exists("skills/quality-gate/SKILL.md"),
        "config_retry_cap": "max_retries: 3" in (ROOT / "config/paths.yaml").read_text(encoding="utf-8"),
        "config_openai_quality": all(
            needle in (ROOT / "config/paths.yaml").read_text(encoding="utf-8")
            for needle in (
                'openai_translation_model: "gpt-5.4-mini"',
                'openai_summary_model: "gpt-5.4-mini"',
                'openai_summary_reasoning_effort: "high"',
                "generate_full_english_transcript: false",
            )
        ),
        "public_guard": file_exists("app/publishing.py"),
        "cost_guard": file_exists("app/cost_guard.py"),
        "text_ingestion": file_exists("app/language.py"),
        "openai_adapter": file_exists("app/openai_quality.py"),
        "mcp_tools": file_exists("app/mcp_tools.py"),
        "provider_policy": file_exists("app/providers.py"),
        "doctor": file_exists("app/doctor.py"),
    }
    completed = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    checks["unit_tests"] = completed.returncode == 0
    passed = sum(1 for value in checks.values() if value)
    score = int(round((passed / len(checks)) * 100))
    print(f"SCORE={score}")
    for name, ok in checks.items():
        print(f"{name}: {'pass' if ok else 'fail'}")
    if completed.returncode != 0:
        print(completed.stdout)
        print(completed.stderr, file=sys.stderr)
    return 0 if score >= 80 else 1


if __name__ == "__main__":
    raise SystemExit(main())
