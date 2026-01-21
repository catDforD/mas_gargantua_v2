from .core.schemas import WorkflowResult
from .execution.engine import ExecutionEngine
from .workflow.factory import WorkflowFactory


async def run_task(task_description: str, verbose: bool = False) -> WorkflowResult:
    workflow = WorkflowFactory().create_from_text(task_description)
    engine = ExecutionEngine(verbose=verbose)
    result = await engine.run(workflow)
    return result


__all__ = ["run_task", "ExecutionEngine", "WorkflowFactory", "WorkflowResult"]
