from __future__ import annotations

from ..core.schemas import TaskResult
from ..core.task import Task


class TaskRunner:
    async def run(self, task: Task) -> TaskResult:
        output = f"Executed task: {task.objective}"
        return TaskResult(task_id=task.task_id, success=True, output=output)
