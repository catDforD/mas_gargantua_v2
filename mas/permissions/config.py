from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FileAccessConfig:
    allowed_paths: list[str] = field(default_factory=list)
    denied_paths: list[str] = field(default_factory=list)
    read_only_paths: list[str] = field(default_factory=list)
    max_file_size: int = 10 * 1024 * 1024


@dataclass
class NetworkAccessConfig:
    allowed_domains: list[str] = field(default_factory=list)
    denied_domains: list[str] = field(default_factory=list)
    require_https: bool = True


@dataclass
class APIAccessConfig:
    allowed_keys: list[str] = field(default_factory=list)
    denied_keys: list[str] = field(default_factory=list)


@dataclass
class PermissionConfig:
    tool_whitelist: dict[str, list[str]] = field(default_factory=dict)
    tool_blacklist: dict[str, list[str]] = field(default_factory=dict)
    file_access: FileAccessConfig = field(default_factory=FileAccessConfig)
    network_access: NetworkAccessConfig = field(default_factory=NetworkAccessConfig)
    api_access: APIAccessConfig = field(default_factory=APIAccessConfig)
