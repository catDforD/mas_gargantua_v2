from __future__ import annotations

import json
import re
from dataclasses import replace
from typing import TYPE_CHECKING

from .types import ContentCategory, ContextEntry

if TYPE_CHECKING:
    from ..llm.client import LLMClient


class ContextCompressor:
    """上下文压缩器，使用 LLM 进行摘要压缩。"""

    SUMMARY_PROMPT = """请简洁地总结以下内容，保留关键信息：

{text}

要求：
1. 控制在 {max_length} 字符以内
2. 保留主要结论和关键数据
3. 保留重要的技术细节
4. 使用简洁的语言

摘要："""

    COMPRESSION_THRESHOLD = 4000

    CODE_PATTERNS = [
        r"^```\w+",
        r"^def\s+\w+",
        r"^class\s+\w+",
        r"^import\s+",
        r"^from\s+",
        r"^\s*if\s+__name__",
        r"^\s*\w+\s*=\s*\(",
    ]

    CODE_BLOCK_MARKERS = [
        "```python",
        "```js",
        "```java",
        "```ts",
        "```go",
        "```rust",
        "```cpp",
        "```sql",
    ]

    def __init__(self, llm_client: LLMClient | None = None):
        self._llm_client = llm_client

    async def summarize(self, text: str, max_length: int = 1000) -> str:
        """使用 LLM 或智能截断生成摘要。

        Args:
            text: 待压缩文本。
            max_length: 摘要允许的最大长度。

        Returns:
            str: 压缩后的摘要。
        """

        if not text:
            return ""

        if self._llm_client is None:
            return self.truncate_smart(text, max_length)

        prompt = self.SUMMARY_PROMPT.format(text=text, max_length=max_length)
        try:
            summary = await self._llm_client.acomplete(prompt, temperature=0.3)
        except Exception:
            return self.truncate_smart(text, max_length)

        cleaned = (summary or "").strip()
        if not cleaned:
            return self.truncate_smart(text, max_length)

        if len(cleaned) > max_length:
            return self.truncate_smart(cleaned, max_length)

        return cleaned

    def truncate_smart(self, text: str, max_length: int) -> str:
        """智能截断文本，尽量保持句子边界。

        Args:
            text: 原始文本。
            max_length: 最大字符数。

        Returns:
            str: 截断后的文本。
        """

        if len(text) <= max_length:
            return text

        boundary_candidates = [
            text.rfind("。", 0, max_length),
            text.rfind(".", 0, max_length),
            text.rfind("\n", 0, max_length),
        ]
        boundary = max(boundary_candidates)

        if boundary != -1 and boundary >= max_length * 0.5:
            return text[: boundary + 1]

        truncated = text[:max_length].rstrip()
        return f"{truncated}..."

    def detect_content_category(self, content: str) -> ContentCategory:
        """Detect if content is code, document, or mixed."""

        if not content:
            return ContentCategory.DOCUMENT

        lines = content.splitlines()
        has_code_marker = any(marker in content for marker in self.CODE_BLOCK_MARKERS)
        if has_code_marker:
            in_block = False
            outside_text = False
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("```"):
                    in_block = not in_block
                    continue
                if not in_block and stripped:
                    outside_text = True
                    break
            return ContentCategory.MIXED if outside_text else ContentCategory.CODE

        non_empty_lines = [line for line in lines if line.strip()]
        if not non_empty_lines:
            return ContentCategory.DOCUMENT

        pattern_hits = 0
        for line in non_empty_lines:
            if any(re.match(pattern, line) for pattern in self.CODE_PATTERNS):
                pattern_hits += 1

        if pattern_hits == 0:
            return ContentCategory.DOCUMENT
        if pattern_hits == len(non_empty_lines):
            return ContentCategory.CODE
        return ContentCategory.MIXED

    async def should_compress(
        self,
        content: str | dict[str, object],
        content_category: ContentCategory | None = None,
    ) -> bool:
        """判断内容长度是否超过压缩阈值。

        Args:
            content: 待检测内容。
            content_category: 内容类别（用于跳过代码压缩）。

        Returns:
            bool: 是否需要压缩。
        """

        if content_category == ContentCategory.CODE:
            return False

        text = self._stringify(content)
        return len(text) >= self.COMPRESSION_THRESHOLD

    async def compress_entry(
        self, entry: ContextEntry, max_length: int = 1000
    ) -> ContextEntry:
        """压缩上下文条目并返回新条目。

        Args:
            entry: 待压缩的上下文条目。
            max_length: 摘要允许的最大长度。

        Returns:
            ContextEntry: 已压缩的条目副本。
        """

        if entry.is_compressed and entry.summary:
            return entry

        text_content = entry.summary or self._stringify(entry.content)
        summary = await self.summarize(text_content, max_length=max_length)
        return replace(
            entry,
            is_compressed=True,
            original_length=len(text_content),
            summary=summary,
        )

    def _stringify(self, content: str | dict[str, object]) -> str:
        if isinstance(content, str):
            return content
        try:
            return json.dumps(content, ensure_ascii=False, sort_keys=True)
        except Exception:
            return str(content)
