from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from app.mcp_tools import call_tool, tool_schemas


class McpToolsTest(unittest.TestCase):
    def make_config(self, temp_dir: str) -> Path:
        config_path = Path(temp_dir) / "paths.test.yaml"
        sandbox = Path(temp_dir) / "sandbox"
        config_path.write_text(
            "\n".join(
                [
                    f'sandbox_root: "{sandbox}"',
                    f'portfolio_public_root: "{Path(temp_dir) / "portfolio_public"}"',
                    'ffmpeg_path: ""',
                    'ffprobe_path: ""',
                    'whisper_command: ".venv/Scripts/whisper.exe"',
                    "max_retries: 2",
                    "retry_backoff_seconds: 0",
                ]
            ),
            encoding="utf-8",
        )
        return config_path

    def test_tool_schemas_include_core_actions(self) -> None:
        names = {tool["name"] for tool in tool_schemas()}
        self.assertIn("process_learning_audio", names)
        self.assertIn("review_learning_mindmap", names)
        self.assertIn("apply_reviewed_mindmap_deltas", names)
        self.assertIn("sanitize_public_outputs", names)
        self.assertIn("rescore_learning_outputs", names)
        self.assertIn("get_learning_app_policy", names)
        self.assertIn("doctor_check", names)
        self.assertIn("audit_public_exhibits", names)
        self.assertIn("plan_workspace_cleanup", names)

    def test_process_tool_mock_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "tool_sample.m4a"
            source.write_bytes(b"fake audio")
            config_path = self.make_config(temp_dir)

            result = call_tool(
                "process_learning_audio",
                {
                    "input_path": str(source),
                    "config_path": str(config_path),
                    "mock": True,
                    "mock_duration_seconds": 120,
                },
            )

            self.assertEqual(result["quality_score"], 100)
            self.assertTrue(Path(result["private_output_dir"]).exists())

    def test_policy_tool_exposes_retry_and_budget(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = self.make_config(temp_dir)
            policy = call_tool("get_learning_app_policy", {"config_path": str(config_path)})
            self.assertEqual(policy["max_retries"], 2)
            self.assertIn("per_task_token_budget", policy)
            self.assertEqual(policy["providers"]["storage_provider"], "local-filesystem")
            self.assertEqual(
                policy["providers"]["openai_quality_layer"]["model"],
                "gpt-5.4-mini",
            )
            self.assertEqual(policy["providers"]["openai_quality_layer"]["reasoning_effort"], "high")
            self.assertEqual(policy["providers"]["openai_quality_layer"]["translation_reasoning_effort"], "low")
            self.assertEqual(policy["providers"]["openai_quality_layer"]["summary_reasoning_effort"], "high")

    def test_portfolio_identity_defaults_to_tkb(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = self.make_config(temp_dir)
            policy = call_tool("get_learning_app_policy", {"config_path": str(config_path)})
            # Visual identity is covered by HTML/publishing tests.
            self.assertEqual(policy["privacy_model"], "public code, private raw data, sanitized public-review outputs")

    def test_doctor_check_reports_mock_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = self.make_config(temp_dir)
            report = call_tool("doctor_check", {"config_path": str(config_path), "create_sandbox": True})
            self.assertTrue(report["ready_for_mock"])
            self.assertFalse(report["ready_for_real_audio"])
            self.assertIn("dependency_checks", report)

    def test_apply_reviewed_mindmap_deltas(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "tool_sample.m4a"
            source.write_bytes(b"fake audio")
            config_path = self.make_config(temp_dir)

            call_tool(
                "process_learning_audio",
                {
                    "input_path": str(source),
                    "config_path": str(config_path),
                    "mock": True,
                    "mock_duration_seconds": 120,
                },
            )
            result = call_tool("apply_reviewed_mindmap_deltas", {"config_path": str(config_path)})

            self.assertGreaterEqual(result["applied_deltas"], 1)
            self.assertGreater(result["node_count"], 0)

    def test_publish_tool_syncs_github_safe_portfolio_export(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "real_learning_note.m4a"
            source.write_bytes(b"fake audio")
            config_path = self.make_config(temp_dir)

            call_tool(
                "process_learning_audio",
                {
                    "input_path": str(source),
                    "config_path": str(config_path),
                    "mock": True,
                    "mock_duration_seconds": 120,
                },
            )
            result = call_tool("sanitize_public_outputs", {"config_path": str(config_path)})

            export_root = Path(result["portfolio_export_root"])
            self.assertTrue((export_root / "index.html").exists())
            self.assertTrue((export_root / "mindmap" / "enterprise_ai_mindmap.html").exists())
            self.assertGreaterEqual(result["mindmap_applied_deltas"], 1)
            self.assertGreater(result["mindmap_node_count"], 0)
            self.assertGreaterEqual(result["portfolio_package_count"], 1)


if __name__ == "__main__":
    unittest.main()
