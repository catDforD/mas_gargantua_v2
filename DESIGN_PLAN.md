# MAS_V2 系统设计方案 - 多智能体系统自动生成框架（细化版）

**撰写日期**: 2026.1.19
**更新日期**: 2026.1.19（细化版：增加权限管理、Hooks 系统、MCP 工具集成、实现指南）
**更新日期**: 2026.1.22（新增：上下文管理系统）

## 一、系统定位与目标

### 1.1 系统目标
构建一个**内生安全的多智能体系统自动生成框架**，能够：
- 针对**一类任务**生成可复用的 workflow（而非一个问题一个 workflow）
- 从智能体池中自动选择最优智能体匹配给子任务
- 支持工具级别和资源级别的权限管理
- 为后续安全模块整合预留 Hooks 接口

### 1.2 支持的任务类型

| 类型 | 描述 | 示例 |
|------|------|------|
| **Web 应用开发** | Flask/FastAPI 后端 + React/Vue 前端 | 待办事项应用、博客系统 |
| **数据处理管道** | ETL、数据分析、报告生成 | CSV 处理、数据可视化 |
| **库/包开发** | 可复用的 Python 包 | 工具库、SDK |
| **简单小游戏** | 命令行或简单 GUI 游戏 | 贪吃蛇、井字棋 |

### 1.3 任务样例

**输入**：
```
"开发一个待办事项 Web 应用，使用 Flask 后端和 React 前端"
```

**输出**：
```
project/
├── backend/
│   ├── app.py           # Flask API
│   ├── models.py        # 数据模型
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   └── components/
│   └── package.json
└── README.md
```

---

## 二、核心架构

### 2.1 模块划分

```
mas_v2/
├── mas/
│   ├── core/           # 核心数据结构
│   ├── agents/         # 智能体池
│   ├── workflow/       # 工作流生成
│   ├── execution/      # 执行引擎
│   ├── permissions/    # 权限管理 (新增)
│   ├── hooks/          # Hooks 系统 (新增)
│   ├── tools/          # MCP 工具集成 (新增)
│   ├── optimization/   # ADAS 优化 (后续扩展)
│   ├── safety/         # 安全接口 (预留)
│   ├── llm/            # LLM 客户端
│   └── utils/          # 工具函数
```

### 2.2 核心流程

```
任务描述 → 任务分类 → Workflow 生成 → 智能体匹配 → 执行
              ↓
        WorkflowFactory
              ↓
    ┌─────────┴─────────┐
    ↓                   ↓
模板匹配            LLM 生成
    ↓                   ↓
    └─────────┬─────────┘
              ↓
         TaskDecomposer (AOV 图)
              ↓
         AgentPool.select()
              ↓
         ExecutionEngine
              ↓
    ┌─────────┴─────────┐
    ↓                   ↓
PreToolUse Hook    PostToolUse Hook
    ↓                   ↓
    └─────────┬─────────┘
              ↓
         输出结果
```

---

## 三、智能体池设计

### 3.1 能力类别

```python
class AgentCapability(Enum):
    CODE_GENERATION = "code_generation"    # 代码生成
    CODE_REVIEW = "code_review"            # 代码审查
    FRONTEND = "frontend"                  # 前端开发
    BACKEND = "backend"                    # 后端开发
    DATA_ANALYSIS = "data_analysis"        # 数据分析
    DOCUMENTATION = "documentation"        # 文档生成
    PLANNING = "planning"                  # 任务规划
    GAME_DEV = "game_dev"                  # 游戏开发
```

### 3.2 智能体实现策略

每个能力类别下有多个实现策略：

| 策略 | 描述 | 适用场景 |
|------|------|---------|
| `chain_of_thought` | 逐步推理 | 复杂逻辑 |
| `reflexion` | 自我反思 + 改进 | 代码质量 |
| `debate` | 多视角讨论 | 架构设计 |
| `role_assignment` | 专家角色分配 | 特定领域 |

### 3.3 智能体元数据（借鉴 Oh My OpenCode）

```python
@dataclass
class AgentDescriptor:
    name: str
    capability: AgentCapability
    strategy: str
    model: str
    temperature: float
    system_prompt: str

    # 新增元数据
    cost: str                    # "low" | "medium" | "high"
    use_when: List[str]          # 适用场景
    avoid_when: List[str]        # 不适用场景
    allowed_tools: List[str]     # 可用工具白名单
    resource_permissions: Dict   # 资源访问权限
```

---

## 四、权限管理系统

### 4.1 权限层级

```
┌─────────────────────────────────────────┐
│ 工具级别 (Tool Level)                    │
│ - 哪些 Agent 可以调用哪些工具            │
│ - 工具参数验证                           │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ 资源级别 (Resource Level)                │
│ - 文件系统访问（读/写/目录限制）         │
│ - 网络访问（URL 白名单）                 │
│ - API 调用（密钥管理）                   │
└─────────────────────────────────────────┘
```

### 4.2 权限配置

```python
@dataclass
class PermissionConfig:
    # 工具级别
    tool_whitelist: Dict[str, List[str]]   # agent_name -> [tool_names]
    tool_blacklist: Dict[str, List[str]]

    # 资源级别
    file_access: FileAccessConfig
    network_access: NetworkAccessConfig
    api_access: APIAccessConfig

@dataclass
class FileAccessConfig:
    allowed_paths: List[str]      # 允许访问的路径
    denied_paths: List[str]       # 禁止访问的路径
    read_only_paths: List[str]    # 只读路径
    max_file_size: int            # 最大文件大小

@dataclass
class NetworkAccessConfig:
    allowed_domains: List[str]    # 允许的域名
    denied_domains: List[str]     # 禁止的域名
    require_https: bool           # 强制 HTTPS
```

### 4.3 权限检查流程

