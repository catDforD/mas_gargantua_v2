## Hook 注册和执行
import asyncio
from mas.hooks.manager import HookManager
from mas.core.schemas import HookType, HookContext, HookResult, PermissionDecision

manager = HookManager()

# 自定义 Hook
async def custom_hook(context: HookContext) -> HookResult:
    print(f"  Hook 触发: {context.tool_name} by {context.agent_name}")
    return HookResult(decision=PermissionDecision.ALLOW)

# 注册 Hook
manager.register(HookType.PRE_TOOL_USE, custom_hook)

# 执行 Hook
context = HookContext(
    agent_name="test_agent",
    tool_name="test_tool",
    params={},
    session_id="session-1",
    timestamp=0.0,
)

result = asyncio.run(manager.execute_pre_tool_use(context))
print(f"✅ Hook 执行成功: {result.decision}")

## Hook 链短路测试
async def deny_hook(context: HookContext) -> HookResult:
    return HookResult(decision=PermissionDecision.DENY, message="Denied by hook")

async def allow_hook(context: HookContext) -> HookResult:
    print("  这条不应该执行")
    return HookResult(decision=PermissionDecision.ALLOW)

manager2 = HookManager()
manager2.register(HookType.PRE_TOOL_USE, deny_hook)
manager2.register(HookType.PRE_TOOL_USE, allow_hook)

result = asyncio.run(manager2.execute_pre_tool_use(context))
assert result.decision == PermissionDecision.DENY
print(f"✅ Hook 链短路正确: {result.message}")


## 内置 Hook 测试
from mas.hooks.builtin.permission_check import permission_check_hook
from mas.hooks.builtin.input_validation import input_validation_hook
from mas.hooks.builtin.audit_log import audit_log_hook

# 测试输入验证 Hook
empty_context = HookContext(
    agent_name="agent",
    tool_name="",  # 空工具名
    params={},
    session_id="s1",
    timestamp=0.0,
)
result = asyncio.run(input_validation_hook(empty_context))
assert result.decision == PermissionDecision.DENY
print(f"✅ input_validation_hook 拒绝空 tool_name")

# 测试审计日志 Hook
result = asyncio.run(audit_log_hook(context))
print(f"✅ audit_log_hook 执行成功")

