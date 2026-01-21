from __future__ import annotations

from typing import ClassVar

from ..core.schemas import AgentCapability, AgentDescriptor


class AgentPoolRegistry:
    _instance: ClassVar["AgentPoolRegistry | None"] = None
    _pools: ClassVar[dict[str, AgentDescriptor]] = {}

    def __new__(cls) -> "AgentPoolRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, descriptor: AgentDescriptor) -> None:
        if descriptor.name in self._pools:
            raise ValueError(f"Agent already registered: {descriptor.name}")
        self._pools[descriptor.name] = descriptor

    def get(self, name: str) -> AgentDescriptor:
        if name not in self._pools:
            raise KeyError(f"Agent not found: {name}")
        return self._pools[name]

    def get_all(self) -> list[AgentDescriptor]:
        return list(self._pools.values())

    def select_best_agent(
        self, capability: AgentCapability, _context: dict[str, str]
    ) -> AgentDescriptor:
        for descriptor in self._pools.values():
            if descriptor.capability == capability:
                return descriptor
        raise LookupError(f"No agent found for capability: {capability}")