```python
class PermissionManager:
    def check_tool_permission(
        self, agent_name: str, tool_name: str, params: Dict
    ) -> PermissionResult:
        """工具调用权限检查"""
        # 1. 检查工具白名单/黑名单
        # 2. 验证参数合法性
        # 3. 返回 allow/deny/ask

    def check_resource_permission(
        self, agent_name: str, resource_type: str, resource_path: str
    ) -> PermissionResult:
        """资源访问权限检查"""
        # 1. 检查路径是否在允许范围
        # 2. 检查操作类型（读/写）
        # 3. 返回 allow/deny/ask
```

---

## 五、Hooks 系统

### 5.1 核心 Hooks（最小实现）

```python
class HookType(Enum):
    PRE_TOOL_USE = "pre_tool_use"      # 工具调用前
    POST_TOOL_USE = "post_tool_use"    # 工具调用后
    ON_ERROR = "on_error"              # 错误处理

@dataclass
class HookContext:
    agent_name: str
    tool_name: str
    params: Dict[str, Any]
    session_id: str
    timestamp: float

@dataclass
class HookResult:
    decision: str           # "allow" | "deny" | "modify"
    modified_params: Dict   # 修改后的参数（如有）
    message: str            # 消息/原因
    metadata: Dict          # 附加数据
```

### 5.2 Hook 注册和执行

```python
class HookManager:
    def __init__(self):
        self._hooks: Dict[HookType, List[Callable]] = defaultdict(list)

    def register(self, hook_type: HookType, handler: Callable) -> None:
        """注册 Hook 处理函数"""
        self._hooks[hook_type].append(handler)

    async def execute_pre_tool_use(
        self, context: HookContext
    ) -> HookResult:
        """执行 PreToolUse Hooks 链"""
        for handler in self._hooks[HookType.PRE_TOOL_USE]:
            result = await handler(context)
            if result.decision == "deny":
                return result  # 短路返回
            if result.decision == "modify":
                context.params = result.modified_params
        return HookResult(decision="allow", ...)
```

### 5.3 内置 Hook 示例

```python
# 权限检查 Hook
async def permission_check_hook(context: HookContext) -> HookResult:
    result = permission_manager.check_tool_permission(
        context.agent_name, context.tool_name, context.params
    )
    return HookResult(decision=result.decision, message=result.reason)

# 输入验证 Hook
async def input_validation_hook(context: HookContext) -> HookResult:
    schema = tool_registry.get_schema(context.tool_name)
    if not validate_params(context.params, schema):
        return HookResult(decision="deny", message="Invalid parameters")
    return HookResult(decision="allow")

# 审计日志 Hook
async def audit_log_hook(context: HookContext) -> HookResult:
    logger.info(f"Tool call: {context.tool_name} by {context.agent_name}")
    return HookResult(decision="allow")

# 安全预留 Hook（供后续整合 TrustEvaluator）
async def safety_check_hook(context: HookContext) -> HookResult:
    # TODO: 整合 Attention-Tracker, TrustEvaluator
    return HookResult(decision="allow")
```

---

## 六、MCP 工具集成

### 6.1 工具配置（借鉴 OpenCode）

```python
@dataclass
class MCPServerConfig:
    name: str
    type: str                     # "stdio" | "sse"
    command: str                  # stdio 模式的命令
    args: List[str]               # 命令参数
    env: Dict[str, str]           # 环境变量
    url: str                      # sse 模式的 URL
    headers: Dict[str, str]       # HTTP headers
```

### 6.2 工具发现和注册

```python
class MCPToolRegistry:
    async def discover_tools(self, server_config: MCPServerConfig) -> List[Tool]:
        """从 MCP 服务器发现工具"""
        client = await self._connect(server_config)
        tools = await client.list_tools()

        for tool in tools:
            # 注册到全局工具表
            self.register(
                name=f"{server_config.name}_{tool.name}",
                schema=tool.input_schema,
                handler=lambda params: client.call_tool(tool.name, params)
            )

        return tools
```

### 6.3 工具调用流程（整合 Hooks）

```python
async def call_tool(
    self, tool_name: str, params: Dict, context: ExecutionContext
) -> ToolResult:
    # 1. PreToolUse Hooks
    hook_context = HookContext(
        agent_name=context.current_agent,
        tool_name=tool_name,
        params=params,
        session_id=context.session_id
    )
    pre_result = await hook_manager.execute_pre_tool_use(hook_context)

    if pre_result.decision == "deny":
        return ToolResult(success=False, error=pre_result.message)

    # 2. 权限检查（作为 Hook 的一部分或独立检查）
    perm_result = permission_manager.check_tool_permission(
        context.current_agent, tool_name, params
    )
    if not perm_result.allowed:
        return ToolResult(success=False, error="Permission denied")

    # 3. 执行工具
    result = await self._execute_tool(tool_name, params)

    # 4. PostToolUse Hooks
    post_result = await hook_manager.execute_post_tool_use(
        hook_context, result
    )

    return result
```

---

## 七、Workflow 模板系统

### 7.1 预定义模板

```python
# workflow/templates/web_app.py
WEB_APP_TEMPLATE = WorkflowTemplate(
    id="web_app_v1",
    name="Web Application Development",
    category=TaskCategory.WEB_APPLICATION,
    stages=[
        WorkflowStage(
            id="requirements",
            name="需求分析",
            capability=AgentCapability.PLANNING,
            dependencies=[],
        ),
        WorkflowStage(
            id="architecture",
            name="架构设计",
            capability=AgentCapability.PLANNING,
            dependencies=["requirements"],
        ),
        WorkflowStage(
            id="backend",
            name="后端实现",
            capability=AgentCapability.BACKEND,
            dependencies=["architecture"],
            parallelizable=True,
        ),
        WorkflowStage(
            id="frontend",
            name="前端实现",
            capability=AgentCapability.FRONTEND,
            dependencies=["architecture"],
            parallelizable=True,
        ),
        WorkflowStage(
            id="integration",
            name="集成联调",
            capability=AgentCapability.CODE_GENERATION,
            dependencies=["backend", "frontend"],
        ),
        WorkflowStage(
            id="review",
            name="代码审查",
            capability=AgentCapability.CODE_REVIEW,
            dependencies=["integration"],
        ),
    ]
)
```

