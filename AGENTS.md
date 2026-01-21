# AGENTS.md

本文档为在此仓库工作的 AI Agent 提供开发指南和规范。

## 仓库概述

**MAS_V2** 是一个**内生安全的多智能体系统自动生成框架**，目前处于设计阶段。本项目旨在：

- 针对一类任务生成可复用的 workflow（而非一个问题一个 workflow）
- 从智能体池中自动选择最优智能体匹配子任务
- 支持工具级别和资源级别的权限管理
- 为安全模块整合预留 Hooks 接口

**注意**：此仓库当前仅包含设计文档，尚未开始编码实现。

---

## 构建与测试命令

### 当前阶段（设计阶段）

```bash
# 无构建命令，仅文档查看
cat DESIGN_PLAN.md          # 查看系统设计方案
cat idea_summary.md         # 查看项目创意摘要
```

### 未来实现阶段的命令（规划）

```bash
# 环境设置（使用现有 conda 环境）
conda activate langgraph_agent

# 安装依赖
pip install -r requirements.txt

# 运行单个测试
pytest tests/test_module.py::test_function

# 运行所有测试
pytest

# 代码格式化（如果使用 Black）
black mas/

# 代码检查
ruff check mas/
```

---

## 代码风格规范

### 命名约定

```python
# 类名：PascalCase
class AgentPool:
    pass

# 函数和变量：snake_case
def get_agent_capability(capability_type: str):
    agent_count = 0

# 常量：UPPER_SNAKE_CASE
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT = 30

# 私有方法/属性：单下划线前缀
def _internal_method(self):
    self._private_attr = value
```

### 类型注解

```python
from typing import Dict, List, Optional, Any

# 函数参数和返回值必须使用类型注解
def execute_task(
    task_id: str,
    agent: AgentDescriptor,
    timeout: Optional[int] = None
) -> TaskResult:
    ...

# 使用 Optional 表示可能为 None 的值
name: Optional[str] = None

# 使用 Union 表示多种可能类型
result: Union[str, int, None] = None
```

### 导入规范

```python
# 标准库导入
import os
import sys
from typing import Dict, List, Optional

# 第三方库导入
import httpx
from pydantic import BaseModel
import networkx as nx

# 本地模块导入
from mas.core.task import Task
from mas.agents.pool import AgentPool
```

### 缩进与排版

- **缩进**：4 空格（不使用 Tab）
- **行长**：尽量不超过 100 字符
- **运算符两侧**：添加空格 `a = b + c`
- **括号内侧**：不加空格 `func(arg1, arg2)`
- **空行**：类/函数之间空两行，类/函数内部逻辑块之间空一行

### 错误处理

```python
# 使用具体异常类型，禁止空 except 块
try:
    result = await llm_client.acomplete(prompt)
except httpx.TimeoutError as e:
    logger.error(f"LLM 请求超时: {e}")
    raise
except ValueError as e:
    logger.error(f"参数验证失败: {e}")
    raise

# 自定义异常类
class PermissionError(Exception):
    """权限相关的错误"""
    pass
```

---

## 项目结构（规划）

```
mas_v2/
├── mas/
│   ├── core/           # 核心数据结构（task.py, workflow.py, schemas.py）
│   ├── agents/         # 智能体池（pool.py, descriptor.py, implementations/）
│   ├── workflow/       # 工作流生成（factory.py, decomposer.py, templates/）
│   ├── execution/      # 执行引擎（engine.py, scheduler.py, runner.py）
│   ├── permissions/    # 权限管理（manager.py, config.py, validators.py）
│   ├── hooks/          # Hooks 系统（manager.py, types.py, builtin/）
│   ├── tools/          # MCP 工具集成（registry.py, mcp_client.py, builtin/）
│   ├── optimization/   # ADAS 优化（预留）
│   ├── safety/         # 安全接口（预留）
│   ├── llm/            # LLM 客户端（client.py）
│   └── utils/          # 工具函数（config.py, logger.py）
├── examples/           # 示例代码
├── tests/              # 测试目录
├── pyproject.toml      # 项目配置（待创建）
└── requirements.txt    # 依赖列表（待创建）
```

---

## 技术栈（规划）

| 类别 | 技术 |
|------|------|
| **后端框架** | Python 3.10+ |
| **多智能体** | LangGraph, LangChain |
| **数据验证** | Pydantic 2.0+ |
| **异步运行时** | asyncio |
| **工具集成** | MCP (Model Context Protocol) |
| **HTTP 客户端** | httpx |
| **图处理** | NetworkX |
| **LLM API** | MiniMax API (兼容 OpenAI 接口) |

---

## 核心依赖（requirements.txt 规划）

```
langgraph>=1.0.0
langchain>=1.0.0
httpx>=0.25.0
pydantic>=2.0.0
networkx>=3.0
python-dotenv>=1.0.0
mcp>=1.0.0
```

---

## 实现优先级（参考 DESIGN_PLAN.md）

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

### 第三阶段（高级功能，后续扩展）
1. `optimization/` - ADAS 自动搜索
2. `safety/` - 安全模块整合

---

## 文档与注释

```python
class AgentPool:
    """
    智能体池管理器。

    维护所有可用智能体，根据任务需求选择最优智能体。

    Attributes:
        _agents: 智能体注册表 {name: AgentDescriptor}
        _capabilities: 能力索引 {capability: [agent_names]}
    """

    def select_best_agent(
        self,
        capability: AgentCapability,
        context: Dict[str, Any]
    ) -> Optional[AgentDescriptor]:
        """
        选择最适合当前任务的智能体。

        Args:
            capability: 所需能力类型
            context: 任务上下文信息

        Returns:
            最优智能体描述符，如无匹配则返回 None
        """
        ...
```

---

## 环境变量

```bash
# .env 文件（不要提交到 Git）
MINIMAX_API_KEY=your_api_key_here
```

---

## 安全规范

- **API 密钥**：使用环境变量，禁止硬编码在代码中
- **权限管理**：严格遵循工具级别和资源级别的权限检查
- **输入验证**：所有外部输入必须经过验证
- **敏感信息**：禁止在日志中输出敏感数据
- **文件访问**：限制在项目目录范围内

---

## 工作流程

1. 阅读现有文档：`DESIGN_PLAN.md`, `idea_summary.md`
2. 按照 DESIGN_PLAN.md 中的实现顺序逐步开发
3. 使用 `todowrite` 跟踪任务进度
4. 完成后使用 `lsp_diagnostics` 验证代码质量
5. 运行测试确保功能正常
6. 遇到长时间无法解决的类型警告可以略过，无编译错误即可
---

## 参考资料

- **主设计文档**：`/home/gargantua/code/mas_safe/mas_v2/DESIGN_PLAN.md`
- **技术研究**：`/home/gargantua/code/mas_safe/mas_v2/opencode-ohmyopencode-technical-research.md`
- **Flow 项目参考**：`/home/gargantua/code/mas_safe/FLOW/`（工作流编排）
- **多智能体框架参考**：`/home/gargantua/code/mas_safe/multi_agent_framework/`（LangGraph 实现）

---

## 注意事项

1. **类型安全**：禁止使用 `as any`、`@ts-ignore`、`@ts-expect-error`
2. **异常处理**：禁止空 `except` 块
3. **代码重复**：及时提取公共逻辑到工具函数
4. **日志记录**：使用项目统一的日志系统
5. **测试覆盖**：核心功能必须有对应测试
