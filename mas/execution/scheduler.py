from __future__ import annotations

from ..core.schemas import TaskStatus
from ..core.task import Task
from ..core.workflow import Workflow


class TaskScheduler:
    def get_ready_tasks(self, workflow: Workflow) -> list[Task]:
        return workflow.get_ready_tasks()

    def has_pending_tasks(self, workflow: Workflow) -> bool:
        return any(
            task.status == TaskStatus.PENDING for task in workflow.tasks.values()
        )
