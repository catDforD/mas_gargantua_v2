from __future__ import annotations

import json
import time
import uuid
from typing import TYPE_CHECKING

from .compression import ContextCompressor
from .scorer import ContextScorer
from .store import ContextStore
from .types import ContextEntry, ContextLayer, ContextType
from .window import ContextWindow

if TYPE_CHECKING:
    from ..llm.client import LLMClient


class ContextManager:
    """上下文管理器 - 管理多智能体系统中的上下文。

    提供上下文的添加、检索、压缩和格式化功能。
    """

    def __init__(
        self,
        session_id: str,
        llm_client: LLMClient | None = None,
        max_tokens: int = 8000,
    ) -> None:
        """初始化上下文管理器。

        Args:
            session_id: 会话唯一标识符。
            llm_client: LLM 客户端（用于摘要压缩）。
            max_tokens: 上下文窗口的最大 token 数。
        """

        self.session_id = session_id
        self.store = ContextStore(session_id)
        self.scorer = ContextScorer()
        self.window = ContextWindow(max_tokens=max_tokens)
        self.compressor = ContextCompressor(llm_client)

    async def add_task_output(
        self,
        task_id: str,
        output: str,
        agent_name: str,
        dependent_task_ids: list[str] | None = None,
    ) -> str:
        """添加任务输出到上下文。

        如果输出超过压缩阈值，自动进行压缩。

        Args:
            task_id: 任务 ID。
            output: 任务输出内容。
            agent_name: 执行任务的 Agent 名称。
            dependent_task_ids: 依赖此任务的其他任务 ID。

        Returns:
            str: 创建的上下文条目 ID。
        """

        importance = self.scorer.compute_task_importance(task_id, agent_name)
        related = list(dependent_task_ids or [])
        entry = ContextEntry(
            id=self._generate_entry_id(ContextType.DEPENDENCY_OUTPUT, task_id),
            type=ContextType.DEPENDENCY_OUTPUT,
            content=f"[Agent: {agent_name}] {output}".strip(),
            timestamp=time.time(),
            source=task_id,
            importance=importance,
            parent_id=task_id,
            related_ids=related,
        )

        if await self.compressor.should_compress(entry.content):
            entry = await self.compressor.compress_entry(entry)

        return self.store.add(ContextLayer.TASK, entry)

    async def add_shared_state(
        self,
        key: str,
        value: str | dict[str, object],
        importance: float = 0.7,
    ) -> str:
        """添加工作流级共享状态。

        Args:
            key: 状态键。
            value: 状态值。
            importance: 重要性分数。

        Returns:
            str: 创建的上下文条目 ID。
        """

        entry = ContextEntry(
            id=self._generate_entry_id(ContextType.SHARED_STATE, key),
            type=ContextType.SHARED_STATE,
            content=value,
            timestamp=time.time(),
            source=key,
            importance=importance,
            parent_id=None,
        )
        return self.store.add(ContextLayer.WORKFLOW, entry, key=key)

    async def get_context_for_task(
        self,
        task_id: str,
        dependency_ids: list[str],
        max_tokens: int | None = None,
    ) -> str:
        """获取优化后的任务上下文字符串。

        Args:
            task_id: 当前任务 ID。
            dependency_ids: 依赖任务 ID 列表。
            max_tokens: 最大 token 数限制。

        Returns:
            str: 格式化的上下文字符串。
        """

        dependency_set = set(dependency_ids)
        task_layer_entries = self.store.get_layer(ContextLayer.TASK).values()
        dependency_entries: list[ContextEntry] = []
        for entry in task_layer_entries:
            if self._is_dependency_entry(entry, dependency_set):
                dependency_entries.append(entry)

        shared_entries = list(self.store.get_layer(ContextLayer.WORKFLOW).values())
        candidates = dependency_entries + shared_entries
        if not candidates:
            return self._format_context([], task_id)

        ranked = self.scorer.rank_entries(candidates, target_task_id=task_id)
        selected = self.window.select(ranked, max_tokens=max_tokens)
        return self._format_context(selected, task_id)

    def _format_context(
        self,
        entries: list[ContextEntry],
        current_task_id: str,
    ) -> str:
        """格式化上下文条目为结构化字符串。

        Args:
            entries: 选中的上下文条目。
            current_task_id: 当前任务 ID。

        Returns:
            str: 格式化的上下文字符串。
        """

        if not entries:
            return f"## 上下文\n- 任务 {current_task_id} 暂无可用上下文。"

        dependency_sections: list[str] = []
        shared_sections: list[str] = []
        other_sections: list[str] = []

        for entry in entries:
            formatted_content = self._stringify(entry)
            header = f"- 来源 {entry.source} | 重要性 {entry.importance:.2f}\n{formatted_content}"
            if entry.type == ContextType.SHARED_STATE:
                shared_sections.append(header)
            elif entry.type == ContextType.DEPENDENCY_OUTPUT or entry.type == ContextType.ERROR_CONTEXT:
                dependency_sections.append(header)
            else:
                other_sections.append(header)

        parts: list[str] = []
        if dependency_sections:
            parts.append("## 前置任务的输出")
            parts.extend(dependency_sections)
        if shared_sections:
            parts.append("## 共享状态")
            parts.extend(shared_sections)
        if other_sections:
            parts.append("## 其他上下文")
            parts.extend(other_sections)

        return "\n".join(parts)

    async def add_error_context(
        self,
        task_id: str,
        error: str,
        agent_name: str,
    ) -> str:
        """添加错误上下文。

        Args:
            task_id: 任务 ID。
            error: 错误信息。
            agent_name: Agent 名称。

        Returns:
            str: 创建的上下文条目 ID。
        """

        importance = min(1.0, self.scorer.compute_task_importance(task_id, agent_name) + 0.2)
        entry = ContextEntry(
            id=self._generate_entry_id(ContextType.ERROR_CONTEXT, task_id),
            type=ContextType.ERROR_CONTEXT,
            content=f"[Agent: {agent_name}] {error}".strip(),
            timestamp=time.time(),
            source=task_id,
            importance=importance,
            parent_id=task_id,
        )

        if await self.compressor.should_compress(entry.content):
            entry = await self.compressor.compress_entry(entry)

        return self.store.add(ContextLayer.TASK, entry)

    def clear_task_context(self) -> int:
        """清空任务层上下文。返回清除的条目数。"""

        return self.store.clear_layer(ContextLayer.TASK)

    def clear_agent_context(self) -> int:
        """清空 Agent 层上下文。返回清除的条目数。"""

        return self.store.clear_layer(ContextLayer.AGENT)

    def get_stats(self) -> dict[str, object]:
        """获取上下文管理统计信息。

        Returns:
            dict[str, object]: 包含各层条目数量、总 token 估算等信息。
        """

        layer_counts: dict[str, int] = {}
        all_entries: list[ContextEntry] = []
        for layer in (
            ContextLayer.SYSTEM,
            ContextLayer.WORKFLOW,
            ContextLayer.TASK,
            ContextLayer.AGENT,
        ):
            layer_entries = list(self.store.get_layer(layer).values())
            layer_counts[layer.name.lower()] = len(layer_entries)
            all_entries.extend(layer_entries)

        return {
            "session_id": self.session_id,
            "layer_counts": layer_counts,
            "total_entries": len(all_entries),
            "token_estimate": self.window.estimate_total_tokens(all_entries),
            "timestamp": time.time(),
        }

    def _generate_entry_id(self, context_type: ContextType, identifier: str) -> str:
        return f"{context_type.value}_{identifier}_{uuid.uuid4().hex[:8]}"

    def _is_dependency_entry(
        self, entry: ContextEntry, dependency_ids: set[str]
    ) -> bool:
        if entry.source in dependency_ids:
            return True
        if entry.parent_id and entry.parent_id in dependency_ids:
            return True
        return bool(dependency_ids.intersection(entry.related_ids))

    def _stringify(self, entry: ContextEntry) -> str:
        content = entry.summary if entry.is_compressed and entry.summary else entry.content
        if isinstance(content, str):
            return content.strip() or "(空)"
        try:
            return json.dumps(content, ensure_ascii=False, sort_keys=True)
        except Exception:
            return str(content)
