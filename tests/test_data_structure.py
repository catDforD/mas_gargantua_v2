# ## Task 测试
# from mas.core.task import Task
# from mas.core.schemas import AgentCapability, TaskStatus, TaskResult

# # 创建任务
# task = Task(
#     task_id="test_task_1",
#     objective="测试任务",
#     capability=AgentCapability.CODE_GENERATION,
#     dependencies=[]
# )

# # 检查初始状态
# assert task.status == TaskStatus.PENDING, "任务初始状态应为 PENDING"
# print(f"✅ Task 创建成功: {task.task_id}, 状态: {task.status}")

# # 测试状态转换
# task.mark_running()
# assert task.status == TaskStatus.RUNNING, "状态应转为 RUNNING"
# print(f"✅ 状态转换成功: {task.status}")

# # 测试完成
# result = TaskResult(task_id="test_task_1", success=True, output="done")
# task.mark_completed(result)
# assert task.status == TaskStatus.COMPLETED, "状态应转为 COMPLETED"
# print(f"✅ 任务完成: {task.status}")



# ## Workflow 测试
# from mas.core.workflow import Workflow
# from mas.core.task import Task
# from mas.core.schemas import AgentCapability

# # 创建工作流
# workflow = Workflow()

# # 添加任务
# task1 = Task("task1", "任务1", AgentCapability.PLANNING, [])
# task2 = Task("task2", "任务2", AgentCapability.BACKEND, ["task1"])
# task3 = Task("task3", "任务3", AgentCapability.FRONTEND, ["task1"])

# workflow.add_task(task1)
# workflow.add_task(task2)
# workflow.add_task(task3)

# # 检查任务数量
# assert len(workflow.tasks) == 3, "应有 3 个任务"
# print(f"✅ Workflow 创建成功，任务数: {len(workflow.tasks)}")

# # 获取就绪任务（无依赖的任务）
# ready = workflow.get_ready_tasks()
# assert len(ready) == 1, "应有 1 个就绪任务"
# assert ready[0].task_id == "task1", "task1 应为就绪任务"
# print(f"✅ 就绪任务检测正确: {[t.task_id for t in ready]}")