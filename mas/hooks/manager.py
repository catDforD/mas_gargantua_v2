from __future__ import annotations

from collections import defaultdict
from collections.abc import Awaitable, Callable

from ..core.schemas import HookContext, HookResult, HookType, PermissionDecision

HookHandler = Callable[[HookContext], Awaitable[HookResult]]


class HookManager:
    def __init__(self) -> None:
        self._hooks: dict[HookType, list[HookHandler]] = defaultdict(list)

    def register(self, hook_type: HookType, handler: HookHandler) -> None:
        self._hooks[hook_type].append(handler)

    async def execute_pre_tool_use(self, context: HookContext) -> HookResult:
        for handler in self._hooks.get(HookType.PRE_TOOL_USE, []):
            result = await handler(context)
            if result.decision == PermissionDecision.DENY:
                return result
            if result.decision == PermissionDecision.ALLOW:
                continue
            if result.decision == PermissionDecision.ASK:
                return result
            if result.modified_params:
                context.params = result.modified_params
        return HookResult(decision=PermissionDecision.ALLOW)

    async def execute_post_tool_use(
        self, context: HookContext, _result: object
    ) -> HookResult:
        for handler in self._hooks.get(HookType.POST_TOOL_USE, []):
            hook_result = await handler(context)
            if hook_result.decision != PermissionDecision.ALLOW:
                return hook_result
        return HookResult(decision=PermissionDecision.ALLOW)

    async def execute_on_error(self, context: HookContext) -> HookResult:
        for handler in self._hooks.get(HookType.ON_ERROR, []):
            hook_result = await handler(context)
            if hook_result.decision != PermissionDecision.ALLOW:
                return hook_result
        return HookResult(decision=PermissionDecision.ALLOW)
