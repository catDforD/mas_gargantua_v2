## workflow_template
# from mas.workflow.templates import TEMPLATES
# from mas.core.schemas import TaskCategory

# print("可用模板:")
# for category, builder in TEMPLATES.items():
#     template = builder()
#     print(f"  - {category.value}: {template.name} ({len(template.stages)} 个阶段)")

# ## Workflow generation test

# from mas.workflow.factory import WorkflowFactory

# factory = WorkflowFactory()

# # 测试 Web 应用模板
# workflow = factory.create_from_text("创建一个 Flask 后端 API")
# print(f"✅ Web 应用工作流: {len(workflow.tasks)} 个任务")

# # 测试数据管道模板
# workflow = factory.create_from_text("处理 CSV 数据并生成报告")
# print(f"✅ 数据管道工作流: {len(workflow.tasks)} 个任务")

# # 测试游戏模板
# workflow = factory.create_from_text("开发一个贪吃蛇游戏")
# print(f"✅ 游戏工作流: {len(workflow.tasks)} 个任务")


# ## Circular dependency detection
# from mas.workflow.decomposer import TaskDecomposer
# from mas.core.schemas import WorkflowTemplate, WorkflowStage, TaskCategory, AgentCapability

# decomposer = TaskDecomposer()

# # 测试正常模板
# normal_template = WorkflowTemplate(
#     id="test",
#     name="Test",
#     category=TaskCategory.WEB_APPLICATION,
#     stages=[
#         WorkflowStage("a", "A", AgentCapability.PLANNING, []),
#         WorkflowStage("b", "B", AgentCapability.BACKEND, ["a"]),
#     ]
# )
# workflow = decomposer.decompose(normal_template, "测试")
# print(f"✅ 正常模板分解成功")

# # 测试循环依赖检测
# cyclic_template = WorkflowTemplate(
#     id="cyclic",
#     name="Cyclic",
#     category=TaskCategory.WEB_APPLICATION,
#     stages=[
#         WorkflowStage("a", "A", AgentCapability.PLANNING, ["b"]),
#         WorkflowStage("b", "B", AgentCapability.BACKEND, ["a"]),
#     ]
# )
# try:
#     decomposer.decompose(cyclic_template, "测试")
#     print("❌ 应该检测到循环依赖")
# except ValueError as e:
#     print(f"✅ 循环依赖检测正确: {e}")