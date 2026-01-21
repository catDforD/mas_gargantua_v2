import asyncio

from dotenv import load_dotenv
from mas.execution.engine import ExecutionEngine
from mas.output.reporter import WorkflowReporter
from mas.workflow.factory import WorkflowFactory

load_dotenv()


async def main() -> None:
    engine = ExecutionEngine(verbose=True)
    workflow = WorkflowFactory().create_from_text("构建一个 CSV 数据清洗与统计分析管道")
    result = await engine.run(workflow)
    reporter = WorkflowReporter(result, engine.tracker)
    reporter.print_summary()
    reporter.save_json("output/data_pipeline_result.json")


if __name__ == "__main__":
    asyncio.run(main())
