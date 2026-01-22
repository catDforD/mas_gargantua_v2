from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..context.manager import ContextManager


class AgentCapability(str, Enum):
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    FRONTEND = "frontend"
    BACKEND = "backend"
    DATA_ANALYSIS = "data_analysis"
    DOCUMENTATION = "documentation"
    PLANNING = "planning"
    GAME_DEV = "game_dev"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class HookType(str, Enum):
    PRE_TOOL_USE = "pre_tool_use"
    POST_TOOL_USE = "post_tool_use"
    ON_ERROR = "on_error"


class TaskCategory(str, Enum):
    WEB_APPLICATION = "web_application"
    DATA_PIPELINE = "data_pipeline"
    LIBRARY = "library"
    GAME = "game"


class PermissionDecision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"


ToolHandler = Callable[[dict[str, object]], object]


@dataclass
class AgentDescriptor:
    name: str
    capability: AgentCapability
    strategy: str
    model: str
    temperature: float
    system_prompt: str
    cost: str
    use_when: list[str] = field(default_factory=list)
    avoid_when: list[str] = field(default_factory=list)
    allowed_tools: list[str] = field(default_factory=list)
    resource_permissions: dict[str, object] = field(default_factory=dict)


@dataclass
class WorkflowStage:
    id: str
    name: str
    capability: AgentCapability
    dependencies: list[str] = field(default_factory=list)
    parallelizable: bool = False


@dataclass
class WorkflowTemplate:
    id: str
    name: str
    category: TaskCategory
    stages: list[WorkflowStage]


@dataclass
class TaskResult:
    task_id: str
    success: bool
    output: object | None = None
    error: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)
    start_time: float | None = None
    end_time: float | None = None
    agent_name: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "task_id": self.task_id,
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "metadata": self.metadata,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "agent_name": self.agent_name,
        }

    def to_json(self) -> str:
        import json

        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass
class WorkflowResult:
    success: bool
    task_results: dict[str, TaskResult]
    errors: dict[str, str] = field(default_factory=dict)
    total_duration_ms: float | None = None
    session_id: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "success": self.success,
            "task_results": {
                key: value.to_dict() for key, value in self.task_results.items()
            },
            "errors": self.errors,
            "total_duration_ms": self.total_duration_ms,
            "session_id": self.session_id,
        }

    def to_json(self) -> str:
        import json

        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def save(self, path: str) -> None:
        from pathlib import Path

        _ = Path(path).write_text(self.to_json(), encoding="utf-8")


@dataclass
class HookContext:
    agent_name: str
    tool_name: str
    params: dict[str, object]
    session_id: str
    timestamp: float


@dataclass
class HookResult:
    decision: PermissionDecision
    modified_params: dict[str, object] = field(default_factory=dict)
    message: str = ""
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass
class ToolResult:
    success: bool
    output: object | None = None
    error: str | None = None


@dataclass
class PermissionResult:
    decision: PermissionDecision
    reason: str = ""
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass
class ExecutionContext:
    original_task: str
    current_agent: str
    session_id: str
    plan_id: str | None = None
    results: dict[str, object] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)
    _context_manager: ContextManager | None = field(default=None, repr=False)

    def get_context_manager(self) -> ContextManager:
        """获取上下文管理器，如果不存在则创建一个新的。

        Returns:
            ContextManager: 上下文管理器实例。
        """

        if self._context_manager is None:
            from ..context.manager import ContextManager

            self._context_manager = ContextManager(self.session_id)
        return self._context_manager

    def set_context_manager(self, manager: ContextManager) -> None:
        """设置上下文管理器。

        Args:
            manager: 要设置的上下文管理器实例。
        """

        self._context_manager = manager