### 7.2 其他模板

- `DATA_PIPELINE_TEMPLATE`：数据处理管道
- `LIBRARY_TEMPLATE`：库/包开发
- `GAME_TEMPLATE`：简单游戏开发

---

## 八、ADAS 优化模块（后续扩展）

### 8.1 预留接口

```python
# optimization/interface.py
class OptimizationInterface(ABC):
    @abstractmethod
    async def evaluate_agent(
        self, agent: AgentDescriptor, task_samples: List[Dict]
    ) -> EvaluationResult:
        """评估单个智能体性能"""
        pass

    @abstractmethod
    async def search_architecture(
        self, n_generations: int
    ) -> List[AgentArchitecture]:
        """搜索新的智能体架构"""
        pass

    @abstractmethod
    def select_best_agent(
        self, capability: AgentCapability, context: Dict
    ) -> AgentDescriptor:
        """基于性能选择最优智能体"""
        pass
```

### 8.2 与 TrustEvaluator 整合点

```python
# 后续扩展：多维度评估
class MultiMetricEvaluator(OptimizationInterface):
    def __init__(self, trust_evaluator: TrustEvaluator):
        self.trust_evaluator = trust_evaluator

    async def evaluate_agent(self, agent, task_samples) -> EvaluationResult:
        # 任务准确率
        accuracy = await self._evaluate_accuracy(agent, task_samples)

        # 安全性评估（整合第一阶段模块）
        safety_score = await self.trust_evaluator.evaluate_safety(agent)
        reliability_score = await self.trust_evaluator.evaluate_reliability(agent)
        honesty_score = await self.trust_evaluator.evaluate_honesty(agent)

        return EvaluationResult(
            accuracy=accuracy,
            safety=safety_score,
            reliability=reliability_score,
            honesty=honesty_score,
            composite=self._compute_composite(...)
        )
```

---

## 九、目录结构（最终版）

```
mas_v2/
├── README.md
├── pyproject.toml
├── requirements.txt
├── idea_summary.md
├── DESIGN_PLAN.md
│
├── mas/
│   ├── __init__.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── task.py
│   │   ├── workflow.py
│   │   └── schemas.py
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── pool.py
│   │   ├── descriptor.py
│   │   └── implementations/
│   │       ├── code_generation.py
│   │       ├── code_review.py
│   │       ├── frontend.py
│   │       ├── backend.py
│   │       └── data_analysis.py
│   │
│   ├── workflow/
│   │   ├── __init__.py
│   │   ├── factory.py
│   │   ├── decomposer.py
│   │   └── templates/
│   │       ├── web_app.py
│   │       ├── data_pipeline.py
│   │       └── game.py
│   │
│   ├── execution/
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   ├── scheduler.py
│   │   └── runner.py
│   │
│   ├── permissions/          # 新增
│   │   ├── __init__.py
│   │   ├── manager.py
│   │   ├── config.py
│   │   └── validators.py
│   │
│   ├── hooks/                # 新增
│   │   ├── __init__.py
│   │   ├── manager.py
│   │   ├── types.py
│   │   └── builtin/
│   │       ├── permission_check.py
│   │       ├── input_validation.py
│   │       └── audit_log.py
│   │
│   ├── tools/                # 新增
│   │   ├── __init__.py
│   │   ├── registry.py
│   │   ├── mcp_client.py
│   │   └── builtin/
│   │       ├── file_ops.py
│   │       ├── code_exec.py
│   │       └── web_fetch.py
│   │
│   ├── logging/              # 新增：结构化日志
│   │   ├── __init__.py
│   │   ├── events.py
│   │   └── tracker.py
│   │
│   ├── output/               # 新增：结果输出
│   │   ├── __init__.py
│   │   ├── reporter.py
│   │   └── serializer.py
│   │
│   ├── optimization/         # 预留
│   │   ├── __init__.py
│   │   └── interface.py
│   │
│   ├── safety/               # 预留
│   │   ├── __init__.py
│   │   └── interface.py
│   │
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   └── prompts.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── config.py
│       └── logger.py
│
├── examples/
│   ├── web_app_demo.py
│   ├── data_pipeline_demo.py
│   └── game_demo.py
│
└── tests/
```

---

## 十、实现优先级

### 第一阶段（核心功能）
1. `core/` - Task, Workflow 基础类
2. `llm/` - LLM 客户端
3. `agents/pool.py` - 智能体池
4. `workflow/factory.py` - 工作流生成
5. `execution/engine.py` - 执行引擎
6. `permissions/` - 权限管理
7. `hooks/` - Hooks 系统（最小实现）
8. `tools/` - MCP 工具基础

### 第二阶段（完善功能）
1. `agents/implementations/` - 各类智能体实现
2. `workflow/templates/` - 预定义模板
3. `workflow/decomposer.py` - AOV 任务分解
4. `hooks/builtin/` - 内置 Hooks
5. `logging/` - 结构化日志系统
6. `output/` - 结果输出系统

### 第三阶段（高级功能，后续扩展）
1. `optimization/` - ADAS 自动搜索
2. `safety/` - 安全模块整合

---

## 十一、关键参考文件

