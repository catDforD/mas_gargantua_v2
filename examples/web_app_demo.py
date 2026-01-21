import asyncio

from mas.execution.engine import ExecutionEngine
from mas.output.reporter import WorkflowReporter
from mas.workflow.factory import WorkflowFactory


async def main() -> None:
    engine = ExecutionEngine(verbose=True)
    workflow = WorkflowFactory().create_from_text(
        "创建一个简单的 Flask API，包含用户登录功能"
    )
    result = await engine.run(workflow)
    reporter = WorkflowReporter(result, engine.tracker)
    reporter.print_summary()
    reporter.save_json("output/web_app_result.json")


if __name__ == "__main__":
    asyncio.run(main())
