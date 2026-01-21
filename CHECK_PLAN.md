# MAS_V2 项目功能检查计划

本文档提供逐步指南，帮助你检查和测试 MAS_V2 项目的各项功能。

---

## 一、环境准备

### 1.1 安装依赖

```bash
# 进入项目目录
cd /home/gargantua/code/mas_safe/mas_v2

# 安装核心依赖
pip install -e .

# 安装开发依赖（包含测试工具）
pip install -e ".[dev]"

# 可选：安装 MCP 支持
pip install -e ".[mcp]"
```

### 1.2 设置环境变量

```bash
# 设置 MiniMax API Key（LLM 调用需要）
export MINIMAX_API_KEY="your_api_key_here"

# 或创建 .env 文件
echo 'MINIMAX_API_KEY=your_api_key_here' > .env
```

### 1.3 验证安装

```bash
# 检查包是否正确安装
python -c "import mas; print('MAS_V2 installed successfully')"
```

**预期结果**: 输出 `MAS_V2 installed successfully`

---

## 二、模块导入检查

### 2.1 核心模块导入

```python
# 在 Python REPL 或脚本中执行
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
```

### 2.2 智能体模块导入

```python
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
```

### 2.3 工作流模块导入

```python
from mas.workflow.factory import WorkflowFactory
from mas.workflow.decomposer import TaskDecomposer
from mas.workflow.templates import TEMPLATES
print(f"✅ workflow 模块导入成功（{len(TEMPLATES)} 个模板）")
```

### 2.4 其他模块导入

```python
from mas.execution.engine import ExecutionEngine
from mas.permissions.manager import PermissionManager
from mas.hooks.manager import HookManager
from mas.tools.registry import ToolRegistry
from mas.llm.client import LLMClient
print("✅ 所有模块导入成功")
```

**检查清单**:
- [√] core 模块（schemas, task, workflow）
- [√] agents 模块（pool, 7 个 implementations）
- [√] workflow 模块（factory, decomposer, 4 个 templates）
- [√] execution 模块（engine, scheduler, runner）
- [√] permissions 模块（config, manager, validators）
- [√] hooks 模块（types, manager, 3 个 builtin hooks）
- [√] tools 模块（registry, mcp_client, builtin）
- [√] llm 模块（client）
- [√] utils 模块（config, logger）

---

## 三、核心数据结构测试

### 3.1 Task 类测试

```python
from mas.core.task import Task
from mas.core.schemas import AgentCapability, TaskStatus, TaskResult

# 创建任务
task = Task(
    task_id="test_task_1",
    objective="测试任务",
    capability=AgentCapability.CODE_GENERATION,
    dependencies=[]
)

# 检查初始状态
assert task.status == TaskStatus.PENDING, "任务初始状态应为 PENDING"
print(f"✅ Task 创建成功: {task.task_id}, 状态: {task.status}")

# 测试状态转换
task.mark_running()
assert task.status == TaskStatus.RUNNING, "状态应转为 RUNNING"
print(f"✅ 状态转换成功: {task.status}")

# 测试完成
result = TaskResult(task_id="test_task_1", success=True, output="done")
task.mark_completed(result)
assert task.status == TaskStatus.COMPLETED, "状态应转为 COMPLETED"
print(f"✅ 任务完成: {task.status}")
```

### 3.2 Workflow 类测试

```python
from mas.core.workflow import Workflow
from mas.core.task import Task
from mas.core.schemas import AgentCapability

# 创建工作流
workflow = Workflow()

# 添加任务
task1 = Task("task1", "任务1", AgentCapability.PLANNING, [])
task2 = Task("task2", "任务2", AgentCapability.BACKEND, ["task1"])
task3 = Task("task3", "任务3", AgentCapability.FRONTEND, ["task1"])

workflow.add_task(task1)
workflow.add_task(task2)
workflow.add_task(task3)

# 检查任务数量
assert len(workflow.tasks) == 3, "应有 3 个任务"
print(f"✅ Workflow 创建成功，任务数: {len(workflow.tasks)}")

# 获取就绪任务（无依赖的任务）
ready = workflow.get_ready_tasks()
assert len(ready) == 1, "应有 1 个就绪任务"
assert ready[0].task_id == "task1", "task1 应为就绪任务"
print(f"✅ 就绪任务检测正确: {[t.task_id for t in ready]}")
```

**检查清单**:
- [√] Task 创建和状态转换
- [√] Workflow 任务添加和依赖管理
- [√] get_ready_tasks() 正确返回就绪任务

---