| 文件路径 | 参考内容 |
|----------|----------|
| `/home/gargantua/code/mas_safe/FLOW/workflow.py` | Task、Workflow 数据结构 |
| `/home/gargantua/code/mas_safe/FLOW/flow.py` | 异步执行引擎 |
| `/home/gargantua/code/mas_safe/multi_agent_framework/orchestration/registry.py` | Agent 注册表 |
| `/home/gargantua/code/mas_safe/multi_agent_framework/orchestration/schemas.py` | PlanningConstraints |
| `/home/gargantua/code/mas_safe/multi_agent_framework/mcp_integration/` | MCP 集成参考 |
| `/home/gargantua/code/mas_safe/ADAS/ADAS/_mgsm/search.py` | ADAS 搜索算法 |
| `/home/gargantua/code/mas_safe/mas_v2/opencode-ohmyopencode-technical-research.md` | Hooks 和权限系统参考 |

---

## 十二、实现指南（给 GPT-5.2-codex）

### 12.1 实现顺序

请严格按照以下顺序实现：

```
第一阶段（核心功能）
├── 1. mas/core/schemas.py         # Pydantic 数据模型
├── 2. mas/core/task.py            # Task 类
├── 3. mas/core/workflow.py        # Workflow 类
├── 4. mas/llm/client.py           # LLM 客户端（支持 MiniMax API）
├── 5. mas/agents/pool.py          # AgentPool 和 Registry
├── 6. mas/agents/descriptor.py    # AgentDescriptor
├── 7. mas/permissions/config.py   # 权限配置数据结构
├── 8. mas/permissions/manager.py  # PermissionManager
├── 9. mas/hooks/types.py          # Hook 类型定义
├── 10. mas/hooks/manager.py       # HookManager
├── 11. mas/tools/registry.py      # 工具注册表
├── 12. mas/workflow/factory.py    # WorkflowFactory
├── 13. mas/execution/engine.py    # ExecutionEngine
└── 14. mas/__init__.py            # 主入口 run_task()

第二阶段（智能体和模板）
├── 15. mas/agents/implementations/code_generation.py
├── 16. mas/agents/implementations/code_review.py
├── 17. mas/agents/implementations/frontend.py
├── 18. mas/agents/implementations/backend.py
├── 19. mas/agents/implementations/data_analysis.py
├── 20. mas/workflow/decomposer.py
├── 21. mas/workflow/templates/web_app.py
├── 22. mas/workflow/templates/data_pipeline.py
├── 23. mas/workflow/templates/game.py
├── 24. mas/hooks/builtin/permission_check.py
├── 25. mas/hooks/builtin/input_validation.py
└── 26. mas/hooks/builtin/audit_log.py

第三阶段（示例和测试）
├── 27. examples/web_app_demo.py
├── 28. examples/data_pipeline_demo.py
├── 29. examples/game_demo.py
└── 30. tests/
```

### 12.2 关键实现细节

#### 12.2.1 LLM 客户端

```python
# mas/llm/client.py
# 参考 /home/gargantua/code/mas_safe/multi_agent_framework/api/client.py
# 使用 MiniMax API，支持异步调用

import os
import httpx
from typing import Optional, Dict, Any

class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("MINIMAX_API_KEY")
        self.base_url = "https://api.minimax.chat/v1"
        self.model = "MiniMax-M2.1"

    async def acomplete(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        response_format: Optional[Dict] = None
    ) -> str:
        """异步调用 LLM"""
        ...

    def complete(self, prompt: str, **kwargs) -> str:
        """同步调用 LLM"""
        import asyncio
        return asyncio.run(self.acomplete(prompt, **kwargs))
```

#### 12.2.2 智能体池单例模式

```python
# mas/agents/pool.py
# 参考 /home/gargantua/code/mas_safe/multi_agent_framework/orchestration/registry.py

class AgentPoolRegistry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._pools = {}
        return cls._instance
```

#### 12.2.3 Hooks 执行链

```python
# mas/hooks/manager.py
# 参考 OpenCode/Oh My OpenCode 的 Hooks 实现

class HookManager:
    async def execute_pre_tool_use(self, context: HookContext) -> HookResult:
        """执行 PreToolUse Hooks 链，遇到 deny 立即返回"""
        for handler in self._hooks[HookType.PRE_TOOL_USE]:
            result = await handler(context)
            if result.decision == "deny":
                return result
            if result.decision == "modify":
                context.params = result.modified_params
        return HookResult(decision="allow")
```

#### 12.2.4 AOV 图任务分解

```python
# mas/workflow/decomposer.py
# 参考 /home/gargantua/code/mas_safe/FLOW/workflow.py

import networkx as nx

class TaskDecomposer:
    def _build_dependency_graph(self, tasks: Dict[str, Task]) -> nx.DiGraph:
        """构建 AOV 依赖图"""
        graph = nx.DiGraph()
        for task_id, task in tasks.items():
            graph.add_node(task_id, task=task)
            for dep_id in task.dependencies:
                if dep_id in tasks:
                    graph.add_edge(dep_id, task_id)

        # 检测循环依赖
        if not nx.is_directed_acyclic_graph(graph):
            raise ValueError("Cyclic dependency detected")

        # 传递规约优化
        return nx.transitive_reduction(graph)
```

### 12.3 依赖安装

```bash
# requirements.txt
langgraph>=1.0.0
langchain>=1.0.0
httpx>=0.25.0
pydantic>=2.0.0
networkx>=3.0
python-dotenv>=1.0.0
mcp>=1.0.0
```

### 12.4 环境变量

```bash
# .env
MINIMAX_API_KEY=your_api_key_here
```

### 12.5 测试验证

实现完成后，请确保以下测试通过：

