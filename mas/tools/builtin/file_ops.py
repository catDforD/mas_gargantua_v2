from __future__ import annotations

from ...core.schemas import ToolResult


async def read_file(params: dict[str, object]) -> ToolResult:
    path = str(params.get("path", ""))
    if not path:
        return ToolResult(success=False, error="path required")
    return ToolResult(success=False, error="file read not implemented")


async def write_file(params: dict[str, object]) -> ToolResult:
    path = str(params.get("path", ""))
    if not path:
        return ToolResult(success=False, error="path required")
    return ToolResult(success=False, error="file write not implemented")
