from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from enum import Enum


class ContextType(str, Enum):
    """上下文实体类型。"""

    DEPENDENCY_OUTPUT = "dependency_output"
    SHARED_STATE = "shared_state"
    TOOL_RESULT = "tool_result"
    LLM_RESPONSE = "llm_response"
    ERROR_CONTEXT = "error_context"
    CONFIGURATION = "configuration"


class ContextLayer(int, Enum):
    """上下文所属层级。"""

    SYSTEM = 0
    WORKFLOW = 1
    TASK = 2
    AGENT = 3


class ContentCategory(str, Enum):
    """内容类别：代码、文档或混合。"""

    CODE = "code"
    DOCUMENT = "document"
    MIXED = "mixed"


@dataclass
class ContextEntry:
    """上下文条目，用于追踪运行时产生的关键数据。"""

    id: str
    type: ContextType
    content: str | dict[str, object]
    timestamp: float
    source: str
    importance: float = 0.5
    relevance_score: float = 0.5
    access_count: int = 0
    ttl: int | None = None
    parent_id: str | None = None
    related_ids: list[str] = field(default_factory=list)
    is_compressed: bool = False
    original_length: int = 0
    summary: str | None = None
    content_category: ContentCategory = ContentCategory.DOCUMENT
    code_file_path: str | None = None

    def compute_score(self, current_task_id: str | None = None) -> float:
        """计算上下文条目的综合分数。

        Args:
            current_task_id: 当前任务 ID，用于未来扩展更细致的调度逻辑。

        Returns:
            float: 综合分值，范围为 0.0-1.0。
        """

        _ = current_task_id  # 预留参数，未来可结合任务信息进行调优
        current_time = time.time()
        age_seconds = max(current_time - self.timestamp, 0.0)
        recency_score = math.exp(-(age_seconds) / 3600.0)
        frequency_score = min(self.access_count / 10.0, 1.0)
        return (
            self.importance * 0.4
            + self.relevance_score * 0.3
            + recency_score * 0.2
            + frequency_score * 0.1
        )

    def increment_access(self) -> None:
        """记录上下文条目被访问一次。"""

        self.access_count += 1
