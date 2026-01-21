from mas.agents.pool import AgentPoolRegistry
from mas.agents.implementations import (
    backend_descriptor,
    code_generation_descriptor,
    frontend_descriptor,
    planning_descriptor,
    game_dev_descriptor,
)
from mas.core.schemas import AgentCapability

# 获取单例
pool = AgentPoolRegistry()

# 注册智能体
pool.register(backend_descriptor())
pool.register(code_generation_descriptor())
pool.register(frontend_descriptor())
pool.register(planning_descriptor())
pool.register(game_dev_descriptor())

print(f"✅ 已注册 {len(pool._pools)} 个智能体")

# 按能力选择智能体
agent = pool.select_best_agent(AgentCapability.BACKEND, {})
print(f"✅ 选择后端智能体: {agent.name}, 策略: {agent.strategy}")

agent = pool.select_best_agent(AgentCapability.PLANNING, {})
print(f"✅ 选择规划智能体: {agent.name}, 策略: {agent.strategy}")

# 测试未注册能力
try:
    pool.select_best_agent(AgentCapability.DOCUMENTATION, {})
    print("❌ 应该抛出 LookupError")
except LookupError as e:
    print(f"✅ 正确处理未注册能力: {e}")