from __future__ import annotations

from dataclasses import dataclass, field

from .schemas import AgentCapability, TaskResult, TaskStatus


@dataclass
class Task:
    task_id: str
    objective: str
    capability: AgentCapability
    dependencies: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: TaskResult | None = None
    metadata: dict[str, object] = field(default_factory=dict)

    def is_ready(self, completed_tasks: set[str]) -> bool:
        return all(dep in completed_tasks for dep in self.dependencies)

    def mark_running(self) -> None:
        self.status = TaskStatus.RUNNING

    def mark_completed(self, result: TaskResult) -> None:
        self.status = TaskStatus.COMPLETED
        self.result = result

    def mark_failed(
        self,
        error: str,
        start_time: float | None = None,
        end_time: float | None = None,
        agent_name: str | None = None,
    ) -> None:
        self.status = TaskStatus.FAILED
        self.result = TaskResult(
            task_id=self.task_id,
            success=False,
            error=error,
            start_time=start_time,
            end_time=end_time,
            agent_name=agent_name,
        )
