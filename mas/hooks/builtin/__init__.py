from __future__ import annotations

from ..manager import HookManager
from ..types import HookType
from .audit_log import audit_log_hook
from .input_validation import input_validation_hook
from .permission_check import permission_check_hook


def register_builtin_hooks(manager: HookManager) -> None:
    manager.register(HookType.PRE_TOOL_USE, permission_check_hook)
    manager.register(HookType.PRE_TOOL_USE, input_validation_hook)
    manager.register(HookType.POST_TOOL_USE, audit_log_hook)


__all__ = ["register_builtin_hooks"]
