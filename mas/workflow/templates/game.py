from __future__ import annotations

from ...core.schemas import (
    AgentCapability,
    TaskCategory,
    WorkflowStage,
    WorkflowTemplate,
)


def build_template() -> WorkflowTemplate:
    stages = [
        WorkflowStage(
            id="requirements",
            name="需求分析",
            capability=AgentCapability.PLANNING,
            dependencies=[],
        ),
        WorkflowStage(
            id="implementation",
            name="游戏实现",
            capability=AgentCapability.GAME_DEV,
            dependencies=["requirements"],
        ),
        WorkflowStage(
            id="review",
            name="代码审查",
            capability=AgentCapability.CODE_REVIEW,
            dependencies=["implementation"],
        ),
    ]
    return WorkflowTemplate(
        id="game",
        name="Game Development",
        category=TaskCategory.GAME,
        stages=stages,
    )
