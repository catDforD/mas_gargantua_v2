from __future__ import annotations

from typing import TYPE_CHECKING

from ...core.schemas import AgentCapability, AgentDescriptor

if TYPE_CHECKING:
    from ..pool import AgentPoolRegistry


def descriptor() -> AgentDescriptor:
    return AgentDescriptor(
        name="planning",
        capability=AgentCapability.PLANNING,
        strategy="chain_of_thought",
        model="MiniMax-M2.1",
        temperature=0.3,
        system_prompt="You analyze requirements and create detailed implementation plans.",
        cost="low",
        use_when=["需要需求分析", "制定实现计划", "架构设计"],
        avoid_when=["直接编码实现"],
        allowed_tools=[],
        resource_permissions={},
    )


def register(registry: AgentPoolRegistry) -> None:
    registry.register(descriptor())
