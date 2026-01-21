from mas.core.schemas import (
    AgentCapability,
    TaskStatus,
    HookType,
    TaskCategory,
    PermissionDecision,
    AgentDescriptor,
    WorkflowStage,
    WorkflowTemplate,
    TaskResult,
    WorkflowResult,
    HookContext,
    HookResult,
    ToolResult,
    PermissionResult,
    ExecutionContext,
)
print("✅ core/schemas 导入成功")

from mas.core.task import Task
print("✅ core/task 导入成功")

from mas.core.workflow import Workflow
print("✅ core/workflow 导入成功")

from mas.agents.pool import AgentPoolRegistry
print("✅ agents/pool 导入成功")

from mas.agents.implementations import (
    backend_descriptor,
    code_generation_descriptor,
    code_review_descriptor,
    data_analysis_descriptor,
    frontend_descriptor,
    game_dev_descriptor,
    planning_descriptor,
)
print("✅ agents/implementations 导入成功（7 个智能体）")

from mas.workflow.factory import WorkflowFactory
from mas.workflow.decomposer import TaskDecomposer
from mas.workflow.templates import TEMPLATES
print(f"✅ workflow 模块导入成功（{len(TEMPLATES)} 个模板）")


from mas.execution.engine import ExecutionEngine
from mas.permissions.manager import PermissionManager
from mas.hooks.manager import HookManager
from mas.tools.registry import ToolRegistry
from mas.llm.client import LLMClient
print("✅ 所有模块导入成功")