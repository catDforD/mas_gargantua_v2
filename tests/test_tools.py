## 工具调用测试
from mas.permissions.manager import PermissionManager
from mas.permissions.config import PermissionConfig
from mas.core.schemas import PermissionDecision

# 测试工具黑名单
config = PermissionConfig(
    tool_blacklist={"coder": ["file_write", "code_exec"]}
)
manager = PermissionManager(config)

# 被禁止的工具
result = manager.check_tool_permission("coder", "file_write", {})
assert result.decision == PermissionDecision.DENY
print(f"✅ 工具黑名单生效: file_write 被拒绝")

# 允许的工具
result = manager.check_tool_permission("coder", "file_read", {})
assert result.decision == PermissionDecision.ALLOW
print(f"✅ 未禁止的工具允许: file_read")

##  资源级别权限测试
from mas.permissions.config import FileAccessConfig

# 测试文件路径限制
config = PermissionConfig(
    file_access=FileAccessConfig(
        allowed_paths=["/home/user/project"],
        denied_paths=["/etc", "/root"],
    )
)
manager = PermissionManager(config)

# 允许的路径
result = manager.check_resource_permission("agent", "file", "/home/user/project/src/main.py")
print(f"✅ 允许路径检测: {result.decision}")

# 禁止的路径
result = manager.check_resource_permission("agent", "file", "/etc/passwd")
assert result.decision == PermissionDecision.DENY
print(f"✅ 禁止路径检测: /etc/passwd 被拒绝")