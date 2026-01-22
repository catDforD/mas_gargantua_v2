"""MAS 上下文管理模块。

提供多层次的上下文管理功能，包括：
- 分层存储 (System/Workflow/Task/Agent)
- 重要性评分
- Token 窗口管理
- LLM 摘要压缩
"""

from __future__ import annotations

from .compression import ContextCompressor
from .manager import ContextManager
from .scorer import ContextScorer
from .store import ContextStore
from .types import ContentCategory, ContextEntry, ContextLayer, ContextType
from .window import ContextWindow

__all__ = [
    "ContextCompressor",
    "ContentCategory",
    "ContextEntry",
    "ContextLayer",
    "ContextManager",
    "ContextScorer",
    "ContextStore",
    "ContextType",
    "ContextWindow",
]
