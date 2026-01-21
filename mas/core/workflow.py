from __future__ import annotations

from dataclasses import dataclass, field

from .schemas import TaskStatus
from .task import Task


@dataclass
class Workflow:
    tasks: dict[str, Task] = field(default_factory=dict)
    description: str = ""

    def add_task(self, task: Task) -> None:
        if task.task_id in self.tasks:
            raise ValueError(f"Task already exists: {task.task_id}")
        self.tasks[task.task_id] = task

    def get_task(self, task_id: str) -> Task:
        if task_id not in self.tasks:
            raise KeyError(f"Task not found: {task_id}")
        return self.tasks[task_id]

    def get_ready_tasks(self) -> list[Task]:
        completed = {
            task_id
            for task_id, task in self.tasks.items()
            if task.status == TaskStatus.COMPLETED
        }
        return [
            task
            for task in self.tasks.values()
            if task.is_ready(completed) and task.status == TaskStatus.PENDING
        ]

    def mark_done(self, task_id: str) -> None:
        task = self.get_task(task_id)
        if task.status == TaskStatus.COMPLETED:
            return
        if task.result is None:
            raise ValueError(f"Task result missing: {task_id}")

    def all_completed(self) -> bool:
        return all(task.status == TaskStatus.COMPLETED for task in self.tasks.values())
