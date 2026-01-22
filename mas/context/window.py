from __future__ import annotations

import math
from typing import Any

from .types import ContextEntry


class ContextWindow:
    """上下文窗口管理器，处理 token 预算内的上下文选择。"""

    DEFAULT_MAX_TOKENS = 8000

    def __init__(self, max_tokens: int = DEFAULT_MAX_TOKENS):
        self.max_tokens = max_tokens
        self._encoding: Any = None

    def count_tokens(self, text: str) -> int:
        """计算文本的 token 数。

        Args:
            text: 待统计的文本。

        Returns:
            int: 估算的 token 数。
        """

        if not text:
            return 0

        encoding = self._ensure_encoding()
        if encoding is not None:
            try:
                return len(encoding.encode(text))
            except Exception:
                self._encoding = None

        return max(1, math.ceil(len(text) / 4))

    def select(
        self, entries: list[ContextEntry], max_tokens: int | None = None
    ) -> list[ContextEntry]:
        """贪心选择上下文条目，在 token 预算内选择最高分的条目。

        Args:
            entries: 可供选择的上下文条目。
            max_tokens: token 预算，默认为实例配置。

        Returns:
            list[ContextEntry]: 被选中的条目列表。
        """

        budget = max_tokens or self.max_tokens
        if budget <= 0 or not entries:
            return []

        ordered = sorted(entries, key=lambda item: item.compute_score(), reverse=True)
        selected: list[ContextEntry] = []
        tokens_used = 0

        for entry in ordered:
            entry_tokens = self._entry_tokens(entry)
            if entry_tokens > budget:
                continue
            if tokens_used + entry_tokens > budget:
                continue

            selected.append(entry)
            tokens_used += entry_tokens
            entry.increment_access()

        return selected

    def estimate_total_tokens(self, entries: list[ContextEntry]) -> int:
        """估算条目列表的总 token 数。

        Args:
            entries: 需要估算的上下文条目列表。

        Returns:
            int: 总 token 数估算。
        """

        return sum(self._entry_tokens(entry) for entry in entries)

    def _ensure_encoding(self) -> Any:
        if self._encoding is not None:
            return self._encoding

        try:
            import tiktoken

            self._encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self._encoding = None

        return self._encoding

    def _entry_tokens(self, entry: ContextEntry) -> int:
        content = entry.summary if entry.is_compressed and entry.summary else entry.content
        text = content if isinstance(content, str) else str(content)
        return self.count_tokens(text)
