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
            id="architecture",
            name="架构设计",
            capability=AgentCapability.PLANNING,
            dependencies=["requirements"],
        ),
        WorkflowStage(
            id="backend",
            name="后端实现",
            capability=AgentCapability.BACKEND,
            dependencies=["architecture"],
        ),
        WorkflowStage(
            id="frontend",
            name="前端实现",
            capability=AgentCapability.FRONTEND,
            dependencies=["architecture"],
        ),
        WorkflowStage(
            id="review",
            name="代码审查",
            capability=AgentCapability.CODE_REVIEW,
            dependencies=["backend", "frontend"],
        ),
    ]
    return WorkflowTemplate(
        id="web_app",
        name="Web Application",
        category=TaskCategory.WEB_APPLICATION,
        stages=stages,
    )
