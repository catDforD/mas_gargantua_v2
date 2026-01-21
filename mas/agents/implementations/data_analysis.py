from __future__ import annotations

from typing import TYPE_CHECKING

from ...core.schemas import AgentCapability, AgentDescriptor

if TYPE_CHECKING:
    from ..pool import AgentPoolRegistry


def descriptor() -> AgentDescriptor:
    return AgentDescriptor(
        name="data_analysis",
        capability=AgentCapability.DATA_ANALYSIS,
        strategy="chain_of_thought",
        model="MiniMax-M2.1",
        temperature=0.2,
        system_prompt="You analyze data and derive insights.",
        cost="low",
        use_when=["需要数据分析", "处理数据管道"],
        avoid_when=["仅需界面开发"],
        allowed_tools=[],
        resource_permissions={},
    )


def register(registry: AgentPoolRegistry) -> None:
    registry.register(descriptor())
