from __future__ import annotations

from ...core.schemas import HookContext, HookResult, PermissionDecision
from ...utils.logger import get_logger


async def audit_log_hook(context: HookContext) -> HookResult:
    logger = get_logger("mas.hooks.audit")
    logger.info(
        "agent=%s tool=%s session=%s params=%s",
        context.agent_name,
        context.tool_name,
        context.session_id,
        context.params,
    )
    return HookResult(decision=PermissionDecision.ALLOW)
