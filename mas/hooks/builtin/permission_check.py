from __future__ import annotations

from ...core.schemas import HookContext, HookResult, PermissionDecision
from ...permissions.manager import PermissionManager


async def permission_check_hook(context: HookContext) -> HookResult:
    manager = PermissionManager()
    result = manager.check_tool_permission(
        context.agent_name, context.tool_name, context.params
    )
    if result.decision != PermissionDecision.ALLOW:
        return HookResult(
            decision=result.decision,
            message=result.reason,
            metadata=result.metadata,
        )
    return HookResult(decision=PermissionDecision.ALLOW)
