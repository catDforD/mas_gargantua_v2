from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RuntimeConfig:
    environment: str = "dev"
    log_level: str = "INFO"
