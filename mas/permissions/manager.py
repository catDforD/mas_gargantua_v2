from __future__ import annotations

import os

from ..core.schemas import PermissionDecision, PermissionResult
from .config import PermissionConfig


class PermissionManager:
    config: PermissionConfig

    def __init__(self, config: PermissionConfig | None = None):
        self.config = config or PermissionConfig()

    def check_tool_permission(
        self, agent_name: str, tool_name: str, _params: dict[str, object]
    ) -> PermissionResult:
        allow_list = self.config.tool_whitelist.get(agent_name, [])
        deny_list = self.config.tool_blacklist.get(agent_name, [])

        if tool_name in deny_list:
            return PermissionResult(
                decision=PermissionDecision.DENY, reason="tool denied"
            )

        if allow_list and tool_name not in allow_list:
            return PermissionResult(
                decision=PermissionDecision.DENY, reason="tool not allowed"
            )

        return PermissionResult(decision=PermissionDecision.ALLOW)

    def check_resource_permission(
        self, _agent_name: str, resource_type: str, resource_path: str
    ) -> PermissionResult:
        file_access = self.config.file_access
        if resource_type == "file":
            normalized = self._normalize_path(resource_path)
            denied = [self._normalize_path(path) for path in file_access.denied_paths]
            allowed = [self._normalize_path(path) for path in file_access.allowed_paths]

            if denied and self._path_matches(normalized, denied):
                return PermissionResult(
                    decision=PermissionDecision.DENY, reason="path denied"
                )
            if allowed and not self._path_matches(normalized, allowed):
                return PermissionResult(
                    decision=PermissionDecision.DENY, reason="path not allowed"
                )

        return PermissionResult(decision=PermissionDecision.ALLOW)

    def _normalize_path(self, path: str) -> str:
        normalized = os.path.realpath(path)
        return normalized.rstrip(os.sep)

    def _path_matches(self, path: str, candidates: list[str]) -> bool:
        for candidate in candidates:
            if path == candidate:
                return True
            if path.startswith(candidate + os.sep):
                return True
        return False
