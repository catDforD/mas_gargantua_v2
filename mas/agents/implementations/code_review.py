from __future__ import annotations

from typing import TYPE_CHECKING

from ...core.schemas import AgentCapability, AgentDescriptor

if TYPE_CHECKING:
    from ..pool import AgentPoolRegistry


def descriptor() -> AgentDescriptor:
    return AgentDescriptor(
        name="code_review",
        capability=AgentCapability.CODE_REVIEW,
        strategy="reflexion",
        model="MiniMax-M2.1",
        temperature=0.2,
        system_prompt="You review code quality and safety.",
        cost="low",
        use_when=["需要审查代码", "检查安全与质量"],
        avoid_when=["需要生成大量新代码"],
        allowed_tools=[],
        resource_permissions={},
    )


def register(registry: AgentPoolRegistry) -> None:
    registry.register(descriptor())
