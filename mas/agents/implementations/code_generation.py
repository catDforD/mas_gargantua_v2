from __future__ import annotations

from typing import TYPE_CHECKING

from ...core.schemas import AgentCapability, AgentDescriptor

if TYPE_CHECKING:
    from ..pool import AgentPoolRegistry


def descriptor() -> AgentDescriptor:
    return AgentDescriptor(
        name="code_generation",
        capability=AgentCapability.CODE_GENERATION,
        strategy="chain_of_thought",
        model="MiniMax-M2.1",
        temperature=0.3,
        system_prompt="You generate implementation code.",
        cost="medium",
        use_when=["需要实现核心功能", "生成代码草稿"],
        avoid_when=["仅需代码审查"],
        allowed_tools=[],
        resource_permissions={},
    )


def register(registry: AgentPoolRegistry) -> None:
    registry.register(descriptor())
