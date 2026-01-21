from __future__ import annotations

from ..core.schemas import PermissionDecision, PermissionResult


def validate_tool_params(params: dict[str, object]) -> PermissionResult:
    if not params:
        return PermissionResult(
            decision=PermissionDecision.DENY,
            reason="params must not be empty",
        )
    return PermissionResult(decision=PermissionDecision.ALLOW)


def validate_resource_path(path: str) -> PermissionResult:
    if not path:
        return PermissionResult(
            decision=PermissionDecision.DENY,
            reason="resource path required",
        )
    return PermissionResult(decision=PermissionDecision.ALLOW)
