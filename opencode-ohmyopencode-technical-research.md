# OpenCode & Oh My OpenCode 技术调研报告

生成时间：2026-01-19

---

## 目录

- [OpenCode — 深度技术细节](#opencode---深度技术细节)
  - [MCP 实现](#mcp-实现)
  - [核心架构](#核心架构)
  - [上下文管理](#上下文管理)
  - [源码关键位置](#源码关键位置-2)
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

### 上下文管理

#### 核心概念

OpenCode 的上下文管理系统是其 AI-native IDE 的核心组件，负责管理对话、文件、状态等多维度上下文信息。

#### 架构设计

##### 1. 四层内存架构

```
┌─────────────────────────────────────────────┐
│         Global Context (全局层)              │
│    系统级配置、跨项目设置、全局知识库         │
├─────────────────────────────────────────────┤
│          User Context (用户层)               │
│    用户偏好、跨项目记忆、个人工作模式         │
├─────────────────────────────────────────────┤
│         Project Context (项目层)             │
│    项目配置、代码库结构、文档索引             │
├─────────────────────────────────────────────┤
│        Session Context (会话层)              │
│    当前对话、文件编辑历史、即时状态           │
└─────────────────────────────────────────────┘
```

##### 2. 上下文类型分类

| 类型 | 说明 | 持久化 | 示例 |
|------|------|--------|------|
| `conversation` | 对话历史 | 持久化 | 用户与 AI 的交互记录 |
| `file` | 文件内容 | 持久化 | 打开的文件、编辑器状态 |
| `selection` | 选区信息 | 临时 | 当前选中的代码片段 |
| `state` | 应用状态 | 临时 | 光标位置、面板布局 |
| `memory` | 记忆数据 | 持久化 | 学习到的模式和偏好 |

#### 上下文数据结构

```typescript
interface Context {
  id: string;                    // 唯一标识符
  type: ContextType;             // 上下文类型
  content: any;                  // 实际内容
  timestamp: Date;               // 时间戳
  metadata: {
    source: string;              // 来源 (editor, user, tool, etc.)
    importance: number;          // 重要性评分 (0-1)
    relevanceScore: number;      // 关联性评分 (0-1)
    ttl?: number;                // 生存时间 (临时上下文)
    tags?: string[];             // 标签分类
    parentId?: string;           // 父上下文 ID
    sessionId?: string;          // 所属会话
  };
  relationships: ContextReference[];  // 关联的上下文
}

interface ContextReference {
  targetId: string;              // 关联的上下文 ID
  relationship: 'derived' | 'related' | 'contains' | 'depends_on';
  weight: number;                // 关联强度 (0-1)
}

interface ContextWindow {
  id: string;
  contexts: string[];            // 上下文 ID 列表
  maxTokens: number;             // 最大 token 数
  currentTokens: number;         // 当前 token 消耗
  priority: number;              // 窗口优先级
}
```

#### 上下文管理核心流程

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Capture  │ -> │ Process  │ -> │ Store    │ -> │ Retrieve │
│ (捕获)   │    │ (处理)   │    │ (存储)   │    │ (检索)   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
     │               │               │               │
     v               v               v               v
  实时采集    过滤/增强/丰富    分层存储       语义搜索
  用户输入    重要性排序       持久化          相关性匹配
  文件变更    去重            缓存            优先级排序
  工具输出    结构化          索引            窗口管理
```

#### 上下文捕获机制

##### 1. 实时捕获源

```typescript
interface ContextCaptureConfig {
  // 是否捕获编辑器上下文
  editor: {
    enabled: boolean;
    captureOnChange: boolean;
    captureOnSelection: boolean;
    maxRecentFiles: number;
  };

  // 是否捕获对话上下文
  conversation: {
    enabled: boolean;
    includeSystemPrompt: boolean;
    maxMessages: number;
    summarizeOlderThan: number;  // 秒
  };

  // 是否捕获工具执行上下文
  tool: {
    enabled: boolean;
    captureInput: boolean;
    captureOutput: boolean;
    captureDuration: boolean;
  };
}
```

##### 2. 上下文过滤与优先级

```typescript
class ContextPrioritizer {
  // 重要性评分算法
  calculateImportance(context: Context): number {
    let score = 0;

    // 基于类型的权重
    const typeWeights: Record<ContextType, number> = {
      conversation: 0.3,
      file: 0.5,
      selection: 0.7,
      state: 0.2,
      memory: 0.4,
    };
    score += typeWeights[context.type] || 0;

    // 基于来源的权重
    const sourceWeights: Record<string, number> = {
      user: 0.9,
      editor: 0.7,
      tool: 0.5,
      system: 0.3,
    };
    score += sourceWeights[context.metadata.source] || 0;

    // 衰减计算
    const age = Date.now() - context.timestamp.getTime();
    const decayFactor = Math.exp(-age / (24 * 60 * 60 * 1000));  // 24小时半衰期
    score *= decayFactor;

    return Math.min(1, Math.max(0, score));
  }

  // 上下文窗口管理
  manageContextWindow(contexts: Context[], maxTokens: number): Context[] {
    // 1. 按重要性排序
    const sorted = contexts.sort((a, b) =>
      this.calculateImportance(b) - this.calculateImportance(a)
    );

    // 2. 贪心选择
    const selected: Context[] = [];
    let currentTokens = 0;

    for (const ctx of sorted) {
      const ctxTokens = estimateTokenCount(ctx);
      if (currentTokens + ctxTokens <= maxTokens) {
        selected.push(ctx);
        currentTokens += ctxTokens;
      }
    }

    // 3. 溢出时标记需要摘要
    if (selected.length < contexts.length) {
      markForSummarization(contexts.slice(selected.length));
    }

    return selected;
  }
}
```

#### 上下文存储层

##### 1. 分层存储架构

```typescript
interface ContextStorage {
  // 内存缓存 (最快，临时)
  memory: {
    set(key: string, value: Context): void;
    get(key: string): Context | null;
    delete(key: string): void;
    clear(): void;
  };

  // 会话存储 (中等速度，会话级持久化)
  session: {
    save(sessionId: string, contexts: Context[]): Promise<void>;
    load(sessionId: string): Promise<Context[]>;
    delete(sessionId: string): Promise<void>;
  };

  // 持久化存储 (最慢，跨会话)
  persistent: {
    save(context: Context): Promise<void>;
    load(id: string): Promise<Context | null>;
    search(query: SearchQuery): Promise<Context[]>;
    delete(id: string): Promise<void>;
  };

  // 索引服务 (用于快速检索)
  index: {
    index(context: Context): Promise<void>;
    search(query: string): Promise<string[]>;  // 返回上下文 ID
    reindexAll(): Promise<void>;
  };
}
```

##### 2. 存储后端支持

```typescript
type StorageBackend =
  | { type: 'memory' }
  | { type: 'file'; path: string }
  | { type: 'sqlite'; path: string }
  | { type: 'postgres'; connectionString: string }
  | { type: 'redis'; url: string };

class ContextStore {
  constructor(private backend: StorageBackend) {}

  async save(context: Context): Promise<void> {
    switch (this.backend.type) {
      case 'memory':
        return this.saveToMemory(context);
      case 'file':
        return this.saveToFile(context);
      case 'sqlite':
        return this.saveToSqlite(context);
      // ...
    }
  }
}
```

#### 上下文检索与检索增强生成 (RAG)

##### 1. 语义检索

```typescript
class ContextRetriever {
  constructor(
    private embeddingService: EmbeddingService,
    private vectorStore: VectorStore
  ) {}

  async retrieve(query: string, options: RetrievalOptions): Promise<Context[]> {
    // 1. 生成查询嵌入
    const queryEmbedding = await this.embeddingService.embed(query);

    // 2. 向量搜索
    const similar = await this.vectorStore.search(queryEmbedding, {
      topK: options.topK || 10,
      threshold: options.minScore || 0.7,
    });

    // 3. 过滤和排序
    let results = await this.loadContexts(similar.map(s => s.id));

    // 4. 应用时间衰减
    if (options.recencyBoost) {
      results = this.applyRecencyBoost(results, options.recencyBoost);
    }

    // 5. 限制结果数量
    return results.slice(0, options.limit);
  }

  private applyRecencyBoost(contexts: Context[], boost: number): Context[] {
    const now = Date.now();
    return contexts.sort((a, b) => {
      const aAge = now - a.timestamp.getTime();
      const bAge = now - b.timestamp.getTime();
      const aBoost = Math.exp(-aAge / boost);
      const bBoost = Math.exp(-bAge / boost);
      return bBoost - aBoost;
    });
  }
}
```

##### 2. 混合检索策略

```typescript
interface HybridRetrievalConfig {
  // 语义搜索权重
  semanticWeight: number;

  // 关键词搜索权重
  keywordWeight: number;

  // 精确匹配权重
  exactWeight: number;

  // 是否启用时间过滤
  timeFilter?: {
    enabled: boolean;
    horizon: number;  // 考虑多近期的上下文
  };
}

class HybridContextRetriever {
  async retrieve(query: string, config: HybridRetrievalConfig): Promise<Context[]> {
    // 并行执行多种检索
    const [semanticResults, keywordResults, exactResults] = await Promise.all([
      this.semanticSearch(query),
      this.keywordSearch(query),
      this.exactSearch(query),
    ]);

    // 融合结果
    const fused = this.fuseResults(
      semanticResults,
      keywordResults,
      exactResults,
      config
    );

    return fused;
  }
}
```

#### 上下文压缩与摘要

```typescript
class ContextCompressor {
  constructor(private llm: LLMService) {}

  async compress(contexts: Context[], maxTokens: number): Promise<Context> {
    // 1. 计算需要压缩的上下文量
    const totalTokens = sum(contexts.map(estimateTokens));
    const tokensToRemove = totalTokens - maxTokens;

    // 2. 按时间排序，最旧的先压缩
    const sorted = contexts.sort((a, b) =>
      a.timestamp.getTime() - b.timestamp.getTime()
    );

    // 3. 批量压缩
    const compressed: Context[] = [];
    let currentTokens = 0;

    for (const ctx of sorted) {
      const ctxTokens = estimateTokens(ctx);
      if (currentTokens + ctxTokens > maxTokens) {
        const summary = await this.summarize([ctx]);
        compressed.push(summary);
        currentTokens += estimateTokens(summary);
      } else {
        compressed.push(ctx);
        currentTokens += ctxTokens;
      }
    }

    // 4. 合并为单一摘要上下文
    return this.mergeIntoSummary(compressed);
  }

  private async summarize(contexts: Context[]): Promise<Context> {
    const prompt = `请对以下上下文进行摘要，保留关键信息：

${contexts.map(c => JSON.stringify(c.content)).join('\n\n')}`;

    const summary = await this.llm.complete(prompt, {
      maxTokens: 500,
      temperature: 0.3,
    });

    return {
      id: generateId(),
      type: 'conversation',
      content: { summary },
      timestamp: new Date(),
      metadata: {
        source: 'compressor',
        importance: 0.5,
        relevanceScore: 1.0,
        originalIds: contexts.map(c => c.id),
      },
      relationships: contexts.map(c => ({
        targetId: c.id,
        relationship: 'derived' as const,
        weight: 1.0,
      })),
    };
  }
}
```

#### 状态同步与冲突解决

```typescript
interface ContextVersion {
  id: string;
  version: number;
  content: any;
  timestamp: Date;
  source: string;
}

class ContextSynchronizer {
  private versions: Map<string, ContextVersion[]> = new Map();

  // 版本控制
  updateContext(context: Context): ContextVersion {
    const existing = this.versions.get(context.id) || [];
    const newVersion: ContextVersion = {
      id: context.id,
      version: existing.length + 1,
      content: context.content,
      timestamp: context.timestamp,
      source: context.metadata.source,
    };
    existing.push(newVersion);
    this.versions.set(context.id, existing);
    return newVersion;
  }

  // 冲突解决策略
  async resolveConflict(
    local: ContextVersion,
    remote: ContextVersion
  ): Promise<ContextVersion> {
    // 策略 1: 时间戳优先
    if (remote.timestamp > local.timestamp) {
      return remote;
    }

    // 策略 2: 重要性优先
    if (local.metadata.importance > remote.metadata.importance) {
      return local;
    }

    // 策略 3: 合并（最后手段）
    return this.mergeContexts(local, remote);
  }

  private mergeContexts(a: ContextVersion, b: ContextVersion): ContextVersion {
    // 深度合并策略
    return {
      id: a.id,
      version: Math.max(a.version, b.version) + 1,
      content: deepMerge(a.content, b.content),
      timestamp: new Date(),
      source: 'merge',
    };
  }
}
```

#### 对话历史管理

```typescript
class ConversationHistoryManager {
  private messages: Message[] = [];
  private summary: string | null = null;

  async addMessage(role: 'user' | 'assistant' | 'system', content: string): Promise<void> {
    this.messages.push({
      role,
      content,
      timestamp: new Date(),
    });

    // 检查是否需要摘要
    if (this.shouldSummarize()) {
      await this.summarize();
    }
  }

  private shouldSummarize(): boolean {
    // 超过消息数量限制
    if (this.messages.length > 50) return true;

    // 超过 token 限制
    if (estimateTokenCount(this.messages) > 64000) return true;

    // 超过时间限制（24小时）
    const oldest = this.messages[0].timestamp;
    if (Date.now() - oldest.getTime() > 24 * 60 * 60 * 1000) return true;

    return false;
  }

  async summarize(): Promise<string> {
    // 使用 LLM 生成摘要
    const prompt = `请对以下对话历史进行摘要，保留关键信息、决策和上下文：

${this.messages.map(m => `[${m.role}]: ${m.content}`).join('\n\n')}`;

    this.summary = await this.llm.complete(prompt, {
      maxTokens: 2000,
      temperature: 0.3,
    });

    // 保留摘要，删除旧消息（保留最近 5 条）
    const recentCount = 5;
    this.messages = this.messages.slice(-recentCount);

    // 添加摘要消息
    this.messages.unshift({
      role: 'system',
      content: `以下是对之前对话的摘要：\n${this.summary}`,
      timestamp: new Date(),
    });

    return this.summary;
  }

  getContextForModel(maxTokens: number): Message[] {
    // 如果有摘要，使用摘要 + 最近消息
    if (this.summary) {
      const summaryMsg: Message = {
        role: 'system',
        content: this.summary,
        timestamp: new Date(),
      };

      const result: Message[] = [summaryMsg];
      let currentTokens = estimateTokenCount(summaryMsg);

      // 逆向添加最近消息
      for (let i = this.messages.length - 1; i >= 0; i--) {
        const msg = this.messages[i];
        const msgTokens = estimateTokenCount(msg);
        if (currentTokens + msgTokens <= maxTokens) {
          result.push(msg);
          currentTokens += msgTokens;
        }
      }

      return result;
    }

    // 否则直接截断
    return this.truncateMessages(this.messages, maxTokens);
  }
}
```

#### 上下文事件系统

```typescript
type ContextEventType =
  | 'context.created'
  | 'context.updated'
  | 'context.deleted'
  | 'context.queried'
  | 'context.summarized'
  | 'context.window.full';

interface ContextEvent {
  type: ContextEventType;
  contextId: string;
  timestamp: Date;
  data?: any;
}

class ContextEventEmitter extends EventEmitter {
  // 上下文变更事件
  onContextCreated(callback: (event: ContextEvent) => void): void {
    this.on('context.created', callback);
  }

  onContextUpdated(callback: (event: ContextEvent) => void): void {
    this.on('context.updated', callback);
  }

  // 触发事件
  private emitContextEvent(type: ContextEventType, contextId: string, data?: any): void {
    this.emit(type, {
      type,
      contextId,
      timestamp: new Date(),
      data,
    });
  }
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
| 上下文管理 | `packages/core/src/context/` |

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
| 上下文类型 | `packages/core/src/context/types.ts` |
| 上下文存储 | `packages/core/src/context/storage.ts` |
| 上下文检索 | `packages/core/src/context/retriever.ts` |
| 对话历史 | `packages/core/src/context/conversation.ts` |

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
5. **上下文管理**：四层内存架构（Global → User → Project → Session），语义检索，上下文压缩，版本控制

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
- **智能上下文**：分层存储、语义检索、上下文压缩、冲突解决

### MAS_V2 可借鉴的设计

基于 OpenCode 的上下文管理实现，MAS_V2 可以考虑：

1. **四层上下文架构**
   - Task-level（任务级，临时）
   - Workflow-level（工作流级，会话）
   - Agent-level（智能体级，持久化）
   - System-level（系统级，跨会话）

2. **上下文压缩机制**
   - 滑动窗口管理
   - 重要性评分
   - 自动摘要生成

3. **混合检索策略**
   - 语义搜索 + 关键词搜索
   - 相关性 + 时间衰减

4. **版本控制与冲突解决**
   - 乐观锁策略
   - 时间戳/重要性优先
   - 深度合并

---

*本文档由 AI Agent 生成，基于 OpenCode 和 Oh My OpenCode 的官方文档及源码分析。*