## 四、智能体池测试

### 4.1 智能体注册

```python
from mas.agents.pool import AgentPoolRegistry
from mas.agents.implementations import (
    backend_descriptor,
    code_generation_descriptor,
    frontend_descriptor,
    planning_descriptor,
    game_dev_descriptor,
)
from mas.core.schemas import AgentCapability

# 获取单例
pool = AgentPoolRegistry()

# 注册智能体
pool.register(backend_descriptor())
pool.register(code_generation_descriptor())
pool.register(frontend_descriptor())
pool.register(planning_descriptor())
pool.register(game_dev_descriptor())

print(f"✅ 已注册 {len(pool._pools)} 个智能体")
```

### 4.2 智能体选择

```python
# 按能力选择智能体
agent = pool.select_best_agent(AgentCapability.BACKEND, {})
print(f"✅ 选择后端智能体: {agent.name}, 策略: {agent.strategy}")

agent = pool.select_best_agent(AgentCapability.PLANNING, {})
print(f"✅ 选择规划智能体: {agent.name}, 策略: {agent.strategy}")

# 测试未注册能力
try:
    pool.select_best_agent(AgentCapability.DOCUMENTATION, {})
    print("❌ 应该抛出 LookupError")
except LookupError as e:
    print(f"✅ 正确处理未注册能力: {e}")
```

**检查清单**:
- [√] AgentPoolRegistry 单例模式
- [√] 智能体注册功能
- [√] 按能力选择智能体
- [√] 处理未注册能力

---

## 五、工作流模板测试

### 5.1 查看可用模板

```python
from mas.workflow.templates import TEMPLATES
from mas.core.schemas import TaskCategory

print("可用模板:")
for category, builder in TEMPLATES.items():
    template = builder()
    print(f"  - {category.value}: {template.name} ({len(template.stages)} 个阶段)")
```

**预期输出**:
```
可用模板:
  - web_application: Web Application Development (5 个阶段)
  - data_pipeline: Data Pipeline Development (4 个阶段)
  - game: Game Development (4 个阶段)
  - library: Library Development (4 个阶段)
```

### 5.2 工作流生成测试

```python
from mas.workflow.factory import WorkflowFactory

factory = WorkflowFactory()

# 测试 Web 应用模板
workflow = factory.create_from_text("创建一个 Flask 后端 API")
print(f"✅ Web 应用工作流: {len(workflow.tasks)} 个任务")

# 测试数据管道模板
workflow = factory.create_from_text("处理 CSV 数据并生成报告")
print(f"✅ 数据管道工作流: {len(workflow.tasks)} 个任务")

# 测试游戏模板
workflow = factory.create_from_text("开发一个贪吃蛇游戏")
print(f"✅ 游戏工作流: {len(workflow.tasks)} 个任务")
```

### 5.3 循环依赖检测

```python
from mas.workflow.decomposer import TaskDecomposer
from mas.core.schemas import WorkflowTemplate, WorkflowStage, TaskCategory, AgentCapability

decomposer = TaskDecomposer()

# 测试正常模板
normal_template = WorkflowTemplate(
    id="test",
    name="Test",
    category=TaskCategory.WEB_APPLICATION,
    stages=[
        WorkflowStage("a", "A", AgentCapability.PLANNING, []),
        WorkflowStage("b", "B", AgentCapability.BACKEND, ["a"]),
    ]
)
workflow = decomposer.decompose(normal_template, "测试")
print(f"✅ 正常模板分解成功")

# 测试循环依赖检测
cyclic_template = WorkflowTemplate(
    id="cyclic",
    name="Cyclic",
    category=TaskCategory.WEB_APPLICATION,
    stages=[
        WorkflowStage("a", "A", AgentCapability.PLANNING, ["b"]),
        WorkflowStage("b", "B", AgentCapability.BACKEND, ["a"]),
    ]
)
try:
    decomposer.decompose(cyclic_template, "测试")
    print("❌ 应该检测到循环依赖")
except ValueError as e:
    print(f"✅ 循环依赖检测正确: {e}")
```

**检查清单**:
- [√] 4 个工作流模板可用
- [√] WorkflowFactory 正确分类任务
- [√] TaskDecomposer 正确分解模板
- [√] 循环依赖检测正常工作

---

## 六、权限管理测试

### 6.1 工具级别权限

