from __future__ import annotations

from .config import AppConfig


def provider_policy(config: AppConfig) -> dict:
    return {
        "storage_provider": config.storage_provider,
        "transcription_provider": config.transcription_provider,
        "translation_provider": config.translation_provider,
        "summary_provider": config.summary_provider,
        "research_provider": config.research_provider,
        "openai_quality_layer": {
            "model": config.openai_summary_model,
            "reasoning_effort": config.openai_summary_reasoning_effort,
            "translation_model": config.openai_translation_model,
            "translation_reasoning_effort": config.openai_translation_reasoning_effort,
            "summary_model": config.openai_summary_model,
            "summary_reasoning_effort": config.openai_summary_reasoning_effort,
            "generate_full_english_transcript": config.generate_full_english_transcript,
            "api_key_env": config.openai_api_key_env,
            "rule": (
                "OpenAI is the approved provider for learning synthesis in this MVP. "
                "Full transcript translation is optional and off by default to control cost."
            ),
            "cost_control": "per-task and daily token budgets stay visible in generated cost_budget.json files.",
            "summary_route": "summarize directly from the source transcript unless a full English transcript is explicitly enabled",
            "mindmap_cost": "Mindmap updates are local and zero-cost, using summary.md and mindmap_ingest.md.",
        },
        "architecture_positioning": {
            "current_default": "OpenAI-centered quality layer, local Whisper transcription, private raw data, human-reviewed public release",
            "future_options": [
                "OpenAI Responses API for translation and summary",
                "OpenAI Whisper/local-whisper-compatible CLI for transcription",
                "approved web-search/research MCP after transcription MVP is stable",
            ],
            "approval_required_for": [
                "higher-cost model upgrade",
                "automatic public publishing",
                "external research automation",
                "public publishing automation",
            ],
        },
    }
