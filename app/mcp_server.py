from __future__ import annotations

from .mcp_tools import TOOLS


def create_server():
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError(
            "Python MCP SDK is not installed. The app still exposes app.mcp_tools for testing; "
            "install the MCP SDK later to run this adapter."
        ) from exc

    server = FastMCP("governed-audio-learning-pipeline")

    @server.tool()
    def process_learning_audio(input_path: str, config_path: str | None = None, mock: bool = False, mock_duration_seconds: float | None = None, archive_after_success: bool = False) -> dict:
        return TOOLS["process_learning_audio"](
            {
                "input_path": input_path,
                "config_path": config_path,
                "mock": mock,
                "mock_duration_seconds": mock_duration_seconds,
                "archive_after_success": archive_after_success,
            }
        )

    @server.tool()
    def review_learning_mindmap(config_path: str | None = None) -> dict:
        return TOOLS["review_learning_mindmap"]({"config_path": config_path})

    @server.tool()
    def sanitize_public_outputs(config_path: str | None = None) -> dict:
        return TOOLS["sanitize_public_outputs"]({"config_path": config_path})

    @server.tool()
    def get_learning_app_policy(config_path: str | None = None) -> dict:
        return TOOLS["get_learning_app_policy"]({"config_path": config_path})

    @server.tool()
    def doctor_check(config_path: str | None = None, create_sandbox: bool = False) -> dict:
        return TOOLS["doctor_check"]({"config_path": config_path, "create_sandbox": create_sandbox})

    @server.tool()
    def plan_workspace_cleanup(config_path: str | None = None, processing_stale_days: int = 14, oversized_archive_mb: int = 500) -> dict:
        return TOOLS["plan_workspace_cleanup"](
            {
                "config_path": config_path,
                "processing_stale_days": processing_stale_days,
                "oversized_archive_mb": oversized_archive_mb,
            }
        )

    return server


def main() -> None:
    create_server().run()


if __name__ == "__main__":
    main()
