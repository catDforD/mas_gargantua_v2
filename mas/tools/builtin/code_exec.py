from __future__ import annotations

from ...core.schemas import ToolResult


async def run_code(params: dict[str, object]) -> ToolResult:
    language = str(params.get("language", ""))
    if not language:
        return ToolResult(success=False, error="language required")
    return ToolResult(success=False, error="code execution not implemented")
