from __future__ import annotations

from typing import Callable

from ..core.schemas import ToolResult

ToolHandler = Callable[[dict[str, object]], object]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolHandler] = {}
        self._schemas: dict[str, dict[str, object]] = {}

    def register(
        self, name: str, schema: dict[str, object], handler: ToolHandler
    ) -> None:
        if name in self._tools:
            raise ValueError(f"Tool already registered: {name}")
        self._tools[name] = handler
        self._schemas[name] = schema

    def get_schema(self, name: str) -> dict[str, object]:
        if name not in self._schemas:
            raise KeyError(f"Tool schema not found: {name}")
        return self._schemas[name]

    async def call_tool(self, name: str, params: dict[str, object]) -> ToolResult:
        if name not in self._tools:
            return ToolResult(success=False, error="Tool not found")
        try:
            result = self._tools[name](params)
            return ToolResult(success=True, output=str(result))
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))
