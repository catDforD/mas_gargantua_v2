# 基本执行测试（无 LLM）
import asyncio
from mas.execution.engine import ExecutionEngine
from mas.workflow.factory import WorkflowFactory

# 创建引擎（不设置 API Key 时使用占位输出）
engine = ExecutionEngine()
factory = WorkflowFactory()

# 创建简单工作流
workflow = factory.create_from_text("创建一个简单的 Flask API")

# 执行
result = asyncio.run(engine.run(workflow))
print(f"✅ 执行完成: success={result.success}")
print(f"   任务结果数: {len(result.task_results)}")
for task_id, task_result in result.task_results.items():
    print(f"   - {task_id}: {task_result.success}")

## 并行执行验证
from mas.core.workflow import Workflow
from mas.core.task import Task
from mas.core.schemas import AgentCapability

# 创建有并行任务的工作流
workflow = Workflow(description="并行执行验证")
workflow.add_task(Task("root", "根任务", AgentCapability.PLANNING, []))
workflow.add_task(Task("branch1", "分支1", AgentCapability.BACKEND, ["root"]))
workflow.add_task(Task("branch2", "分支2", AgentCapability.FRONTEND, ["root"]))
workflow.add_task(
    Task("merge", "合并", AgentCapability.CODE_REVIEW, ["branch1", "branch2"])
)

# 执行
result = asyncio.run(engine.run(workflow))
print(f"✅ 并行执行测试: success={result.success}")
print(f"   完成任务: {list(result.task_results.keys())}")
