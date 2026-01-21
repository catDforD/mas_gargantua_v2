from __future__ import annotations

from ..core.schemas import AgentCapability, TaskCategory
from ..core.task import Task
from ..core.workflow import Workflow
from .decomposer import TaskDecomposer
from .templates import TEMPLATES


class WorkflowFactory:
    _decomposer: TaskDecomposer

    def __init__(self, decomposer: TaskDecomposer | None = None) -> None:
        self._decomposer = decomposer or TaskDecomposer()

    def create_from_text(self, task_description: str) -> Workflow:
        category = self._classify_task(task_description)
        template_builder = TEMPLATES.get(category)
        if template_builder is None:
            return self._create_default_workflow(task_description)
        template = template_builder()
        workflow = self._decomposer.decompose(template, task_description)
        workflow.description = task_description
        return workflow

    def _classify_task(self, task_description: str) -> TaskCategory:
        lowered = task_description.lower()
        if "web" in lowered or "flask" in lowered or "fastapi" in lowered:
            return TaskCategory.WEB_APPLICATION
        if "data" in lowered or "pipeline" in lowered or "csv" in lowered:
            return TaskCategory.DATA_PIPELINE
        if "game" in lowered or "游戏" in task_description:
            return TaskCategory.GAME
        return TaskCategory.LIBRARY

    def _create_default_workflow(self, task_description: str) -> Workflow:
        workflow = Workflow(description=task_description)
        for task in self._create_default_tasks(task_description):
            workflow.add_task(task)
        return workflow

    def _create_default_tasks(self, task_description: str) -> list[Task]:
        return [
            Task(
                task_id="requirements",
                objective=f"分析需求: {task_description}",
                capability=AgentCapability.PLANNING,
                dependencies=[],
            ),
            Task(
                task_id="implementation",
                objective="实现核心功能",
                capability=AgentCapability.CODE_GENERATION,
                dependencies=["requirements"],
            ),
            Task(
                task_id="review",
                objective="代码审查",
                capability=AgentCapability.CODE_REVIEW,
                dependencies=["implementation"],
            ),
        ]