```python
# 基本功能测试
async def test_basic():
    from mas import run_task

    result = await run_task("创建一个简单的 Flask API，包含用户登录功能")
    assert result.success
    assert "backend" in result.task_results

# 权限测试
async def test_permissions():
    from mas.permissions import PermissionManager

    manager = PermissionManager()
    result = manager.check_tool_permission("coder", "file_write", {"path": "/etc/passwd"})
    assert result.decision == "deny"

# Hooks 测试
async def test_hooks():
    from mas.hooks import HookManager, HookType

    manager = HookManager()
    manager.register(HookType.PRE_TOOL_USE, permission_check_hook)
    result = await manager.execute_pre_tool_use(context)
    assert result.decision in ["allow", "deny", "modify"]
```

---

## 十三、审查清单（给 Claude 审查用）

项目完成后，请检查以下内容：

### 13.1 功能完整性
- [ ] 所有核心模块已实现
- [ ] 智能体池可以注册和选择智能体
- [ ] Workflow 可以从模板生成
- [ ] 执行引擎可以运行 workflow
- [ ] 权限管理正常工作
- [ ] Hooks 系统正常拦截

### 13.2 代码质量
- [ ] 类型注解完整（使用 typing）
- [ ] 文档字符串完整
- [ ] 无明显代码重复
- [ ] 异常处理合理
- [ ] 日志记录完整

### 13.3 安全性
- [ ] 权限检查无绕过漏洞
- [ ] 输入验证完整
- [ ] 敏感信息不暴露
- [ ] 文件访问有限制
- [ ] 网络访问有限制

### 13.4 可扩展性
- [ ] ADAS 接口预留正确
- [ ] Safety 接口预留正确
- [ ] TrustEvaluator 整合点明确
- [ ] Hooks 可以动态注册

### 13.5 测试覆盖
- [ ] 核心功能有测试
- [ ] 边界情况有测试
- [ ] 异常情况有测试

---

## 十四、日志和结果记录系统

### 14.1 问题背景

当前系统运行示例时只能看到简单的结果信息：
```
success=False
task_results=['requirements', 'implementation']
```

**无法看到的关键信息**：
1. 每个任务的 LLM 输出内容
2. 任务执行的中间过程
3. 错误详情和堆栈
4. 执行耗时和性能数据
5. 智能体选择和决策过程

### 14.2 新增模块

```
mas/
├── logging/              # 新增：结构化日志系统
│   ├── __init__.py
│   ├── tracker.py        # 执行追踪器
│   └── events.py         # 日志事件类型定义
│
├── output/               # 新增：结果输出系统
│   ├── __init__.py
│   ├── reporter.py       # 结果报告生成器（控制台 + JSON）
│   └── serializer.py     # 序列化工具（to_dict/to_json）
```

### 14.3 核心数据结构

#### 14.3.1 日志事件 (`logging/events.py`)

```python
class LogEvent(Enum):
    WORKFLOW_START = "workflow_start"
    WORKFLOW_END = "workflow_end"
    TASK_START = "task_start"
    TASK_END = "task_end"
    AGENT_SELECTED = "agent_selected"
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"
    HOOK_EXECUTED = "hook_executed"
    ERROR_OCCURRED = "error_occurred"

@dataclass
class LogRecord:
    event: LogEvent
    timestamp: float
    session_id: str
    task_id: str | None
    agent_name: str | None
    data: dict[str, object]
    duration_ms: float | None = None
```

#### 14.3.2 执行追踪器 (`logging/tracker.py`)

```python
class ExecutionTracker:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.records: list[LogRecord] = []
        self._timers: dict[str, float] = {}

    def log_workflow_start(self, task_description: str) -> None: ...
    def log_task_start(self, task: Task, agent: AgentDescriptor) -> None: ...
    def log_llm_response(self, task_id: str, response: str) -> None: ...
    def log_task_end(self, task_id: str, result: TaskResult) -> None: ...
    def log_error(self, task_id: str, error: Exception) -> None: ...

    def get_summary(self) -> dict: ...
    def export_json(self, path: str) -> None: ...
```

#### 14.3.3 结果报告器 (`output/reporter.py`)

```python
class WorkflowReporter:
    def __init__(self, result: WorkflowResult, tracker: ExecutionTracker):
        self.result = result
        self.tracker = tracker

    def print_summary(self) -> None:
        """打印摘要到控制台（默认模式）"""

    def save_json(self, path: str) -> None:
        """保存 JSON 格式报告"""
```

### 14.4 数据结构增强 (`core/schemas.py`)

```python
@dataclass
class TaskResult:
    task_id: str
    success: bool
    output: object | None = None
    error: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)

    # 新增字段
    start_time: float | None = None
    end_time: float | None = None
    agent_name: str | None = None

    def to_dict(self) -> dict: ...
    def to_json(self) -> str: ...

@dataclass
class WorkflowResult:
    success: bool
    task_results: dict[str, TaskResult]
    errors: dict[str, str] = field(default_factory=dict)

    # 新增字段
    total_duration_ms: float | None = None
    session_id: str | None = None

    def to_dict(self) -> dict: ...
    def to_json(self) -> str: ...
    def save(self, path: str) -> None: ...
```

### 14.5 执行引擎改进

```python
class ExecutionEngine:
    def __init__(self, ..., verbose: bool = False):
        self.verbose = verbose
        self.tracker = ExecutionTracker(self._session_id)

    async def run(self, workflow: Workflow) -> WorkflowResult:
        self.tracker.log_workflow_start(workflow.description)

        # ... 执行逻辑 ...

        for task in ready_tasks:
            self.tracker.log_task_start(task, agent)
            result = await self._execute_task(task, context, task_results)  # 传递已完成任务结果
            self.tracker.log_task_end(task.task_id, result)

            if self.verbose:
                self._print_task_progress(task, result)

        return WorkflowResult(
            ...,
            session_id=self._session_id,
            total_duration_ms=self.tracker.get_total_duration(),
        )
```