```python
from mas.permissions.manager import PermissionManager
from mas.permissions.config import PermissionConfig
from mas.core.schemas import PermissionDecision

# 测试工具黑名单
config = PermissionConfig(
    tool_blacklist={"coder": ["file_write", "code_exec"]}
)
manager = PermissionManager(config)

# 被禁止的工具
result = manager.check_tool_permission("coder", "file_write", {})
assert result.decision == PermissionDecision.DENY
print(f"✅ 工具黑名单生效: file_write 被拒绝")

# 允许的工具
result = manager.check_tool_permission("coder", "file_read", {})
assert result.decision == PermissionDecision.ALLOW
print(f"✅ 未禁止的工具允许: file_read")
```

### 6.2 资源级别权限

```python
from mas.permissions.config import FileAccessConfig

# 测试文件路径限制
config = PermissionConfig(
    file_access=FileAccessConfig(
        allowed_paths=["/home/user/project"],
        denied_paths=["/etc", "/root"],
    )
)
manager = PermissionManager(config)

# 允许的路径
result = manager.check_resource_permission("agent", "file", "/home/user/project/src/main.py")
print(f"✅ 允许路径检测: {result.decision}")

# 禁止的路径
result = manager.check_resource_permission("agent", "file", "/etc/passwd")
assert result.decision == PermissionDecision.DENY
print(f"✅ 禁止路径检测: /etc/passwd 被拒绝")
```

**检查清单**:
- [√] 工具白名单/黑名单
- [√] 文件路径允许/禁止
- [√] 路径规范化和前缀匹配

---

## 七、Hooks 系统测试

### 7.1 Hook 注册和执行

```python
import asyncio
from mas.hooks.manager import HookManager
from mas.core.schemas import HookType, HookContext, HookResult, PermissionDecision

manager = HookManager()

# 自定义 Hook
async def custom_hook(context: HookContext) -> HookResult:
    print(f"  Hook 触发: {context.tool_name} by {context.agent_name}")
    return HookResult(decision=PermissionDecision.ALLOW)

# 注册 Hook
manager.register(HookType.PRE_TOOL_USE, custom_hook)

# 执行 Hook
context = HookContext(
    agent_name="test_agent",
    tool_name="test_tool",
    params={},
    session_id="session-1",
    timestamp=0.0,
)

result = asyncio.run(manager.execute_pre_tool_use(context))
print(f"✅ Hook 执行成功: {result.decision}")
```

### 7.2 Hook 链短路测试

```python
async def deny_hook(context: HookContext) -> HookResult:
    return HookResult(decision=PermissionDecision.DENY, message="Denied by hook")

async def allow_hook(context: HookContext) -> HookResult:
    print("  这条不应该执行")
    return HookResult(decision=PermissionDecision.ALLOW)

manager2 = HookManager()
manager2.register(HookType.PRE_TOOL_USE, deny_hook)
manager2.register(HookType.PRE_TOOL_USE, allow_hook)

result = asyncio.run(manager2.execute_pre_tool_use(context))
assert result.decision == PermissionDecision.DENY
print(f"✅ Hook 链短路正确: {result.message}")
```

### 7.3 内置 Hook 测试

```python
from mas.hooks.builtin.permission_check import permission_check_hook
from mas.hooks.builtin.input_validation import input_validation_hook
from mas.hooks.builtin.audit_log import audit_log_hook

# 测试输入验证 Hook
empty_context = HookContext(
    agent_name="agent",
    tool_name="",  # 空工具名
    params={},
    session_id="s1",
    timestamp=0.0,
)
result = asyncio.run(input_validation_hook(empty_context))
assert result.decision == PermissionDecision.DENY
print(f"✅ input_validation_hook 拒绝空 tool_name")

# 测试审计日志 Hook
result = asyncio.run(audit_log_hook(context))
print(f"✅ audit_log_hook 执行成功")
```

**检查清单**:
- [√] Hook 注册功能
- [√] PreToolUse Hook 链执行
- [√] Hook 链短路（遇 deny 立即返回）
- [√] 3 个内置 Hook 正常工作

---

## 八、执行引擎测试

### 8.1 基本执行测试（无 LLM）

```python
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
```

### 8.2 并行执行验证

```python
from mas.core.workflow import Workflow
from mas.core.task import Task
from mas.core.schemas import AgentCapability

# 创建有并行任务的工作流
workflow = Workflow()
workflow.add_task(Task("root", "根任务", AgentCapability.PLANNING, []))
workflow.add_task(Task("branch1", "分支1", AgentCapability.BACKEND, ["root"]))
workflow.add_task(Task("branch2", "分支2", AgentCapability.FRONTEND, ["root"]))
workflow.add_task(Task("merge", "合并", AgentCapability.CODE_REVIEW, ["branch1", "branch2"]))

# 执行
result = asyncio.run(engine.run(workflow))
print(f"✅ 并行执行测试: success={result.success}")
print(f"   完成任务: {list(result.task_results.keys())}")
```

