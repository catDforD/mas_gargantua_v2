from __future__ import annotations

from typing import TYPE_CHECKING

from ...core.schemas import AgentCapability, AgentDescriptor

if TYPE_CHECKING:
    from ..pool import AgentPoolRegistry


def descriptor() -> AgentDescriptor:
    return AgentDescriptor(
        name="frontend",
        capability=AgentCapability.FRONTEND,
        strategy="role_assignment",
        model="MiniMax-M2.1",
        temperature=0.4,
        system_prompt="You implement frontend features and UI logic.",
        cost="medium",
        use_when=["涉及前端功能", "需要界面实现"],
        avoid_when=["纯后端任务"],
        allowed_tools=[],
        resource_permissions={},
    )


def register(registry: AgentPoolRegistry) -> None:
    registry.register(descriptor())
