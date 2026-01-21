from __future__ import annotations

from ..core.schemas import WorkflowTemplate
from ..core.task import Task
from ..core.workflow import Workflow


class TaskDecomposer:
    def decompose(self, template: WorkflowTemplate, task_description: str) -> Workflow:
        self._validate_dependencies(template)
        workflow = Workflow(description=task_description)
        for stage in template.stages:
            task = Task(
                task_id=stage.id,
                objective=f"{stage.name}: {task_description}",
                capability=stage.capability,
                dependencies=list(stage.dependencies),
            )
            workflow.add_task(task)
        return workflow

    def _validate_dependencies(self, template: WorkflowTemplate) -> None:
        stage_ids = {stage.id for stage in template.stages}
        if len(stage_ids) != len(template.stages):
            raise ValueError("Duplicate stage id detected")
        for stage in template.stages:
            for dependency in stage.dependencies:
                if dependency not in stage_ids:
                    raise ValueError("Unknown dependency detected")
        if self._has_cycle(template):
            raise ValueError("Cyclic dependency detected")

    def _has_cycle(self, template: WorkflowTemplate) -> bool:
        edges: dict[str, set[str]] = {
            stage.id: set(stage.dependencies) for stage in template.stages
        }
        state: dict[str, int] = {stage.id: 0 for stage in template.stages}

        def visit(node: str) -> bool:
            if state[node] == 1:
                return True
            if state[node] == 2:
                return False
            state[node] = 1
            for dependency in edges[node]:
                if dependency in edges and visit(dependency):
                    return True
            state[node] = 2
            return False

        return any(visit(node) for node in edges)