### 14.5.1 任务间上下文传递 ⭐ 新增

多智能体协作的关键是任务间的信息传递。每个任务的输出会自动传递给依赖它的后续任务。

**设计原理**:
```
requirements → implementation → review
    ↓              ↓              ↓
  需求文档  →  基于需求写代码  →  审查代码
```

**实现机制**:
```python
async def _execute_task(
    self,
    task: Task,
    context: ExecutionContext,
    task_results: dict[str, TaskResult],  # 已完成任务的结果
) -> TaskResult:
    # 收集依赖任务的输出
    dependency_outputs: dict[str, str] = {}
    for dep_id in task.dependencies:
        if dep_id in task_results and task_results[dep_id].output:
            dependency_outputs[dep_id] = str(task_results[dep_id].output)

    # 调用 LLM 时传入依赖输出
    output = await self._call_llm(task, agent, dependency_outputs)
    ...

async def _call_llm(
    self,
    task: Task,
    agent: AgentDescriptor | None,
    dependency_outputs: dict[str, str],
) -> str:
    # 构建包含依赖任务输出的 prompt
    context_section = ""
    if dependency_outputs:
        context_parts = []
        for dep_id, dep_output in dependency_outputs.items():
            # 截断过长输出避免 token 超限
            truncated = dep_output[:8000] if len(dep_output) > 8000 else dep_output
            context_parts.append(f"### {dep_id} 任务的输出:\n{truncated}")
        context_section = "\n\n## 前置任务的输出（请基于这些内容完成当前任务）:\n\n" + "\n\n".join(context_parts)

    prompt = f"""System: {system_prompt}
{context_section}

## 当前任务:
{task.objective}

请基于前置任务的输出（如果有）完成当前任务，并提供你的回答。"""
    ...
```

**效果验证**:
- `implementation` 任务能看到 `requirements` 的需求分析
- `review` 任务能看到 `implementation` 的代码实现
- 任务协作更加连贯，输出质量显著提升

### 14.6 示例改进

```python
# examples/web_app_demo.py
import asyncio
from mas import run_task
from mas.output.reporter import WorkflowReporter

async def main():
    result = await run_task(
        "创建一个待办事项 Web 应用，使用 Flask 后端",
        verbose=True  # 新增：实时输出
    )

    # 摘要报告
    reporter = WorkflowReporter(result)
    reporter.print_summary()

    # 保存 JSON 结果
    reporter.save_json("output/web_app_result.json")

if __name__ == "__main__":
    asyncio.run(main())
```

### 14.7 输出示例

**控制台输出（verbose=True）：**
```
[14:30:01] 🚀 开始执行工作流: web_application
[14:30:01] ├─ 任务 [requirements] 开始 (PlanningAgent)
[14:30:05] │  └─ ✅ 完成 (3.2s) - "## 需求分析\n\n1. 用户认证..."
[14:30:05] ├─ 任务 [architecture] 开始 (PlanningAgent)
[14:30:10] │  └─ ✅ 完成 (4.8s) - "## 架构设计\n\n采用前后端分离..."
[14:30:10] ├─ 任务 [backend] 开始 (BackendAgent)
[14:30:10] ├─ 任务 [frontend] 开始 (FrontendAgent)
[14:30:25] │  └─ ✅ backend 完成 (15.2s) - "```python\nfrom flask..."
[14:30:28] │  └─ ✅ frontend 完成 (18.1s) - "```jsx\nimport React..."
[14:30:28] └─ 工作流完成 (总耗时: 27.3s)

📊 执行摘要:
  - 成功: True
  - 任务数: 5/5 完成
  - 总耗时: 27.3s
