from __future__ import annotations

import json
from collections.abc import Iterable

from .types import ContextEntry, ContextType


class ContextScorer:
    """上下文重要性评分器。"""

    TYPE_WEIGHTS: dict[ContextType, float] = {
        ContextType.DEPENDENCY_OUTPUT: 0.8,
        ContextType.SHARED_STATE: 0.7,
        ContextType.TOOL_RESULT: 0.6,
        ContextType.LLM_RESPONSE: 0.5,
        ContextType.ERROR_CONTEXT: 0.9,
        ContextType.CONFIGURATION: 0.4,
    }

    def compute_task_importance(self, task_id: str, agent_name: str) -> float:
        """计算任务输出的基础重要性分数。

        Args:
            task_id: 任务标识符。
            agent_name: 处理该任务的 Agent 名称。

        Returns:
            float: 0.5-1.0 范围内的分数。
        """

        base = 0.6
        normalized_task = task_id.lower()
        normalized_agent = agent_name.lower()

        if "critical" in normalized_task or "safety" in normalized_task:
            base += 0.2
        elif "workflow" in normalized_task or "planner" in normalized_agent:
            base += 0.1

        if normalized_agent.endswith("-reviewer"):
            base += 0.05

        noise = (abs(hash((task_id, agent_name))) % 40) / 200.0
        score = max(0.5, min(1.0, base + noise))
        return score

    def compute_relevance(
        self,
        entry: ContextEntry,
        target_task_id: str,
        dependency_ids: list[str],
    ) -> float:
        """计算上下文条目与目标任务的相关性。

        Args:
            entry: 上下文条目。
            target_task_id: 目标任务 ID。
            dependency_ids: 目标任务依赖的任务 ID 列表。

        Returns:
            float: 相关性得分。
        """

        if entry.source in dependency_ids:
            return 1.0

        if target_task_id in entry.related_ids:
            return 0.9

        return self.TYPE_WEIGHTS.get(entry.type, 0.5)

    def rank_entries(
        self, entries: list[ContextEntry], target_task_id: str | None = None
    ) -> list[ContextEntry]:
        """按综合得分排序上下文条目（降序）。

        Args:
            entries: 待排序的上下文条目。
            target_task_id: 当前关注的任务 ID。

        Returns:
            list[ContextEntry]: 已按分数排序的上下文条目。
        """

        if not entries:
            return []

        dependency_ids = self._collect_dependency_ids(entries)
        for entry in entries:
            entry.importance = self._compute_entry_importance(entry)
            if target_task_id:
                entry.relevance_score = self.compute_relevance(
                    entry, target_task_id, dependency_ids
                )
            else:
                entry.relevance_score = max(
                    entry.relevance_score, self.TYPE_WEIGHTS.get(entry.type, 0.5)
                )

        scored = sorted(
            entries,
            key=lambda item: item.compute_score(current_task_id=target_task_id),
            reverse=True,
        )
        return scored

    def _collect_dependency_ids(self, entries: Iterable[ContextEntry]) -> list[str]:
        return [
            entry.source
            for entry in entries
            if entry.type == ContextType.DEPENDENCY_OUTPUT
        ]

    def _compute_entry_importance(self, entry: ContextEntry) -> float:
        type_weight = self.TYPE_WEIGHTS.get(entry.type, 0.5)
        content_text = self._stringify_content(entry.content)
        length_factor = min(len(content_text) / 2000.0, 1.0)
        access_penalty = min(entry.access_count / 20.0, 0.1)
        importance = type_weight + 0.2 * length_factor - access_penalty
        return max(0.3, min(1.0, importance))

    def _stringify_content(self, content: str | dict[str, object]) -> str:
        if isinstance(content, str):
            return content
        return json.dumps(content, ensure_ascii=False, sort_keys=True)
