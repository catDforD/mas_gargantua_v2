from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class LogEvent(str, Enum):
    WORKFLOW_START = "workflow_start"
    WORKFLOW_END = "workflow_end"
    TASK_START = "task_start"
    TASK_END = "task_end"
    AGENT_SELECTED = "agent_selected"
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"
    HOOK_EXECUTED = "hook_executed"
    ERROR_OCCURRED = "error_occurred"


@dataclass
class LogRecord:
    event: LogEvent
    timestamp: float
    session_id: str
    task_id: str | None
    agent_name: str | None
    data: dict[str, object]
    duration_ms: float | None = None
