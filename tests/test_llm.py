import os
from mas.llm.client import LLMClient
from dotenv import load_dotenv
load_dotenv()

# 检查 API Key
if not os.getenv("MINIMAX_API_KEY"):
    print("⚠️ MINIMAX_API_KEY 未设置，跳过 LLM 测试")
else:
    client = LLMClient()

    # 同步调用
    response = client.complete("Say 'Hello, MAS!'")
    print(f"✅ LLM 响应: {response[:50]}...")

    # 异步调用
    import asyncio
    response = asyncio.run(client.acomplete("What is 2+2?"))
    print(f"✅ 异步 LLM 响应: {response[:50]}...")

import asyncio
import os
from mas import run_task

if not os.getenv("MINIMAX_API_KEY"):
    print("⚠️ 跳过带 LLM 的完整执行测试")
else:
    result = asyncio.run(run_task("创建一个简单的待办事项 API"))
    print(f"✅ 完整执行: success={result.success}")
    for task_id, task_result in result.task_results.items():
        if task_result.output:
            print(f"   {task_id}: {str(task_result.output)[:100]}...")