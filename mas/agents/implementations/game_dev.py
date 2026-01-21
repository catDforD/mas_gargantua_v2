from __future__ import annotations

from typing import TYPE_CHECKING

from ...core.schemas import AgentCapability, AgentDescriptor

if TYPE_CHECKING:
    from ..pool import AgentPoolRegistry


def descriptor() -> AgentDescriptor:
    return AgentDescriptor(
        name="game_dev",
        capability=AgentCapability.GAME_DEV,
        strategy="chain_of_thought",
        model="MiniMax-M2.1",
        temperature=0.4,
        system_prompt="You develop games including game logic, mechanics, and interactive features.",
        cost="medium",
        use_when=["需要开发游戏", "实现游戏逻辑", "创建交互功能"],
        avoid_when=["纯数据处理", "Web 应用开发"],
        allowed_tools=[],
        resource_permissions={},
    )


def register(registry: AgentPoolRegistry) -> None:
    registry.register(descriptor())
