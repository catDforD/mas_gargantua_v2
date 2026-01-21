from __future__ import annotations

from ...core.schemas import HookContext, HookResult, PermissionDecision


async def input_validation_hook(context: HookContext) -> HookResult:
    if not context.tool_name:
        return HookResult(
            decision=PermissionDecision.DENY,
            message="tool_name is required",
        )
    return HookResult(decision=PermissionDecision.ALLOW)
