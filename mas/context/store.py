from __future__ import annotations

from .types import ContextEntry, ContextLayer, ContextType


class ContextStore:
    """分层上下文存储，按 ContextLayer 组织上下文条目。"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self._layers: dict[ContextLayer, dict[str, ContextEntry]] = {
            ContextLayer.SYSTEM: {},
            ContextLayer.WORKFLOW: {},
            ContextLayer.TASK: {},
            ContextLayer.AGENT: {},
        }
        self._index: dict[str, tuple[ContextLayer, str]] = {}  # id -> (layer, key)

    def add(self, layer: ContextLayer, entry: ContextEntry, key: str | None = None) -> str:
        """添加上下文条目到指定层。

        Args:
            layer: 目标层级。
            entry: 要添加的上下文条目。
            key: 用于层内检索的键，默认为 entry.id。

        Returns:
            str: 被添加条目的 ID。
        """

        entry_id = entry.id
        if entry_id in self._index:
            self.remove(entry_id)

        entry_key = key or entry_id
        self._layers[layer][entry_key] = entry
        self._index[entry_id] = (layer, entry_key)
        return entry_id

    def get(self, entry_id: str) -> ContextEntry | None:
        """通过 ID 获取上下文条目。

        Args:
            entry_id: 条目 ID。

        Returns:
            ContextEntry | None: 匹配的条目。
        """

        resolved = self._resolve_entry(entry_id)
        if resolved is None:
            return None

        entry, _, _ = resolved
        entry.increment_access()
        return entry

    def get_by_key(self, layer: ContextLayer, key: str) -> ContextEntry | None:
        """通过层和键获取上下文条目。

        Args:
            layer: 目标层级。
            key: 层内键。

        Returns:
            ContextEntry | None: 匹配的条目。
        """

        entry = self._layers[layer].get(key)
        if entry is None:
            return None

        entry.increment_access()
        return entry

    def get_layer(self, layer: ContextLayer) -> dict[str, ContextEntry]:
        """获取指定层的所有条目。

        Args:
            layer: 目标层级。

        Returns:
            dict[str, ContextEntry]: 层内条目的浅拷贝。
        """

        return dict(self._layers[layer])

    def get_for_task(self, task_id: str) -> list[ContextEntry]:
        """获取与指定任务相关的上下文条目。

        Args:
            task_id: 任务 ID。

        Returns:
            list[ContextEntry]: 相关上下文条目集合。
        """

        entries: list[ContextEntry] = []
        entries.extend(self._layers[ContextLayer.SYSTEM].values())
        entries.extend(self._layers[ContextLayer.WORKFLOW].values())

        for entry in self._layers[ContextLayer.TASK].values():
            if (
                entry.parent_id == task_id
                or entry.source == task_id
                or task_id in entry.related_ids
            ):
                entries.append(entry)

        return list(entries)

    def get_by_type(self, context_type: ContextType) -> list[ContextEntry]:
        """获取指定类型的所有条目。

        Args:
            context_type: 目标类型。

        Returns:
            list[ContextEntry]: 匹配的上下文条目列表。
        """

        results: list[ContextEntry] = []
        for layer_entries in self._layers.values():
            results.extend(
                entry for entry in layer_entries.values() if entry.type == context_type
            )
        return results

    def update(self, entry_id: str, **kwargs: object) -> bool:
        """更新上下文条目的属性。

        Args:
            entry_id: 目标条目 ID。
            **kwargs: 需要更新的字段。

        Returns:
            bool: 是否成功更新至少一个字段。
        """

        resolved = self._resolve_entry(entry_id)
        if resolved is None:
            return False

        entry, _, _ = resolved
        updated = False
        for field, value in kwargs.items():
            if hasattr(entry, field):
                setattr(entry, field, value)
                updated = True
        return updated

    def remove(self, entry_id: str) -> bool:
        """移除上下文条目。

        Args:
            entry_id: 目标条目 ID。

        Returns:
            bool: 是否成功移除。
        """

        resolved = self._resolve_entry(entry_id)
        if resolved is None:
            return False

        _, layer, key = resolved
        del self._layers[layer][key]
        del self._index[entry_id]
        return True

    def clear_layer(self, layer: ContextLayer) -> int:
        """清空指定层的所有条目。

        Args:
            layer: 目标层级。

        Returns:
            int: 被清除的条目数。
        """

        entries = self._layers[layer]
        removed_ids = [entry.id for entry in entries.values()]
        cleared_count = len(removed_ids)

        for entry_id in removed_ids:
            self._index.pop(entry_id, None)

        entries.clear()
        return cleared_count

    def clear_all(self) -> int:
        """清空所有层的所有条目。

        Returns:
            int: 被清除的条目总数。
        """

        total = 0
        for layer in self._layers:
            total += self.clear_layer(layer)
        return total

    def _resolve_entry(
        self, entry_id: str
    ) -> tuple[ContextEntry, ContextLayer, str] | None:
        """定位条目及其所在层。"""

        mapping = self._index.get(entry_id)
        if mapping is None:
            return None

        layer, key = mapping
        entry = self._layers[layer].get(key)
        if entry is None:
            self._index.pop(entry_id, None)
            return None

        return entry, layer, key
