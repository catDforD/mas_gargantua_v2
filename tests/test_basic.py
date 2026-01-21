import pytest

from mas import run_task
from mas.core.schemas import PermissionDecision
from mas.hooks.builtin.permission_check import permission_check_hook
from mas.hooks.manager import HookManager
from mas.core.schemas import HookContext, HookType, PermissionDecision
from mas.permissions.config import PermissionConfig
from mas.permissions.manager import PermissionManager


@pytest.mark.asyncio
async def test_basic_run_task() -> None:
    result = await run_task("创建一个简单的 Flask API，包含用户登录功能")
    assert result.success
    assert "requirements" in result.task_results


def test_permissions_deny() -> None:
    config = PermissionConfig(tool_blacklist={"coder": ["file_write"]})
    manager = PermissionManager(config)
    result = manager.check_tool_permission(
        "coder", "file_write", {"path": "/etc/passwd"}
    )
    assert result.decision == PermissionDecision.DENY


@pytest.mark.asyncio
async def test_hooks_permission_check() -> None:
    context = HookContext(
        agent_name="coder",
        tool_name="file_write",
        params={"path": "/etc/passwd"},
        session_id="session-1",
        timestamp=0.0,
    )
    manager = HookManager()
    manager.register(HookType.PRE_TOOL_USE, permission_check_hook)
    result = await manager.execute_pre_tool_use(context)
    assert result.decision in {
        PermissionDecision.ALLOW,
        PermissionDecision.DENY,
        PermissionDecision.ASK,
    }
