from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MCPClientConfig:
    server_url: str
    api_key: str | None = None
    timeout: float = 30.0


class MCPClient:
    _config: MCPClientConfig

    def __init__(self, config: MCPClientConfig) -> None:
        self._config = config

    async def call_tool(self, _tool_name: str, _params: dict[str, object]) -> object:
        raise NotImplementedError("MCP client is not implemented")
