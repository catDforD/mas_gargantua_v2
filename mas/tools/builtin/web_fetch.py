from __future__ import annotations

from ...core.schemas import ToolResult


async def fetch_url(params: dict[str, object]) -> ToolResult:
    url = str(params.get("url", ""))
    if not url:
        return ToolResult(success=False, error="url required")
    return ToolResult(success=False, error="web fetch not implemented")
