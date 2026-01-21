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
            id="pipeline",
            name="数据管道实现",
            capability=AgentCapability.DATA_ANALYSIS,
            dependencies=["requirements"],
        ),
        WorkflowStage(
            id="review",
            name="代码审查",
            capability=AgentCapability.CODE_REVIEW,
            dependencies=["pipeline"],
        ),
    ]
    return WorkflowTemplate(
        id="data_pipeline",
        name="Data Pipeline",
        category=TaskCategory.DATA_PIPELINE,
        stages=stages,
    )
