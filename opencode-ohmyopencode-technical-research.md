# OpenCode & Oh My OpenCode 技术调研报告

生成时间：2026-01-19

---

## 目录

- [OpenCode — 深度技术细节](#opencode---深度技术细节)
  - [MCP 实现](#mcp-实现)
  - [核心架构](#核心架构)
  - [源码关键位置](#源码关键位置)
- [Oh My OpenCode — 深度技术细节](#oh-my-opencode---深度技术细节)
  - [Agent 系统](#agent-系统)
  - [Specialized Agents 架构](#specialized-agents-架构)
  - [Hooks 系统](#hooks-系统)
  - [源码关键位置](#源码关键位置-1)

---

## OpenCode — 深度技术细节

### MCP 实现

#### 配置与注册
MCP 服务器配置在 `mcpServers` 配置项中，支持两种传输类型：

```json
{
  "mcpServers": {
    "example": {
      "type": "stdio",
      "command": "path/to/mcp-server",
      "env": [],
      "args": []
    },
    "web-example": {
      "type": "sse",
      "url": "https://example.com/mcp",
      "headers": {
        "Authorization": "Bearer token"
      }
    }
  }
}
```

配置类型定义（Go）：
```go
type MCPType string

const (
    MCPStdio MCPType = "stdio"
    MCPSse   MCPType = "sse"
)

type MCPServer struct {
    Command string            `json:"command"`
    Env     []string          `json:"env"`
    Args    []string          `json:"args"`
    Type    MCPType           `json:"type"`
    URL     string            `json:"url"`
    Headers map[string]string `json:"headers"`
}
```

默认类型处理：
```go
for k, v := range cfg.MCPServers {
    if v.Type == "" {
        v.Type = MCPStdio
        cfg.MCPServers[k] = v
    }
}
```

#### 工具发现流程
启动时（goroutine，30s 超时），OpenCode 通过 `mark3labs/mcp-go` 初始化 MCP 客户端：

```go
go func() {
    defer logging.RecoverPanic("MCP-goroutine", nil)
    ctxWithTimeout, cancel := context.WithTimeout(ctx, 30*time.Second)
    defer cancel()
    agent.GetMcpTools(ctxWithTimeout, app.Permissions)
    logging.Info("MCP message handling goroutine exiting")
}()
```

工具注册流程：
```go
// 初始化
initRequest.Params.ProtocolVersion = mcp.LATEST_PROTOCOL_VERSION
initRequest.Params.ClientInfo = mcp.Implementation{
    Name:    "OpenCode",
    Version: version.Version,
}
_, err := c.Initialize(ctx, initRequest)

// 发现工具
toolsRequest := mcp.ListToolsRequest{}
tools, err := c.ListTools(ctx, toolsRequest)

// 注册工具（命名格式：serverName_toolName）
for _, t := range tools.Tools {
    stdioTools = append(stdioTools, NewMcpTool(name, t, permissions, m))
}
```

工具信息提取：
```go
return tools.ToolInfo{
    Name:        fmt.Sprintf("%s_%s", b.mcpName, b.tool.Name),
    Description: b.tool.Description,
    Parameters:  b.tool.InputSchema.Properties,
    Required:    required,
}
```

JSON Schema 验证：
```json
{
  "mcpServers": {
    "additionalProperties": {
      "properties": {
        "args": { "type": "array", "items": { "type": "string" } },
        "command": { "type": "string" },
        "env": { "type": "array", "items": { "type": "string" } },
        "headers": { "type": "object", "additionalProperties": { "type": "string" } },
        "type": { "default": "stdio", "enum": ["stdio", "sse"], "type": "string" },
        "url": { "type": "string" }
      },
      "required": ["command"]
    }
  }
}
```

#### 权限拦截
每次 MCP 工具调用前执行权限检查：

```go
p := b.permissions.Request(
    permission.CreatePermissionRequest{
        SessionID:   sessionID,
        Path:        config.WorkingDirectory(),
        ToolName:    b.Info().Name,
        Action:      "execute",
        Description: permissionDescription,
        Params:      params.Input,
    },
)
if !p {
    return tools.NewTextErrorResponse("permission denied"), nil
}
```

#### 消息流
```
Agent 请求 → 权限检查 → 初始化 MCP 会话 → 解析 JSON 输入 → CallTool → 返回文本内容
```

工具执行流程：
```go
// 解析 JSON 输入
if err = json.Unmarshal([]byte(input), &args); err != nil {
    return tools.NewTextErrorResponse(fmt.Sprintf("error parsing parameters: %s", err)), nil
}
toolRequest.Params.Arguments = args
result, err := c.CallTool(ctx, toolRequest)
```

传输类型支持：
```go
switch b.mcpConfig.Type {
case config.MCPStdio:
    c, err := client.NewStdioMCPClient(
        b.mcpConfig.Command,
        b.mcpConfig.Env,
        b.mcpConfig.Args...,
    )
    ...
    return runTool(ctx, c, b.tool.Name, params.Input)
case config.MCPSse:
    c, err := client.NewSSEMCPClient(
        b.mcpConfig.URL,
        client.WithHeaders(b.mcpConfig.Headers),
    )
    ...
    return runTool(ctx, c, b.tool.Name, params.Input)
}
```

### 核心架构

#### 客户端/服务器分离
- **TUI 客户端**：终端用户界面
- **本地服务器**：暴露 OpenAPI 3.1 端点，用于 SDK 和多客户端访问

当运行 `opencode` 时：
1. 启动 TUI 客户端
2. 启动本地服务器
3. 服务器暴露 OpenAPI 3.1 规范端点
4. 该端点用于生成 SDK

#### SDK 生成
- 从 OpenAPI 3.1 规范生成 SDK
- 支持多语言绑定
- SDK 可以独立调用 OpenCode 服务器

#### 权限系统
基于规则引擎，支持三种决策模式：

| 决策 | 说明 |
|------|------|
| `allow` | 自动允许执行 |
| `ask` | 请求用户批准 |
| `deny` | 拒绝执行 |

默认行为：
- 大多数权限默认为 `allow`
- `doom_loop` 和 `external_directory` 默认为 `ask`

### 源码关键位置

| 组件 | 路径 |
|------|------|
| 配置 | `internal/config/config.go` |
| MCP 工具 | `internal/llm/agent/mcp-tools.go` |
| Schema 生成 | `cmd/schema/main.go` |
| Schema 定义 | `opencode-schema.json` |
| 启动入口 | `cmd/root.go` |
| 服务器 | `internal/server/server.go` |

---

## Oh My OpenCode — 深度技术细节

### Agent 系统

#### Schema 定义
Agent 覆盖配置使用 Zod schema 定义：

```typescript
export const BuiltinAgentNameSchema = z.enum([
  "Sisyphus",
  "oracle",
  "librarian",
  "explore",
  "frontend-ui-ux-engineer",
  "document-writer",
  "multimodal-looker",
  "Metis (Plan Consultant)",
  "Momus (Plan Reviewer)",
  "orchestrator-sisyphus",
])

export const AgentOverrideConfigSchema = z.object({
  model: z.string().optional(),
  variant: z.string().optional(),
  category: z.string().optional(),
  skills: z.array(z.string()).optional(),
  temperature: z.number().min(0).max(2).optional(),
  top_p: z.number().min(0).max(1).optional(),
  prompt: z.string().optional(),
  prompt_append: z.string().optional(),
  tools: z.record(z.string(), z.boolean()).optional(),
  disable: z.boolean().optional(),
  description: z.string().optional(),
  mode: z.enum(["subagent", "primary", "all"]).optional(),
  color: z.string().regex(/^#[0-9A-Fa-f]{6}$/).optional(),
  permission: AgentPermissionSchema.optional(),
})

export const AgentOverridesSchema = z.object({
  oracle: AgentOverrideConfigSchema.optional(),
  librarian: AgentOverrideConfigSchema.optional(),
  explore: AgentOverrideConfigSchema.optional(),
  // ... 其他内置 agents
})
```

#### Agent 注册
内置 agents 注册表：

```typescript
export const builtinAgents: Record<string, AgentConfig> = {
  Sisyphus: sisyphusAgent,
  oracle: oracleAgent,
  librarian: librarianAgent,
  explore: exploreAgent,
  "frontend-ui-ux-engineer": frontendUiUxEngineerAgent,
  "document-writer": documentWriterAgent,
  "multimodal-looker": multimodalLookerAgent,
  "Metis (Plan Consultant)": metisAgent,
  "Momus (Plan Reviewer)": momusAgent,
  "orchestrator-sisyphus": orchestratorSisyphusAgent,
}
```

Agent 构建流程：
```typescript
const agentSources: Record<BuiltinAgentName, AgentSource> = { ... }

export function buildAgent(...) {
  const base = isFactory(source) ? source(model) : source
  ...

  // 应用分类默认值
  if (agentWithCategory.category) {
    const categoryConfig = categoryConfigs[agentWithCategory.category]
    if (categoryConfig) {
      if (!base.model) base.model = categoryConfig.model
      if (base.temperature === undefined && categoryConfig.temperature !== undefined) {
        base.temperature = categoryConfig.temperature
      }
      if (base.variant === undefined && categoryConfig.variant !== undefined) {
        base.variant = categoryConfig.variant
      }
    }
  }

  // 解析技能并注入提示
  if (agentWithCategory.skills?.length) {
    const { resolved } = resolveMultipleSkills(agentWithCategory.skills, { gitMasterConfig })
    ...
    base.prompt = skillContent + (base.prompt ? "\n\n" + base.prompt : "")
  }

  return base
}

export function createBuiltinAgents(...) {
  ...
  for (const [name, source] of Object.entries(agentSources)) {
    ...
    let config = buildAgent(source, model, mergedCategories, gitMasterConfig)
    ...
    if (override) {
      config = mergeAgentConfig(config, override)
    }
    result[name] = config
    ...
  }
  ...
}
```

Plugin 注入到 OpenCode 配置：
```typescript
const builtinAgents = createBuiltinAgents(...)

if (isSisyphusEnabled && builtinAgents.Sisyphus) {
  (config as { default_agent?: string }).default_agent = "Sisyphus";
  const agentConfig: Record<string, unknown> = { Sisyphus: builtinAgents.Sisyphus };
  ...
  config.agent = {
    ...agentConfig,
    ...Object.fromEntries(Object.entries(builtinAgents).filter(([k]) => k !== "Sisyphus")),
    ...userAgents,
    ...projectAgents,
    ...pluginAgents,
    ...filteredConfigAgents,
    ...
  };
} else {
  config.agent = {
    ...builtinAgents,
    ...userAgents,
    ...projectAgents,
    ...pluginAgents,
    ...configAgent,
  };
}
```

#### Agent 通信

**delegate_task 工具**：核心调度工具

```typescript
return tool({
  args: {
    description: ...,
    prompt: ...,
    category: ...,
    subagent_type: ...,
    run_in_background: ...,
    resume: ...,
    skills: ...
  },
  async execute(args: DelegateTaskArgs, toolContext) {
    if (args.run_in_background === undefined) { ... }
    if (args.category && args.subagent_type) { ... }
    if (!args.category && !args.subagent_type) { ... }
    ...
  }
})
```

**同步执行流程**：创建子会话 → 发送提示 → 轮询稳定输出

```typescript
const createResult = await client.session.create({
  body: { parentID: ctx.sessionID, title: `Task: ${args.description}` },
  ...
})

await client.session.prompt({
  path: { id: sessionID },
  body: {
    agent: agentToUse,
    system: systemContent,
    tools: { task: false, delegate_task: false, call_omo_agent: true },
    parts: [{ type: "text", text: args.prompt }],
    ...(categoryModel ? { model: categoryModel } : {}),
  },
})

const messagesResult = await client.session.messages({ path: { id: sessionID } })
```

**call_omo_agent 工具**：受限工具，仅用于 `explore`/`librarian`

```typescript
args: {
  description: ...,
  prompt: ...,
  subagent_type: tool.schema.enum(ALLOWED_AGENTS),
  run_in_background: tool.schema.boolean(),
  session_id: tool.schema.string().optional(),
},
...
if (args.run_in_background) { ... executeBackground(...) }
return await executeSync(...)
```

#### 并行执行

并发管理器：
```typescript
getConcurrencyLimit(model: string): number {
  const modelLimit = this.config?.modelConcurrency?.[model]
  ...
  const provider = model.split('/')[0]
  const providerLimit = this.config?.providerConcurrency?.[provider]
  ...
  const defaultLimit = this.config?.defaultConcurrency
  ...
  return 5
}
```

后台任务启动：
```typescript
async launch(input: LaunchInput): Promise<BackgroundTask> {
  const task: BackgroundTask = {
    id: `bg_${crypto.randomUUID().slice(0, 8)}`,
    status: "pending",
    ...
  }
  ...
  const key = this.getConcurrencyKeyFromInput(input)
  const queue = this.queuesByKey.get(key) ?? []
  queue.push({ task, input })
  this.queuesByKey.set(key, queue)
  this.processKey(key)
  return task
}

private async processKey(key: string): Promise<void> {
  ...
  while (queue && queue.length > 0) {
    const item = queue[0]
    await this.concurrencyManager.acquire(key)
    ...
    await this.startTask(item)
    queue.shift()
  }
}
```

后台任务执行：
```typescript
this.client.session.prompt({
  path: { id: sessionID },
  body: {
    agent: input.agent,
    ...(input.model ? { model: input.model } : {}),
    system: input.skillContent,
    tools: {
      ...getAgentToolRestrictions(input.agent),
      task: false,
      delegate_task: false,
      call_omo_agent: true,
    },
    parts: [{ type: "text", text: input.prompt }],
  },
})
```

### Specialized Agents 架构

#### Agent 元数据系统
```typescript
export interface AgentPromptMetadata {
  category: AgentCategory
  cost: AgentCost
  triggers: DelegationTrigger[]
  useWhen?: string[]
  avoidWhen?: string[]
  dedicatedSection?: string
  promptAlias?: string
  keyTrigger?: string
}
```

#### Sisyphus — 主编排器
```typescript
const prompt = availableAgents
  ? buildDynamicSisyphusPrompt(availableAgents, tools, skills)
  : buildDynamicSisyphusPrompt([], tools, skills)

const base = {
  description: "Sisyphus - Powerful AI orchestrator from OhMyOpenCode...",
  mode: "primary" as const,
  model,
  maxTokens: 64000,
  prompt,
  ...
}
```

动态提示构建基于可用的 agents/tools/skills。

#### Oracle — 只读顾问
```typescript
return {
  description: "Read-only consultation agent...",
  mode: "subagent" as const,
  model,
  temperature: 0.1,
  ...restrictions,
  prompt: ORACLE_SYSTEM_PROMPT,
}
```

- 严格推理指南
- 受限工具集
- 不执行写操作

#### Librarian — 外部文档专家
```typescript
return {
  description: "Specialized codebase understanding agent ... GitHub CLI, Context7, and Web Search.",
  mode: "subagent" as const,
  model,
  temperature: 0.1,
  ...restrictions,
  prompt: `# THE LIBRARIAN
  ...
  **CURRENT YEAR CHECK**: Before ANY search, verify the current date ...
  ...
`
}
```

- GitHub CLI + Context7 + Web Search
- 强制要求 GitHub permalinks
- 日期感知

#### Explore — 代码库搜索专家
```typescript
return {
  description: 'Contextual grep for codebases...',
  mode: "subagent" as const,
  model,
  temperature: 0.1,
  ...restrictions,
  prompt: `You are a codebase search specialist...
  ### 2. Parallel Execution (Required)
  Launch **3+ tools simultaneously** ...
  ...
  <results>
  <files> ... </files>
  <answer> ... </answer>
  <next_steps> ... </next_steps>
  </results>`
}
```

- 强制并行工具使用（3+ 同时执行）
- 结构化输出格式
- 专注于本地代码搜索

#### Orchestrator Sisyphus
```typescript
/**
 * Orchestrator Sisyphus - Master Orchestrator Agent
 * Orchestrates work via delegate_task() to complete ALL tasks in a todo list until fully done
 */
...
return `##### Option B: Use AGENT directly (for specialized experts)
...
| \`oracle\` | Read-only consultation. High-IQ debugging, architecture design |
| \`explore\` | Codebase exploration, pattern finding |
| \`librarian\` | External docs, GitHub examples, OSS reference |
...
`
```

- 定义代理决策矩阵
- 使用 `delegate_task()` 作为核心编排原语

### Hooks 系统

#### Hook 定义格式
```typescript
export type ClaudeHookEvent =
  | "PreToolUse"
  | "PostToolUse"
  | "UserPromptSubmit"
  | "Stop"
  | "PreCompact"

export interface HookMatcher {
  matcher: string
  hooks: HookCommand[]
}

export interface HookCommand {
  type: "command"
  command: string
}

export interface ClaudeHooksConfig {
  PreToolUse?: HookMatcher[]
  PostToolUse?: HookMatcher[]
  UserPromptSubmit?: HookMatcher[]
  Stop?: HookMatcher[]
  PreCompact?: HookMatcher[]
}
```

规范化：
```typescript
interface RawHookMatcher {
  matcher?: string
  pattern?: string
  hooks: HookCommand[]
}

function normalizeHookMatcher(raw: RawHookMatcher): HookMatcher {
  return {
    matcher: raw.matcher ?? raw.pattern ?? "*",
    hooks: raw.hooks,
  }
}

function mergeHooksConfig(
  base: ClaudeHooksConfig,
  override: ClaudeHooksConfig
): ClaudeHooksConfig {
  const result: ClaudeHooksConfig = { ...base }
  const eventTypes: (keyof ClaudeHooksConfig)[] = [
    "PreToolUse",
    "PostToolUse",
    "UserPromptSubmit",
    "Stop",
    "PreCompact",
  ]
  for (const eventType of eventTypes) {
    if (override[eventType]) {
      result[eventType] = [...(base[eventType] || []), ...override[eventType]]
    }
  }
  return result
}
```

配置加载：
```typescript
export function getClaudeSettingsPaths(customPath?: string): string[] {
  const paths = [
    join(claudeConfigDir, "settings.json"),
    join(process.cwd(), ".claude", "settings.json"),
    join(process.cwd(), ".claude", "settings.local.json"),
  ]
  ...
}

export async function loadClaudeHooksConfig(
  customSettingsPath?: string
): Promise<ClaudeHooksConfig | null> {
  const paths = getClaudeSettingsPaths(customPath)
  let mergedConfig: ClaudeHooksConfig = {}
  ...
  if (settings.hooks) {
    const normalizedHooks = normalizeHooksConfig(settings.hooks)
    mergedConfig = mergeHooksConfig(mergedConfig, normalizedHooks)
  }
  ...
}
```

#### 生命周期阶段

| 事件 | 时机 | 可阻塞 | 用例 |
|------|------|---------|------|
| PreToolUse | 工具执行前 | 是 | 验证/修改输入，注入上下文 |
| PostToolUse | 工具执行后 | 否 | 追加警告，截断输出 |
| UserPromptSubmit | 提示提交时 | 是 | 关键词检测，模式切换 |
| Stop | 会话空闲时 | 否 | 自动继续（todo-continuation, ralph-loop） |
| onSummarize | 压缩时 | 否 | 保留关键状态 |

Plugin 事件注册：
```typescript
return {
  ...
  "chat.message": async (input, output) => { ... },
  "experimental.chat.messages.transform": async (...) => { ... },
  event: async (input) => { ... },
  "tool.execute.before": async (input, output) => { ... },
  "tool.execute.after": async (input, output) => { ... },
};
```

#### Hook 拦截机制

**PreToolUse**：
```typescript
const matchers = findMatchingHooks(config, "PreToolUse", transformedToolName)
...
const result = await executeHookCommand(...)
if (result.exitCode === 2) {
  return { decision: "deny", ... }
}
if (result.exitCode === 1) {
  return { decision: "ask", ... }
}
...
if (output.hookSpecificOutput?.permissionDecision) {
  decision = output.hookSpecificOutput.permissionDecision
  modifiedInput = output.hookSpecificOutput.updatedInput
}
...
return { decision: decision ?? "allow", modifiedInput, ... }
```

修改工具参数：
```typescript
const result = await executePreToolUseHooks(preCtx, claudeConfig, extendedConfig)
...
if (result.modifiedInput) {
  Object.assign(output.args as Record<string, unknown>, result.modifiedInput)
}
```

**PostToolUse**：
```typescript
if (result.warnings && result.warnings.length > 0) {
  output.output = `${output.output}\n\n${result.warnings.join("\n")}`
}
if (result.message) {
  output.output = `${output.output}\n\n${result.message}`
}
```

**Stop**：
```typescript
if (event.type === "session.idle") {
  ...
  const stopResult = await executeStopHooks(stopCtx, claudeConfig, extendedConfig)
  ...
  } else if (stopResult.block && stopResult.injectPrompt) {
    ctx.client.session.prompt({
      body: { parts: [{ type: "text", text: stopResult.injectPrompt }] },
      ...
    })
  }
}
```

#### Hook 链顺序

**chat.message**:
```
keywordDetector → claudeCodeHooks → autoSlashCommand → startWork → ralphLoop
```

**tool.execute.before**:
```
claudeCodeHooks → nonInteractiveEnv → commentChecker → directoryAgentsInjector → directoryReadmeInjector → rulesInjector
```

**tool.execute.after**:
```
editErrorRecovery → delegateTaskRetry → commentChecker → toolOutputTruncator → emptyTaskResponseDetector → claudeCodeHooks
```

### 源码关键位置

| 组件 | 路径 |
|------|------|
| Schema 定义 | `src/config/schema.ts` |
| Agents 注册 | `src/agents/index.ts` |
| Agents 工具 | `src/agents/utils.ts` |
| Sisyphus | `src/agents/sisyphus.ts` |
| Oracle | `src/agents/oracle.ts` |
| Librarian | `src/agents/librarian.ts` |
| Explore | `src/agents/explore.ts` |
| Orchestrator Sisyphus | `src/agents/orchestrator-sisyphus.ts` |
| delegate_task | `src/tools/delegate-task/tools.ts` |
| call_omo_agent | `src/tools/call-omo-agent/tools.ts` |
| 并发管理 | `src/features/background-agent/concurrency.ts` |
| 后台管理 | `src/features/background-agent/manager.ts` |
| Hooks 类型 | `src/hooks/claude-code-hooks/types.ts` |
| Hooks 配置 | `src/hooks/claude-code-hooks/config.ts` |
| PreToolUse | `src/hooks/claude-code-hooks/pre-tool-use.ts` |
| Hooks 入口 | `src/hooks/claude-code-hooks/index.ts` |
| Plugin 主入口 | `src/index.ts` |
| Hooks 文档 | `src/hooks/AGENTS.md` |

---

## 外部参考

### OpenCode
- 官方文档：https://opencode.ai/docs/
- GitHub：https://github.com/opencode-ai/opencode
- MCP 协议：https://modelcontextprotocol.io/

### Oh My OpenCode
- 官方网站：https://ohmyopencode.com/
- 功能介绍：https://ohmyopencode.com/features/
- Agents：https://ohmyopencode.com/agents/
- Hooks：https://ohmyopencode.com/hooks/
- 安装指南：https://ohmyopencode.com/installation/
- GitHub：https://github.com/code-yeongyu/oh-my-opencode

---

## 总结

### OpenCode 核心能力
1. **MCP 集成**：完整支持 MCP 协议，工具发现、权限拦截、多传输类型
2. **插件架构**：OpenAPI 3.1 规范 + SDK 生成，易于扩展
3. **权限系统**：细粒度权限控制，支持 allow/ask/deny 三种模式
4. **多客户端支持**：TUI、桌面应用、IDE 扩展，通过本地服务器统一接口

### Oh My OpenCode 核心能力
1. **多 Agent 系统**：专业化 Agent（Sisyphus, Oracle, Librarian, Explore 等），明确的分工
2. **Agent 调度**：`delegate_task` 和 `call_omo_agent` 工具，支持同步/后台执行
3. **并行执行**：并发管理器，队列系统，可配置的并发限制
4. **Hooks 系统**：完整的事件拦截机制，生命周期钩子，配置驱动的链式调用
5. **动态提示**：基于可用 agents/tools/skills 构建动态提示，灵活适应场景

### 技术亮点
- **类型安全**：Go 严格类型检查，TypeScript Zod schema 验证
- **可扩展性**：插件系统、技能系统、配置覆盖
- **并发控制**：精细的并发管理，避免资源耗尽
- **权限保护**：多层权限检查，hook 拦截机制
- **文档驱动**：OpenAPI 规范，自动化 SDK 生成

---

*本文档由 AI Agent 生成，基于 OpenCode 和 Oh My OpenCode 的官方文档及源码分析。*
