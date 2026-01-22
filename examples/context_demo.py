"""演示上下文管理功能的工作流测试。"""

import asyncio
import json

from mas.execution.engine import ExecutionEngine
from mas.output.reporter import WorkflowReporter
from mas.workflow.factory import WorkflowFactory
from dotenv import load_dotenv
load_dotenv()

async def main() -> None:
    print("=" * 60)
    print("MAS_V2 上下文管理功能演示")
    print("=" * 60)

    # 创建执行引擎
    engine = ExecutionEngine(verbose=True, context_max_tokens=8000)

    # 创建一个多阶段工作流来测试上下文传递
    workflow = WorkflowFactory().create_from_text(
        "设计并实现一个简单的待办事项 API，包含增删改查功能"
    )

    print(f"\n工作流任务数: {len(workflow.tasks)}")
    print("任务列表:")
    for task_id, task in workflow.tasks.items():
        deps = f" (依赖: {task.dependencies})" if task.dependencies else ""
        print(f"  - {task_id}: {task.objective[:50]}...{deps}")

    print("\n" + "-" * 60)
    print("开始执行工作流...")
    print("-" * 60 + "\n")

    # 执行工作流
    result = await engine.run(workflow)

    # 打印上下文管理统计
    print("\n" + "=" * 60)
    print("上下文管理统计")
    print("=" * 60)

    stats = engine.context_manager.get_stats()
    print(f"会话 ID: {stats['session_id'][:8]}...")
    print(f"总条目数: {stats['total_entries']}")
    print(f"Token 估算: {stats['token_estimate']}")
    print("\n各层条目数:")
    for layer, count in stats["layer_counts"].items():
        print(f"  - {layer}: {count}")

    # 打印上下文存储内容
    print("\n" + "-" * 60)
    print("任务层上下文条目:")
    print("-" * 60)

    from mas.context.types import ContextLayer

    task_layer = engine.context_manager.store.get_layer(ContextLayer.TASK)
    for key, entry in task_layer.items():
        content_preview = str(entry.content)[:100] + "..." if len(str(entry.content)) > 100 else str(entry.content)
        compressed_mark = " [已压缩]" if entry.is_compressed else ""
        print(f"\n[{entry.type.value}] {entry.source}{compressed_mark}")
        print(f"  重要性: {entry.importance:.2f}, 相关性: {entry.relevance_score:.2f}")
        print(f"  访问次数: {entry.access_count}")
        print(f"  内容预览: {content_preview}")

    # 打印工作流结果摘要
    print("\n" + "=" * 60)
    print("工作流执行结果")
    print("=" * 60)

    reporter = WorkflowReporter(result, engine.tracker)
    reporter.print_summary()

    # 保存详细结果
    output_path = "output/context_demo_result.json"
    reporter.save_json(output_path)
    print(f"\n详细结果已保存到: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
