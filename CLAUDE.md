# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MAS_V2 is an **intrinsically secure multi-agent system auto-generation framework** that:
- Generates reusable workflows for task categories (not one workflow per problem)
- Auto-selects optimal agents from a pool to match sub-tasks
- Supports tool-level and resource-level permission management
- Provides Hooks interface for security module integration

## Common Commands

```bash
# Install dependencies
pip install -e .                    # Core dependencies
pip install -e ".[dev]"             # With dev tools (pytest, ruff, mypy)
pip install -e ".[mcp]"             # With MCP support

# Run tests
pytest                              # All tests
pytest tests/test_basic.py          # Single test file
pytest tests/test_basic.py::test_permissions_deny  # Single test

# Code quality
ruff check mas/                     # Linting
ruff format mas/                    # Formatting
mypy mas/                           # Type checking
```

## Architecture

```
mas/
├── core/           # Core data structures (Task, Workflow, schemas)
├── agents/         # Agent pool and implementations by capability
├── workflow/       # Workflow factory, decomposer, and templates
├── execution/      # Execution engine, scheduler, runner
├── permissions/    # Tool and resource level permission management
├── hooks/          # Hook system (pre/post tool use, on error)
├── tools/          # MCP tool integration and builtin tools
├── optimization/   # ADAS optimization (reserved)
├── safety/         # Safety interface (reserved)
├── llm/            # LLM client (MiniMax API)
└── utils/          # Config and logging utilities
```

### Core Flow

```
Task Description → Classification → WorkflowFactory → AgentPool.select()
                                         ↓
                                  TaskDecomposer (AOV graph)
                                         ↓
                                  ExecutionEngine
                                         ↓
                             PreToolUse → Tool → PostToolUse
```

### Key Components

- **AgentPool** (`agents/pool.py`): Singleton registry managing agents by capability
- **WorkflowFactory** (`workflow/factory.py`): Creates workflows from templates or LLM
- **ExecutionEngine** (`execution/engine.py`): Runs workflows with hook integration
- **HookManager** (`hooks/manager.py`): Chain-of-responsibility for pre/post tool hooks
- **PermissionManager** (`permissions/manager.py`): Tool and resource access control

### Agent Capabilities

Defined in `core/schemas.py` - `AgentCapability` enum:
- `CODE_GENERATION`, `CODE_REVIEW`, `FRONTEND`, `BACKEND`
- `DATA_ANALYSIS`, `DOCUMENTATION`, `PLANNING`, `GAME_DEV`

### Workflow Templates

Located in `workflow/templates/`:
- `web_app.py` - Web application development (Flask/FastAPI + React/Vue)
- `data_pipeline.py` - ETL, data analysis, reporting
- `game.py` - Simple command-line or GUI games
- `library.py` - Reusable Python packages

## Code Style

- **Type annotations required** on all function parameters and return values
- **4 spaces** for indentation
- **100 char** line limit (ruff configured for 88)
- **Docstrings** in Google style with Chinese descriptions
- **Async-first** design using `asyncio`

### Naming Conventions

```python
class AgentPool:        # PascalCase for classes
def get_agent():        # snake_case for functions
MAX_RETRY = 3           # UPPER_SNAKE_CASE for constants
self._private = None    # Single underscore for private
```

## Environment Variables

```bash
MINIMAX_API_KEY=your_api_key_here   # Required for LLM client
```

## Permission System

Two-level permission model:
1. **Tool Level**: Which agents can call which tools
2. **Resource Level**: File paths, network domains, API access

Permission checks happen in `PreToolUse` hooks before any tool execution.

## Hooks System

Three hook types in `HookType` enum:
- `PRE_TOOL_USE`: Before tool execution (can deny/modify)
- `POST_TOOL_USE`: After tool execution
- `ON_ERROR`: Error handling

Built-in hooks in `hooks/builtin/`:
- `permission_check.py` - Permission validation
- `input_validation.py` - Parameter validation
- `audit_log.py` - Logging

## Testing

Tests use `pytest-asyncio` with auto mode. Core test patterns:

```python
@pytest.mark.asyncio
async def test_example():
    result = await run_task("task description")
    assert result.success
```

## Reference Files

- `DESIGN_PLAN.md` - Detailed system design document
- `AGENTS.md` - AI agent development guidelines
- `idea_summary.md` - Project concept and research background