### 8.3 任务间上下文传递验证 ⭐ 新增

验证依赖任务的输出会自动传递给后续任务。

```python
import asyncio
from dotenv import load_dotenv
load_dotenv()

from mas.execution.engine import ExecutionEngine
from mas.workflow.factory import WorkflowFactory
from mas.logging.events import LogEvent

async def test_context_passing():
    engine = ExecutionEngine(verbose=False)
    workflow = WorkflowFactory().create_from_text('写一个 hello world 程序')
    result = await engine.run(workflow)

    # 检查 tracker 中记录的 LLM_REQUEST
    print('检查 prompt 中是否包含依赖任务输出:')
    for record in engine.tracker.records:
        if record.event == LogEvent.LLM_REQUEST:
            task_id = record.task_id
            prompt = record.data.get('prompt', '')

            if task_id in ['implementation', 'review']:
                has_context = '前置任务的输出' in prompt
                print(f'  [{task_id}] 包含前置任务输出: {has_context}')
                assert has_context, f"{task_id} 应该包含前置任务输出"

    print("✅ 任务间上下文传递验证通过")

asyncio.run(test_context_passing())
```

**预期输出**:
```
检查 prompt 中是否包含依赖任务输出:
  [implementation] 包含前置任务输出: True
  [review] 包含前置任务输出: True
✅ 任务间上下文传递验证通过
```

**检查清单**:
- [√] ExecutionEngine 初始化
- [√] 工作流执行
- [√] 任务依赖顺序正确
- [√] 并行任务正确调度
- [√] 任务间上下文传递（依赖任务输出自动传递）

---

## 九、LLM 集成测试（需要 API Key）

### 9.1 LLM 客户端测试

```python
import os
from mas.llm.client import LLMClient

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
```

### 9.2 带 LLM 的完整执行

```python
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
```

**检查清单**:
- [√] LLMClient 同步调用
- [√] LLMClient 异步调用
- [√] API 错误处理
- [√] 完整流程 LLM 集成

---

## 十、运行示例和自动测试

### 10.1 运行示例文件

```bash
# Web 应用示例
python examples/web_app_demo.py

# 数据管道示例
python examples/data_pipeline_demo.py

# 游戏示例
python examples/game_demo.py
```

### 10.2 运行 pytest 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行单个测试
pytest tests/test_basic.py::test_basic_run_task -v

# 带覆盖率
pytest tests/ -v --cov=mas --cov-report=term-missing
```

### 10.3 代码质量检查

```bash
# Ruff 代码检查
ruff check mas/

# Mypy 类型检查
mypy mas/ --ignore-missing-imports

# 格式化检查
ruff format mas/ --check
```

**预期结果**:
- pytest: 3/3 通过
- mypy: 0 个错误
- ruff: 少量代码风格建议（非阻塞）

---

## 十一、检查总结清单

### 核心功能
- [ ] 模块导入无错误
- [ ] Task/Workflow 数据结构正常
- [ ] 智能体注册和选择
- [ ] 工作流模板生成
- [ ] 循环依赖检测

### 安全功能
- [ ] 工具级权限（白名单/黑名单）
- [ ] 资源级权限（文件路径）
- [ ] Hook 系统拦截

### 执行功能
- [ ] 执行引擎运行
- [ ] 任务调度正确
- [ ] 并行任务执行
- [ ] 任务间上下文传递

### 集成功能
- [ ] LLM 调用（需 API Key）
- [ ] 端到端测试

### 代码质量
- [ ] pytest 测试通过
- [ ] mypy 类型检查通过
- [ ] ruff 代码检查

---

## 十二、常见问题

### Q1: 模块导入失败
```
ModuleNotFoundError: No module named 'mas'
```
**解决**: 运行 `pip install -e .`

### Q2: LLM 测试失败
```
ValueError: MINIMAX_API_KEY is not set
```
**解决**: 设置环境变量 `export MINIMAX_API_KEY=your_key`

### Q3: 测试失败
```
async def functions are not natively supported
```
**解决**: 安装 pytest-asyncio `pip install pytest-asyncio`

### Q4: 权限测试路径不匹配
**原因**: 路径规范化使用 `os.path.realpath()`，相对路径会被转换
**解决**: 使用绝对路径测试

---

**检查计划完成** ✅
