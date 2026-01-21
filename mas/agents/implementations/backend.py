from __future__ import annotations

from typing import TYPE_CHECKING

from ...core.schemas import AgentCapability, AgentDescriptor

if TYPE_CHECKING:
    from ..pool import AgentPoolRegistry


def descriptor() -> AgentDescriptor:
    return AgentDescriptor(
        name="backend",
        capability=AgentCapability.BACKEND,
        strategy="chain_of_thought",
        model="MiniMax-M2.1",
        temperature=0.3,
        system_prompt="You implement backend services and APIs.",
        cost="medium",
        use_when=["涉及后端逻辑", "需要构建 API"],
        avoid_when=["纯前端任务"],
        allowed_tools=[],
        resource_permissions={},
    )


def register(registry: AgentPoolRegistry) -> None:
    registry.register(descriptor())
