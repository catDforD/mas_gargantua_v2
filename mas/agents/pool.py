from __future__ import annotations

from typing import ClassVar

from ..core.schemas import AgentCapability, AgentDescriptor


class AgentPoolRegistry:
    _instance: ClassVar[AgentPoolRegistry | None] = None
    _pools: ClassVar[dict[str, AgentDescriptor]] = {}

    def __new__(cls) -> AgentPoolRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, descriptor: AgentDescriptor) -> None:
        if descriptor.name in self._pools:
            raise ValueError(f"Agent already registered: {descriptor.name}")
        self._pools[descriptor.name] = descriptor

    def get(self, name: str) -> AgentDescriptor:
        if name not in self._pools:
            raise KeyError(f"Agent not found: {name}")
        return self._pools[name]

    def get_all(self) -> list[AgentDescriptor]:
        return list(self._pools.values())

    def select_best_agent(
        self, capability: AgentCapability, context: dict[str, str]
    ) -> AgentDescriptor:
        """选择最适合当前任务的 Agent。

        Args:
            capability: 所需的 Agent 能力。
            context: 任务上下文，可包含 task_description, task_id 等信息。

        Returns:
            AgentDescriptor: 选中的 Agent 描述符。

        Raises:
            LookupError: 未找到匹配能力的 Agent。
        """

        candidates = [d for d in self._pools.values() if d.capability == capability]
        if not candidates:
            raise LookupError(f"No agent found for capability: {capability}")

        if len(candidates) == 1 or not context:
            return candidates[0]

        scored = [
            (agent, self._compute_agent_score(agent, context)) for agent in candidates
        ]
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[0][0]

    def _compute_agent_score(
        self,
        agent: AgentDescriptor,
        context: dict[str, str],
    ) -> float:
        """计算 Agent 与当前任务的匹配分数。

        Args:
            agent: Agent 描述符。
            context: 任务上下文。

        Returns:
            float: 匹配分数，越高越好。
        """

        score = 1.0
        task_description = context.get("task_description", "").lower()

        for condition in agent.use_when:
            if condition.lower() in task_description:
                score += 0.5

        for condition in agent.avoid_when:
            if condition.lower() in task_description:
                score -= 0.5

        cost_penalty = {"low": 0.0, "medium": 0.1, "high": 0.2}
        score -= cost_penalty.get(agent.cost, 0.0)
        return score
