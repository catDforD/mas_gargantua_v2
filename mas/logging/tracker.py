from __future__ import annotations

import json
import time
from dataclasses import asdict
from pathlib import Path

from ..core.schemas import TaskResult, WorkflowResult
from .events import LogEvent, LogRecord


class ExecutionTracker:
    session_id: str
    records: list[LogRecord]
    _timers: dict[str, float]

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.records = []
        self._timers = {}
        self.session_id = self.session_id

    def log_workflow_start(self, task_description: str) -> None:
        self._timers["workflow"] = time.time()
        self._add_record(
            LogEvent.WORKFLOW_START,
            task_id=None,
            agent_name=None,
            data={"task_description": task_description},
        )

    def log_workflow_end(self, result: WorkflowResult) -> None:
        duration_ms = self._pop_timer_ms("workflow")
        self._add_record(
            LogEvent.WORKFLOW_END,
            task_id=None,
            agent_name=None,
            data={"success": result.success, "errors": result.errors},
            duration_ms=duration_ms,
        )

    def log_task_start(self, task_id: str, agent_name: str) -> None:
        self._timers[task_id] = time.time()
        self._add_record(
            LogEvent.TASK_START,
            task_id=task_id,
            agent_name=agent_name,
            data={},
        )

    def log_agent_selected(self, task_id: str, agent_name: str) -> None:
        self._add_record(
            LogEvent.AGENT_SELECTED,
            task_id=task_id,
            agent_name=agent_name,
            data={},
        )

    def log_llm_request(self, task_id: str, agent_name: str, prompt: str) -> None:
        self._add_record(
            LogEvent.LLM_REQUEST,
            task_id=task_id,
            agent_name=agent_name,
            data={"prompt": prompt},
        )

    def log_llm_response(self, task_id: str, agent_name: str, response: str) -> None:
        self._add_record(
            LogEvent.LLM_RESPONSE,
            task_id=task_id,
            agent_name=agent_name,
            data={"response": response},
        )

    def log_task_end(self, task_id: str, result: TaskResult) -> None:
        duration_ms = self._pop_timer_ms(task_id)
        self._add_record(
            LogEvent.TASK_END,
            task_id=task_id,
            agent_name=result.agent_name,
            data={"success": result.success, "error": result.error},
            duration_ms=duration_ms,
        )

    def log_hook_executed(
        self,
        task_id: str | None,
        agent_name: str | None,
        tool_name: str,
        decision: str,
        message: str,
    ) -> None:
        self._add_record(
            LogEvent.HOOK_EXECUTED,
            task_id=task_id,
            agent_name=agent_name,
            data={"tool_name": tool_name, "decision": decision, "message": message},
        )

    def log_error(self, task_id: str | None, error: Exception) -> None:
        self._add_record(
            LogEvent.ERROR_OCCURRED,
            task_id=task_id,
            agent_name=None,
            data={"error": str(error)},
        )

    def get_summary(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "total_events": len(self.records),
            "event_counts": self._count_events(),
        }

    def export_json(self, path: str) -> None:
        payload = [asdict(record) for record in self.records]
        _ = Path(path).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _add_record(
        self,
        event: LogEvent,
        task_id: str | None,
        agent_name: str | None,
        data: dict[str, object],
        duration_ms: float | None = None,
    ) -> None:
        record = LogRecord(
            event=event,
            timestamp=time.time(),
            session_id=self.session_id,
            task_id=task_id,
            agent_name=agent_name,
            data=data,
            duration_ms=duration_ms,
        )
        self.records.append(record)

    def _pop_timer_ms(self, key: str) -> float | None:
        start = self._timers.pop(key, None)
        if start is None:
            return None
        return (time.time() - start) * 1000

    def _count_events(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for record in self.records:
            counts[record.event.value] = counts.get(record.event.value, 0) + 1
        return counts