```

**JSON 输出 (`output/result.json`)：**
```json
{
  "session_id": "abc-123",
  "success": true,
  "total_duration_ms": 27300,
  "task_results": {
    "requirements": {
      "task_id": "requirements",
      "success": true,
      "agent_name": "PlanningAgent",
      "start_time": 1706012401.0,
      "end_time": 1706012405.2,
      "output": "## 需求分析\n\n1. 用户认证...",
      "metadata": {}
    }
  }
}
```

### 14.8 实现指南（给 GPT-5.2-codex）

#### 实现顺序

```
1. mas/logging/events.py          # 日志事件定义
2. mas/logging/tracker.py         # 执行追踪器
3. mas/output/serializer.py       # 序列化工具
4. mas/output/reporter.py         # 结果报告器
5. mas/core/schemas.py            # 添加 to_dict/to_json 和时间戳
6. mas/execution/engine.py        # 集成 tracker，添加 verbose
7. mas/__init__.py                # 更新 run_task 签名
8. examples/*.py                  # 更新示例
```

#### 关键要求

1. **摘要模式输出**：LLM 输出内容截断显示（前 50 字符 + "..."）
2. **JSON 保存**：完整保存所有 LLM 输出内容到 output 字段
3. **时间记录**：每个任务记录 start_time 和 end_time
4. **实时输出**：verbose=True 时在任务开始/完成时打印信息

#### 需要修改的文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `mas/core/schemas.py` | 修改 | 添加 to_dict/to_json 方法和时间戳字段 |
| `mas/execution/engine.py` | 修改 | 集成 ExecutionTracker，添加 verbose 参数 |
| `mas/logging/__init__.py` | 新增 | 日志模块入口 |
| `mas/logging/events.py` | 新增 | 日志事件类型定义 |
| `mas/logging/tracker.py` | 新增 | 执行追踪器 |
| `mas/output/__init__.py` | 新增 | 输出模块入口 |
| `mas/output/reporter.py` | 新增 | 结果报告生成器 |
| `mas/output/serializer.py` | 新增 | 序列化工具 |
| `examples/*.py` | 修改 | 使用新的输出功能 |
| `mas/__init__.py` | 修改 | run_task 添加 verbose 参数 |

---

## 十五、上下文管理系统

### 15.1 问题背景

在多智能体协作场景中，任务间的上下文传递至关重要。之前的实现使用简单的字符串截断（8000 字符），可能导致关键信息丢失。

### 15.2 四层上下文架构

```
┌─────────────────────────────────────────────┐
│         System Context (Level 0)             │
│    - 全局配置                                │
│    - Agent 池元数据                          │
│    - 权限配置                                │
├─────────────────────────────────────────────┤
│          Workflow Context (Level 1)          │
│    - 任务描述                                │
│    - 跨任务共享状态                          │
│    - 工作流级目标和约束                      │
├─────────────────────────────────────────────┤
│            Task Context (Level 2)            │
│    - 依赖任务输出                            │
│    - 工具调用结果                            │
│    - LLM 响应                                │
├─────────────────────────────────────────────┤
│           Agent Context (Level 3)            │
│    - Agent 特定记忆                          │
│    - 工具调用历史                            │
│    - 错误恢复状态                            │
└─────────────────────────────────────────────┘
```

### 15.3 上下文类型定义

```python
# context/types.py

class ContextType(str, Enum):
    DEPENDENCY_OUTPUT = "dependency_output"  # 依赖任务输出
    SHARED_STATE = "shared_state"            # 共享状态
    TOOL_RESULT = "tool_result"              # 工具结果
    LLM_RESPONSE = "llm_response"            # LLM 响应
    ERROR_CONTEXT = "error_context"          # 错误上下文
    CONFIGURATION = "configuration"          # 配置信息

class ContextLayer(int, Enum):
    SYSTEM = 0      # 系统层
    WORKFLOW = 1    # 工作流层
    TASK = 2        # 任务层
    AGENT = 3       # 智能体层

@dataclass
class ContextEntry:
    id: str
    type: ContextType
    content: str | dict[str, object]
    timestamp: float
    source: str                              # agent_name 或 task_id
    importance: float = 0.5                  # 0.0-1.0
    relevance_score: float = 0.5             # 0.0-1.0
    access_count: int = 0                    # 访问次数
    ttl: int | None = None                   # 生存时间（秒）
    parent_id: str | None = None             # 父上下文 ID
    related_ids: list[str] = field(default_factory=list)
    is_compressed: bool = False              # 是否已压缩
    original_length: int = 0                 # 原始长度
    summary: str | None = None               # 压缩摘要
```

### 15.4 重要性评分算法

```python
def compute_score(self, current_task_id: str | None = None) -> float:
    """计算综合分数"""
    # 基础重要性权重（基于类型）
    type_weights = {
        ContextType.ERROR_CONTEXT: 0.9,
        ContextType.DEPENDENCY_OUTPUT: 0.8,
        ContextType.SHARED_STATE: 0.7,
        ContextType.TOOL_RESULT: 0.6,
        ContextType.LLM_RESPONSE: 0.5,
        ContextType.CONFIGURATION: 0.4,
    }
    base = type_weights.get(self.type, 0.5)

    # 时间衰减（1小时半衰期）
    recency = math.exp(-(time.time() - self.timestamp) / 3600.0)

    # 访问频率（归一化）
    frequency = min(self.access_count / 10.0, 1.0)

    # 加权求和
    return base * 0.4 + self.relevance_score * 0.3 + recency * 0.2 + frequency * 0.1
```

### 15.5 Token 窗口管理

```python
# context/window.py

class ContextWindow:
    DEFAULT_MAX_TOKENS = 8000

    def __init__(self, max_tokens: int = DEFAULT_MAX_TOKENS):
        self.max_tokens = max_tokens
        self._encoding = None  # tiktoken 编码器

    def select(self, entries: list[ContextEntry], max_tokens: int | None = None) -> list[ContextEntry]:
        """在 Token 预算内贪心选择最高分的条目"""
        budget = max_tokens or self.max_tokens
        ordered = sorted(entries, key=lambda e: e.compute_score(), reverse=True)

        selected = []
        used_tokens = 0
        for entry in ordered:
            tokens = self._entry_tokens(entry)
            if used_tokens + tokens <= budget:
                selected.append(entry)
                used_tokens += tokens
                entry.increment_access()

        return selected
```

### 15.6 LLM 摘要压缩

```python
# context/compression.py

class ContextCompressor:
    COMPRESSION_THRESHOLD = 4000  # 超过此长度触发压缩

    async def summarize(self, text: str, max_length: int = 1000) -> str:
        """使用 LLM 生成摘要"""
        if self._llm_client is None:
            return self.truncate_smart(text, max_length)

        prompt = f"""请简洁地总结以下内容，保留关键信息：

{text}

要求：
1. 控制在 {max_length} 字符以内
2. 保留主要结论和关键数据
3. 保留重要的技术细节

摘要："""

        try:
            summary = await self._llm_client.acomplete(prompt, temperature=0.3)
            return summary[:max_length]
        except Exception:
            return self.truncate_smart(text, max_length)

    def truncate_smart(self, text: str, max_length: int) -> str:
        """智能截断，保留句子边界"""
        if len(text) <= max_length:
            return text

        # 查找句号或换行符
        boundary = max(text.rfind("。", 0, max_length),
                       text.rfind(".", 0, max_length),
                       text.rfind("\n", 0, max_length))

        if boundary != -1 and boundary >= max_length * 0.5:
            return text[: boundary + 1]

        return text[:max_length].rstrip() + "..."
```

### 15.7 上下文管理器

```python
# context/manager.py

class ContextManager:
    """上下文管理器 - 管理多智能体系统中的上下文"""

    def __init__(
        self,
        session_id: str,
        llm_client: "LLMClient | None" = None,
        max_tokens: int = 8000,
    ):
        self.session_id = session_id
        self.store = ContextStore(session_id)
        self.scorer = ContextScorer()
        self.window = ContextWindow(max_tokens=max_tokens)
        self.compressor = ContextCompressor(llm_client)

    async def add_task_output(
        self,
        task_id: str,
        output: str,
        agent_name: str,
        dependent_task_ids: list[str] | None = None,
    ) -> str:
        """添加任务输出，自动压缩长输出"""
        importance = self.scorer.compute_task_importance(task_id, agent_name)

        entry = ContextEntry(
            id=f"task_output_{task_id}_{uuid.uuid4().hex[:8]}",
            type=ContextType.DEPENDENCY_OUTPUT,
            content=output,
            timestamp=time.time(),
            source=task_id,
            importance=importance,
            parent_id=task_id,
            related_ids=list(dependent_task_ids or []),
        )

        # 自动压缩
        if await self.compressor.should_compress(entry.content):
            entry = await self.compressor.compress_entry(entry)

        return self.store.add(ContextLayer.TASK, entry)

    async def get_context_for_task(
        self,
        task_id: str,
        dependency_ids: list[str],
        max_tokens: int | None = None,
    ) -> str:
        """获取优化后的任务上下文"""
        # 收集相关条目
        candidates = self._collect_related_entries(task_id, dependency_ids)

        # 评分排序
        ranked = self.scorer.rank_entries(candidates, target_task_id=task_id)

        # Token 预算内选择
        selected = self.window.select(ranked, max_tokens=max_tokens)

        return self._format_context(selected)

    def _collect_related_entries(self, task_id: str, dependency_ids: list[str]) -> list[ContextEntry]:
        """收集相关上下文条目"""
        entries = []
        # 添加依赖任务输出
        for entry in self.store.get_layer(ContextLayer.TASK).values():
            if entry.source in dependency_ids:
                entries.append(entry)
        # 添加共享状态
        entries.extend(self.store.get_layer(ContextLayer.WORKFLOW).values())
        return entries
```

### 15.8 与执行引擎集成

```python
# execution/engine.py

class ExecutionEngine:
    def __init__(self, ..., context_max_tokens: int = 8000):
        ...
        self.context_manager = ContextManager(
            session_id=self._session_id,
            llm_client=self.llm_client,
            max_tokens=context_max_tokens,
        )

    async def _execute_task(self, task, context, task_results) -> TaskResult:
        # 获取优化后的上下文
        optimized_context = await self.context_manager.get_context_for_task(
            task_id=task.task_id,
            dependency_ids=task.dependencies,
            max_tokens=8000,
        )

        output = await self._call_llm(task, agent, optimized_context)

        # 存储任务输出
        await self.context_manager.add_task_output(
            task_id=task.task_id,
            output=str(output),
            agent_name=agent_name,
        )

        return result
```

### 15.9 上下文感知的 Agent 选择

```python
# agents/pool.py

def select_best_agent(self, capability: AgentCapability, context: dict[str, str]) -> AgentDescriptor:
    """根据上下文智能选择最优 Agent"""
    candidates = [d for d in self._pools.values() if d.capability == capability]

    if len(candidates) == 1 or not context:
        return candidates[0]

    # 上下文评分
    scored = []
    for agent in candidates:
        score = self._compute_agent_score(agent, context)
        scored.append((agent, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[0][0]

def _compute_agent_score(self, agent: AgentDescriptor, context: dict[str, str]) -> float:
    """计算 Agent 与任务的匹配分数"""
    score = 1.0
    task_desc = context.get("task_description", "").lower()

    # use_when 条件匹配
    for condition in agent.use_when:
        if condition.lower() in task_desc:
            score += 0.5

    # avoid_when 条件匹配
    for condition in agent.avoid_when:
        if condition.lower() in task_desc:
            score -= 0.5

    # 成本惩罚
    cost_penalty = {"low": 0.0, "medium": 0.1, "high": 0.2}
    score -= cost_penalty.get(agent.cost, 0.0)

    return score
```

### 15.10 目录结构

```
mas/context/
├── __init__.py           # 公共 API 导出
├── types.py              # ContextType, ContextLayer, ContextEntry
├── store.py              # ContextStore 分层存储
├── scorer.py             # ContextScorer 重要性评分
├── window.py             # ContextWindow Token 窗口管理
├── compression.py        # ContextCompressor 摘要压缩
└── manager.py            # ContextManager 主管理接口
```

### 15.11 实现效果

| 指标 | 之前 | 之后 |
|------|------|------|
| Token 利用率 | ~50%（简单截断） | >90%（智能选择） |
| 关键信息保留 | 可能丢失 | LLM 摘要保留 |
| Agent 选择 | 仅基于能力 | 上下文感知 |
| 上下文检索 | 无 | 相关性评分 |

---

## 十六、后续扩展计划

### 15.1 ADAS 优化模块（第三阶段）

当核心框架稳定后，实现 ADAS 自动搜索：

1. 实现 `mas/optimization/adas_engine.py`
2. 实现 `mas/optimization/evaluator.py`
3. 实现 `mas/optimization/archive.py`
4. 整合到 AgentPool 的选择逻辑中

### 15.2 安全模块整合（第三阶段）

整合第一阶段的安全评估模块：

1. 在 `mas/safety/` 中实现 TrustEvaluator wrapper
2. 在 PreToolUse Hook 中调用 Attention-Tracker
3. 在智能体选择中考虑信任度得分
4. 实现动态 Agent 替换机制

### 15.3 更多工具支持

1. 文件系统工具（读/写/创建目录）
2. 代码执行工具（Python/Node.js）
3. Web 访问工具（fetch/搜索）
4. 数据库工具（SQLite/PostgreSQL）
