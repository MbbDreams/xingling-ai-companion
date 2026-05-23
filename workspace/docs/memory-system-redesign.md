# 星灵 AI 伴侣 — 记忆系统重构设计文档

> 版本: v2.0  
> 日期: 2026-05-24  
> 参考方案: MemGPT/Letta、Zep/Graphiti、LangGraph、OpenAI Memory、星野(MiniMax)、Coze

---

## 一、问题诊断

### 1.1 现有系统核心问题

| # | 问题 | 严重度 | 位置 |
|---|------|--------|------|
| 1 | pgvector embedding 字段已建但完全未使用，检索仅靠 ILIKE 模糊匹配 | **致命** | memory_manager.py |
| 2 | 每条对话都无条件存储为 CONVERSATION_STYLE 记忆，记忆无限膨胀 | **致命** | memory_manager.py |
| 3 | 旧记忆压缩中删除代码被注释掉，记忆只增不减 | **严重** | memory_manager.py |
| 4 | PromptBuilder 完整系统未被集成，实际用的是硬编码简单模板 | **严重** | companion_agent.py |
| 5 | 记忆在 system prompt 和 build_llm_messages 中重复注入，token 浪费 | **严重** | companion_agent.py |
| 6 | get_conversation_history() 取的是最早 N 条而非最近 N 条（缺 offset） | **严重** | conversation_manager.py |
| 7 | summarize_conversation() 存在但主流程从未调用，长对话直接截断 | **严重** | conversation_manager.py |
| 8 | 亲密度/相识天数/关系类型等动态参数全部硬编码 | **中等** | companion_agent.py |
| 9 | recall_count / last_recalled_at / TIME_DECAY_DAYS 定义了但未使用 | **中等** | memory_manager.py |
| 10 | get_user_memories() 传入空字符串导致检索退化为无关键词过滤 | **中等** | companion_agent.py |

### 1.2 用户可感知的问题

1. **历史记录多时记忆质量差** — 噪音记忆淹没关键信息，AI 无法精准回忆
2. **Token 成本高** — 每次对话都塞入大量低价值历史
3. **长对话丢失上下文** — 超过 20 条消息后早期内容直接截断，无摘要补充
4. **AI 回复缺乏个性深度** — PromptBuilder 的关系适配、情绪响应、Few-shot 示例全部闲置

---

## 二、架构设计

### 2.1 整体架构 — 三层记忆 + 上下文工程

参考 MemGPT/Letta 的分层架构 + LangGraph 的 SummarizationMiddleware + 星野的五层体系，设计适合本项目的高效方案：

```
┌─────────────────────────────────────────────────────────────┐
│                    LLM 上下文窗口                            │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Layer 1: 核心记忆 Core Memory (常驻, ~500 tokens)   │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │   │
│  │  │ 角色设定      │ │ 用户画像摘要  │ │ 关系状态     │ │   │
│  │  │ (静态常驻)    │ │ (动态更新)    │ │ (动态更新)   │ │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Layer 2: 工作记忆 Working Memory (~1500 tokens)     │   │
│  │  ┌──────────────────┐ ┌──────────────────────────┐  │   │
│  │  │ 对话摘要          │ │ 最近 K 轮原始对话         │  │   │
│  │  │ (早期对话压缩)    │ │ (滑动窗口, K=6)          │  │   │
│  │  └──────────────────┘ └──────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Layer 3: 检索记忆 Retrieved Memory (~500 tokens)   │   │
│  │  ┌──────────────────────────────────────────────┐   │   │
│  │  │ 向量语义检索的相关长期记忆 (Top 3-5 条)       │   │   │
│  │  └──────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  当前用户消息                                        │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Token 预算分配

| 区域 | Token 预算 | 内容 |
|------|-----------|------|
| System Prompt (核心记忆) | ~500 | 角色设定 + 用户画像 + 关系状态 |
| 对话摘要 | ~300 | 早期对话的压缩摘要 |
| 最近对话 (滑动窗口) | ~1200 | 最近 6 轮原始对话 (~200 tokens/轮) |
| 检索记忆 | ~400 | 向量检索的 3-5 条相关记忆 |
| 当前消息 | ~200 | 用户当前输入 |
| AI 回复预留 | ~800 | AI 生成回复的空间 |
| **总计** | **~3400** | 适配 DeepSeek 的 8K-32K 上下文窗口 |

### 2.3 记忆生命周期

```
对话发生
  │
  ├─ Step 1: 实时写入
  │   └─ 原始消息存入 messages 表（已有）
  │
  ├─ Step 2: 异步记忆提取（后台任务）
  │   ├─ 用轻量模型从对话中提取结构化记忆
  │   ├─ 去重：与已有记忆计算相似度，相似度 > 0.85 则合并更新
  │   ├─ 生成 embedding 向量
  │   └─ 写入 memories 表（category/importance/embedding）
  │
  ├─ Step 3: 对话摘要触发（条件触发）
  │   ├─ 触发条件：当前会话消息数 > 12 条
  │   ├─ 对前 N 条消息生成摘要，存入 conversation_summaries 表
  │   └─ 后续构建上下文时用摘要替代原始消息
  │
  ├─ Step 4: 用户画像更新（条件触发）
  │   ├─ 触发条件：每 10 轮对话 或 检测到新的关键信息
  │   ├─ 汇总所有 basic_info/preference 类记忆
  │   └─ 生成紧凑的用户画像文本，存入 core_memory 表
  │
  └─ Step 5: 记忆清理（定时任务）
      ├─ 每日清理：删除 recall_count=0 且超过 90 天的低重要性记忆
      ├─ 记忆合并：相似度 > 0.9 的记忆合并为一条
      └─ 重要性衰减：超过 60 天的记忆 importance *= 0.8
```

---

## 三、数据库设计变更

### 3.1 新增表

#### 3.1.1 `core_memory` — 核心记忆表（常驻上下文的结构化记忆）

```sql
CREATE TABLE core_memory (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT REFERENCES users(id) ON DELETE CASCADE,
    companion_id    BIGINT REFERENCES companions(id) ON DELETE CASCADE,
    
    -- 核心记忆分区
    persona_block   TEXT DEFAULT '',    -- 角色设定（静态，初始化时写入）
    human_block     TEXT DEFAULT '',    -- 用户画像摘要（动态，定期更新）
    relationship_block TEXT DEFAULT '', -- 关系状态摘要（动态，定期更新）
    
    -- 元数据
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, companion_id)
);

CREATE INDEX idx_core_memory_user ON core_memory(user_id);
```

**设计说明**：
- 参考 Letta 的 Core Memory 概念，但简化为三个文本块
- `persona_block`：角色设定，几乎不变，只在初始化时写入一次
- `human_block`：用户画像摘要，由后台任务定期从 memories 表汇总生成
- `relationship_block`：关系状态（亲密度、相识天数、关系类型、最近互动摘要）
- 三个块合计控制在 ~500 tokens 以内

#### 3.1.2 `conversation_summaries` — 对话摘要表

```sql
CREATE TABLE conversation_summaries (
    id              BIGSERIAL PRIMARY KEY,
    conversation_id BIGINT REFERENCES conversations(id) ON DELETE CASCADE,
    user_id         BIGINT REFERENCES users(id) ON DELETE CASCADE,
    
    -- 摘要内容
    summary         TEXT NOT NULL,       -- 摘要文本
    message_range   JSONB DEFAULT '{}', -- {"start_id": 1, "end_id": 15, "count": 15}
    
    -- 元数据
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active       BOOLEAN DEFAULT TRUE -- 是否为当前有效摘要
);

CREATE INDEX idx_conv_summaries_conv ON conversation_summaries(conversation_id);
CREATE INDEX idx_conv_summaries_user ON conversation_summaries(user_id);
```

**设计说明**：
- 每个会话维护一个活跃摘要（is_active=True）
- 当消息数超过阈值时，对早期消息生成摘要，后续用摘要替代原始消息
- `message_range` 记录摘要覆盖的消息范围，用于增量更新

### 3.2 修改表

#### 3.2.1 `memories` 表 — 增加字段

```sql
-- 新增字段
ALTER TABLE memories ADD COLUMN memory_type VARCHAR(32) DEFAULT 'general';
ALTER TABLE memories ADD COLUMN source VARCHAR(32) DEFAULT 'user_told';
ALTER TABLE memories ADD COLUMN is_merged BOOLEAN DEFAULT FALSE;
ALTER TABLE memories ADD COLUMN merged_from_ids JSONB DEFAULT '[]';
ALTER TABLE memories ADD COLUMN expires_at TIMESTAMP WITH TIME ZONE;

-- 新增索引
CREATE INDEX idx_memories_type ON memories(user_id, memory_type);
CREATE INDEX idx_memories_importance ON memories(user_id, importance DESC);
CREATE INDEX idx_memories_expires ON memories(expires_at) WHERE expires_at IS NOT NULL;
```

**字段说明**：
- `memory_type`：记忆分类（basic_info/preference/event/emotion/hobby/goal 等），对应 MemoryType 枚举
- `source`：记忆来源（user_told 用户主动告知 / ai_inferred AI 推断）
- `is_merged`：是否为合并后的记忆
- `merged_from_ids`：被合并的原始记忆 ID 列表
- `expires_at`：过期时间（用于定时清理）

### 3.3 完整 ER 关系图

```
users (1) ──→ (N) companions
   │                │
   │                ├──→ (N) conversations ──→ (N) messages
   │                │         │
   │                │         └──→ (1) conversation_summaries
   │                │
   ├──→ (1) core_memory (per user+companion)
   │
   └──→ (N) memories
              │
              └──→ embedding (Vector 1536, pgvector)
```

---

## 四、模块设计

### 4.1 模块架构总览

```
backend/app/agent/
├── __init__.py
├── companion_agent.py          # [重构] 核心对话引擎
├── memory/
│   ├── __init__.py
│   ├── core_memory.py          # [新建] 核心记忆管理（常驻上下文）
│   ├── working_memory.py       # [新建] 工作记忆管理（对话历史+摘要）
│   ├── long_term_memory.py     # [新建] 长期记忆管理（向量检索）
│   ├── memory_extractor.py     # [新建] 记忆提取器（从对话提取结构化记忆）
│   ├── memory_maintenance.py   # [新建] 记忆维护（清理/合并/衰减）
│   └── embedder.py             # [新建] 向量化服务
├── context_builder.py          # [新建] 上下文组装器（Token预算控制）
├── prompts.py                  # [保留] 提示词系统（需集成）
├── models.py                   # [保留] Pydantic 模型
└── conversation_manager.py     # [重构] 对话管理（集成摘要）
```

### 4.2 各模块详细设计

#### 4.2.1 `embedder.py` — 向量化服务

**职责**：统一管理文本向量化，支持多种 Embedding 模型

```python
class Embedder:
    """向量化服务"""
    
    def __init__(self, api_key: str, base_url: str = None, model: str = "text-embedding-3-small"):
        """
        初始化 Embedding 客户端
        - 默认使用 OpenAI text-embedding-3-small (1536维)
        - 支持 DeepSeek 等兼容 API（但 DeepSeek 目前不提供 embedding，需用 OpenAI）
        - 降级方案：如果 embedding API 不可用，使用关键词匹配
        """
    
    async def embed_text(self, text: str) -> list[float]:
        """生成文本的向量表示"""
    
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量生成向量（提高效率）"""
    
    async def cosine_similarity(self, vec_a: list[float], vec_b: list[float]) -> float:
        """计算两个向量的余弦相似度"""
```

**关键设计决策**：
- DeepSeek 不提供 embedding API，需要单独配置一个 OpenAI API key 用于 embedding（或使用开源模型如 BAAI/bge-m3）
- 提供降级方案：embedding API 不可用时回退到关键词匹配（保持现有 ILIKE 逻辑作为 fallback）

#### 4.2.2 `core_memory.py` — 核心记忆管理

**职责**：管理常驻上下文的结构化记忆块

```python
class CoreMemoryManager:
    """核心记忆管理器 — 管理常驻上下文的结构化记忆"""
    
    async def initialize(self, user_id: int, companion_id: int) -> None:
        """
        初始化核心记忆（首次使用时调用）
        - 写入 persona_block（角色设定，从 PromptBuilder 获取）
        - 初始化空的 human_block 和 relationship_block
        """
    
    async def get_core_memory(self, user_id: int, companion_id: int) -> CoreMemory:
        """获取核心记忆三个块"""
    
    async def update_human_block(self, user_id: int, companion_id: int) -> str:
        """
        更新用户画像摘要
        - 从 memories 表汇总 basic_info/preference 类记忆
        - 用 LLM 生成紧凑摘要（~150 tokens）
        - 更新 core_memory.human_block
        """
    
    async def update_relationship_block(self, user_id: int, companion_id: int) -> str:
        """
        更新关系状态摘要
        - 从 Companion 表读取亲密度、等级
        - 计算相识天数
        - 统计最近互动频率
        - 生成关系状态文本（~100 tokens）
        """
    
    def build_core_prompt(self, core_memory: CoreMemory) -> str:
        """
        组装核心记忆为 system prompt 的一部分
        格式：
        ## 关于用户
        {human_block}
        
        ## 我们的关系
        {relationship_block}
        """
```

#### 4.2.3 `working_memory.py` — 工作记忆管理

**职责**：管理当前对话的短期上下文（滑动窗口 + 摘要）

```python
class WorkingMemoryManager:
    """工作记忆管理器 — 管理当前对话的短期上下文"""
    
    SUMMARY_THRESHOLD = 12      # 消息数超过此值时触发摘要
    KEEP_RECENT_MESSAGES = 6    # 滑动窗口保留最近 N 轮
    MAX_SUMMARY_TOKENS = 300    # 摘要最大 token 数
    
    async def get_context_messages(
        self, 
        conversation_id: int, 
        user_message: str
    ) -> list[dict]:
        """
        获取工作记忆上下文
        
        策略（参考 LangGraph SummarizationMiddleware）：
        1. 检查是否有活跃摘要 → 有则作为上下文开头
        2. 获取最近 KEEP_RECENT_MESSAGES 条消息 → 作为上下文尾部
        3. 拼接为完整的消息列表
        
        示例输出：
        [
            {"role": "system", "content": "之前的对话摘要：用户今天加班很累..."},
            {"role": "user", "content": "最近5轮的原始消息1"},
            {"role": "assistant", "content": "最近5轮的原始回复1"},
            ...
        ]
        """
    
    async def maybe_summarize(self, conversation_id: int, user_id: int) -> bool:
        """
        检查是否需要生成摘要，需要则生成
        
        触发条件：当前会话消息数 > SUMMARY_THRESHOLD 且无活跃摘要
        
        摘要内容包含：
        - 主要讨论的话题
        - 用户的情绪状态
        - 关键信息点（事实、偏好、事件）
        - 未完成的话题（如有）
        """
    
    async def get_or_create_summary(
        self, 
        conversation_id: int, 
        user_id: int
    ) -> str | None:
        """获取当前活跃摘要，不存在则返回 None"""
```

#### 4.2.4 `long_term_memory.py` — 长期记忆管理

**职责**：管理跨会话的长期记忆，基于向量语义检索

```python
class LongTermMemoryManager:
    """长期记忆管理器 — 跨会话的持久化记忆，向量语义检索"""
    
    MAX_RETRIEVE = 5             # 最大检索条数
    MIN_SIMILARITY = 0.6        # 最低相似度阈值
    TIME_DECAY_DAYS = 60        # 时间衰减天数
    RECENT_BOOST_DAYS = 7       # 最近记忆加权天数
    
    async def store_memory(
        self,
        user_id: int,
        companion_id: int,
        content: str,
        memory_type: str,
        importance: float,
        source: str = "user_told",
        source_message_id: int = None,
        embedding: list[float] = None,
    ) -> int:
        """
        存储一条记忆
        - 生成 embedding 向量
        - 写入 memories 表
        - 返回记忆 ID
        """
    
    async def retrieve_memories(
        self,
        user_id: int,
        query: str,
        limit: int = 5,
        exclude_types: list[str] = None,
    ) -> list[MemoryEntry]:
        """
        语义检索相关记忆
        
        检索流程：
        1. 将 query 生成 embedding 向量
        2. 在 memories 表中做向量相似度搜索（pgvector）
        3. 混合排序 = 语义相似度 * 0.6 + 重要性 * 0.2 + 时间新鲜度 * 0.2
        4. 过滤低于 MIN_SIMILARITY 的结果
        5. 返回 top limit 条
        
        时间新鲜度计算：
        - 7 天内: 1.0
        - 7-30 天: 0.8
        - 30-60 天: 0.5
        - 60+ 天: 0.3
        """
    
    async def deduplicate_and_merge(
        self,
        user_id: int,
        new_content: str,
        new_embedding: list[float],
        threshold: float = 0.85,
    ) -> bool:
        """
        去重检查：新记忆与已有记忆的相似度
        
        如果相似度 > threshold：
        - 合并内容（保留更详细的版本）
        - 更新 importance = max(old, new)
        - 标记 is_merged=True, merged_from_ids=[old_id]
        - 删除旧记忆
        - 返回 True（已合并）
        
        否则返回 False（需要新建）
        """
```

**向量检索 SQL 示例**（pgvector）：
```sql
SELECT m.*, 
       1 - (m.embedding <=> :query_embedding) AS similarity
FROM memories m
WHERE m.user_id = :user_id
  AND m.embedding IS NOT NULL
  AND (m.expires_at IS NULL OR m.expires_at > NOW())
ORDER BY m.embedding <=> :query_embedding
LIMIT :limit * 2
```

#### 4.2.5 `memory_extractor.py` — 记忆提取器

**职责**：从对话中智能提取结构化记忆

```python
class MemoryExtractor:
    """记忆提取器 — 从对话中提取结构化记忆"""
    
    # 提取触发关键词（参考星野的动态触发规则）
    EXTRACTION_KEYWORDS = {
        'basic_info': ['我叫', '我是', '我的名字', '我今年', '我住', '我在'],
        'preference': ['喜欢', '讨厌', '不爱', '最爱', '偏好', '习惯'],
        'family': ['爸爸', '妈妈', '哥哥', '姐姐', '弟弟', '妹妹', '家里', '家人'],
        'pet': ['猫', '狗', '宠物', '养了'],
        'hobby': ['爱好', '平时', '周末', '运动', '游戏', '音乐', '电影', '看书'],
        'emotion': ['开心', '难过', '生气', '焦虑', '压力', '累', '烦', '郁闷'],
        'event': ['昨天', '上周', '前几天', '最近', '发生', '去了', '参加了'],
        'goal': ['计划', '打算', '目标', '想', '准备', '要'],
        'relationship': ['男朋友', '女朋友', '老公', '老婆', '对象', '暗恋'],
    }
    
    async def extract_from_conversation(
        self,
        user_message: str,
        ai_response: str,
        user_id: int,
    ) -> list[MemoryEntry]:
        """
        从一轮对话中提取记忆
        
        流程：
        1. 快速判断：检查是否包含提取关键词 → 不包含则跳过（节省 LLM 调用）
        2. LLM 提取：调用轻量模型，使用 ProactivePromptBuilder.build_memory_extraction_prompt()
        3. 解析结果：JSON 数组 → MemoryEntry 列表
        4. 去重检查：与已有记忆比较，决定新建或合并
        5. 返回需要存储的记忆列表
        """
    
    async def should_extract(self, user_message: str) -> bool:
        """
        快速判断是否需要提取记忆（关键词预过滤）
        避免对"嗯"、"好的"等无信息量消息调用 LLM
        """
```

**关键优化**：
- **关键词预过滤**：先检查是否包含有意义的关键词，不包含则直接跳过 LLM 调用
- **使用轻量模型**：记忆提取用 deepseek-chat 而非更贵的模型
- **去重合并**：新记忆与已有记忆相似度 > 0.85 时合并，避免重复存储

#### 4.2.6 `memory_maintenance.py` — 记忆维护

**职责**：定期清理、合并、衰减记忆

```python
class MemoryMaintenance:
    """记忆维护器 — 定期清理、合并、衰减"""
    
    async def daily_cleanup(self) -> dict:
        """
        每日清理任务（建议通过 APScheduler 或 FastAPI 后台任务调用）
        
        1. 清理过期记忆：
           - recall_count=0 且 created_at > 90天 且 importance < 0.3 → 删除
           - expires_at 已过期 → 删除
        
        2. 重要性衰减：
           - created_at > 60天 的记忆 importance *= 0.8
           - 但 basic_info 类型的记忆不衰减（用户基本信息不会过时）
        
        3. 相似记忆合并：
           - 对同一用户的记忆两两计算相似度
           - 相似度 > 0.9 的合并为一条
           - 保留 importance 更高的版本
        
        返回清理统计：{"deleted": N, "decayed": N, "merged": N}
        """
    
    async def update_core_memories(self) -> dict:
        """
        更新所有用户的核心记忆（用户画像 + 关系状态）
        建议每日执行一次
        """
```

#### 4.2.7 `context_builder.py` — 上下文组装器

**职责**：按 Token 预算组装完整的 LLM 输入

```python
class ContextBuilder:
    """上下文组装器 — 按 Token 预算组装 LLM 输入"""
    
    # Token 预算（按 DeepSeek 的 token 计算方式，约 1.5 汉字/token）
    BUDGET = {
        'system_prompt': 500,     # 角色设定 + 核心记忆
        'summary': 300,            # 对话摘要
        'recent_messages': 1200,   # 最近对话
        'retrieved_memories': 400, # 检索记忆
    }
    
    def __init__(
        self,
        core_memory_mgr: CoreMemoryManager,
        working_memory_mgr: WorkingMemoryManager,
        long_term_memory_mgr: LongTermMemoryManager,
    ):
        pass
    
    async def build_context(
        self,
        user_id: int,
        companion_id: int,
        conversation_id: int,
        user_message: str,
    ) -> list[dict]:
        """
        组装完整的 LLM 消息列表
        
        步骤：
        1. 获取核心记忆 → 构建 system prompt
        2. 获取工作记忆 → 摘要 + 最近对话
        3. 获取检索记忆 → 向量检索相关记忆
        4. 按 Token 预算裁剪
        5. 组装为 [system, ...messages, user_message]
        
        返回格式：
        [
            {"role": "system", "content": "角色设定\n\n## 关于用户\n...\n\n## 我们的关系\n..."},
            {"role": "system", "content": "之前的对话摘要：..."},
            {"role": "user", "content": "最近对话1"},
            {"role": "assistant", "content": "最近回复1"},
            ...
            {"role": "system", "content": "## 相关记忆\n- 用户喜欢猫\n- 用户上周加班很累"},
            {"role": "user", "content": "当前用户消息"},
        ]
        """
```

### 4.3 重构 `companion_agent.py`

**核心变更**：

```python
class CompanionAgent:
    """AI 伴侣核心引擎 — 重构版"""
    
    def __init__(self, db_session, api_key, model, base_url):
        # 初始化各管理器
        self.embedder = Embedder(api_key=api_key, base_url=base_url)
        self.core_memory_mgr = CoreMemoryManager(db_session, self.embedder)
        self.working_memory_mgr = WorkingMemoryManager(db_session)
        self.long_term_memory_mgr = LongTermMemoryManager(db_session, self.embedder)
        self.memory_extractor = MemoryExtractor(llm=self.llm)
        self.context_builder = ContextBuilder(
            self.core_memory_mgr,
            self.working_memory_mgr,
            self.long_term_memory_mgr,
        )
    
    async def chat(self, user_id: int, message: str, conversation_id: int = None) -> ChatResult:
        """
        重构后的对话流程：
        
        1. 获取/创建会话
        2. 获取 companion_id
        3. 确保核心记忆已初始化
        4. 通过 ContextBuilder 组装完整上下文
           ├─ 核心记忆 (CoreMemoryManager)
           ├─ 工作记忆 (WorkingMemoryManager)
           └─ 检索记忆 (LongTermMemoryManager)
        5. 调用 LLM 生成回复
        6. 存储消息到 messages 表
        7. 异步触发记忆提取（不阻塞响应）
        8. 检查是否需要生成对话摘要
        9. 返回结果
        
        与旧版对比：
        - 旧版：手动拼接 system prompt + 历史消息 + 记忆，记忆重复注入
        - 新版：ContextBuilder 统一管理，Token 预算控制，无重复
        """
    
    async def _async_memory_tasks(self, user_id: int, companion_id: int, 
                                    user_message: str, ai_response: str):
        """
        异步记忆任务（不阻塞用户响应）
        
        1. 记忆提取 + 存储
        2. 检查是否需要更新核心记忆（每 10 轮检查一次）
        3. 检查是否需要生成对话摘要
        """
```

### 4.4 集成 `PromptBuilder`

**变更**：`companion_agent.py` 中的 `_build_system_prompt()` 改为使用 `PromptBuilder.build_system_prompt()`

```python
# 旧版（硬编码）
def _build_system_prompt(self, user_summary, memories):
    prompt = COMPANION_SYSTEM_PROMPT.format(...)
    return prompt

# 新版（使用 PromptBuilder）
async def _build_system_prompt(self, user_id, companion_id):
    # 从数据库读取关系状态
    companion = await self._get_companion(user_id, companion_id)
    core_memory = await self.core_memory_mgr.get_core_memory(user_id, companion_id)
    
    # 使用 PromptBuilder 构建完整 system prompt
    return PromptBuilder.build_system_prompt(
        user_name=companion.user.nickname,
        relationship_type=RelationshipType.PARTNER,
        relationship_level=companion.intimacy // 100,
        intimacy=companion.intimacy,
        current_emotion=companion.mood,
        memories=core_memory.human_block,  # 用户画像摘要
        conversation_turns=0,
    )
```

---

## 五、记忆提取 Prompt 设计

### 5.1 记忆提取 Prompt（使用 ProactivePromptBuilder 中已有的版本）

```python
MEMORY_EXTRACTION_PROMPT = """
你是一个记忆提取助手。请从以下对话中提取关于用户的关键信息。

## 提取规则
1. 只提取关于**用户**的信息，不提取关于 AI 的信息
2. 每条记忆应该是独立的、具体的事实或偏好
3. 忽略寒暄、确认等无信息量内容（如"好的"、"嗯嗯"）
4. 重要性评分 1-10：基本信息 8-10，偏好 5-7，闲聊 1-3
5. 如果没有值得记忆的信息，返回空数组

## 记忆类型
- basic_info: 姓名、年龄、职业、住址等基本信息
- preference: 喜欢/讨厌的事物、习惯
- family: 家庭成员信息
- pet: 宠物信息
- hobby: 兴趣爱好
- emotion: 情绪状态（当前）
- event: 重要事件或经历
- goal: 计划或目标
- relationship: 人际关系信息

## 对话内容
用户: {user_message}
AI: {ai_response}

## 输出格式（JSON 数组）
[
  {{"content": "用户叫张三", "type": "basic_info", "importance": 9}},
  {{"content": "用户喜欢猫", "type": "preference", "importance": 6}}
]

如果没有值得记忆的信息，返回: []
"""
```

### 5.2 对话摘要 Prompt

```python
CONVERSATION_SUMMARY_PROMPT = """
请将以下对话内容压缩为简洁的摘要，保留关键信息。

## 要求
1. 保留：主要话题、用户情绪、关键事实、用户偏好
2. 省略：寒暄、重复确认、过渡语句
3. 使用第三人称描述用户
4. 控制在 100 字以内

## 对话内容
{conversation_text}

## 输出格式
摘要文本（不超过100字）
"""
```

### 5.3 用户画像更新 Prompt

```python
USER_PROFILE_UPDATE_PROMPT = """
根据以下关于用户的所有已知信息，生成一段简洁的用户画像描述。

## 要求
1. 包含：基本信息、性格特点、兴趣爱好、当前状态
2. 省略：过于细节的日常琐事
3. 使用第三人称
4. 控制在 80 字以内
5. 如果某些类别没有信息，不要编造

## 已知信息
{memories_text}

## 输出格式
用户画像描述（不超过80字）
"""
```

---

## 六、API 变更

### 6.1 新增 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/memory/core` | 获取当前用户的核心记忆 |
| PUT | `/memory/core` | 手动更新核心记忆（调试用） |
| GET | `/memory/stats` | 获取记忆统计（总数、分类分布、存储占用） |
| POST | `/memory/maintenance/cleanup` | 手动触发记忆清理（管理用） |

### 6.2 修改 API

| 方法 | 路径 | 变更 |
|------|------|------|
| GET | `/chat/history` | 新增 `include_summary` 参数，返回对话摘要 |
| POST | `/chat/send` | 响应中新增 `memories_used` 字段（使用的记忆列表） |

---

## 七、配置变更

### 7.1 `.env` 新增配置

```env
# Embedding 配置（用于记忆向量化）
EMBEDDING_API_KEY=sk-xxx           # OpenAI API key（用于 embedding）
EMBEDDING_BASE_URL=                # 留空使用 OpenAI 默认
EMBEDDING_MODEL=text-embedding-3-small  # embedding 模型

# 记忆系统配置
MEMORY_SUMMARY_THRESHOLD=12        # 触发摘要的消息数阈值
MEMORY_KEEP_RECENT=6               # 滑动窗口保留消息数
MEMORY_MAX_RETRIEVE=5              # 最大检索记忆条数
MEMORY_CLEANUP_INTERVAL=86400      # 记忆清理间隔（秒），默认每天
```

### 7.2 `config.py` 新增字段

```python
class Settings(BaseSettings):
    # ... 现有字段 ...
    
    # Embedding 配置
    embedding_api_key: str = ""
    embedding_base_url: str = ""
    embedding_model: str = "text-embedding-3-small"
    
    # 记忆系统配置
    memory_summary_threshold: int = 12
    memory_keep_recent: int = 6
    memory_max_retrieve: int = 5
    memory_cleanup_interval: int = 86400
```

---

## 八、实施计划

### Phase 1: 基础设施（优先级最高）

| # | 任务 | 文件 | 说明 |
|---|------|------|------|
| 1.1 | 新建 embedder.py | agent/memory/embedder.py | 向量化服务，支持 OpenAI embedding + 降级 |
| 1.2 | 数据库迁移 | migrations/ | 新建 core_memory、conversation_summaries 表，修改 memories 表 |
| 1.3 | 更新 config.py | core/config.py | 新增 embedding 和记忆系统配置 |

### Phase 2: 核心模块（优先级高）

| # | 任务 | 文件 | 说明 |
|---|------|------|------|
| 2.1 | 新建 core_memory.py | agent/memory/core_memory.py | 核心记忆管理（初始化/读取/更新） |
| 2.2 | 新建 working_memory.py | agent/memory/working_memory.py | 工作记忆管理（滑动窗口+摘要） |
| 2.3 | 新建 long_term_memory.py | agent/memory/long_term_memory.py | 长期记忆管理（向量检索+去重合并） |
| 2.4 | 新建 memory_extractor.py | agent/memory/memory_extractor.py | 记忆提取器（关键词预过滤+LLM提取） |
| 2.5 | 新建 context_builder.py | agent/context_builder.py | 上下文组装器（Token预算控制） |

### Phase 3: 集成重构（优先级高）

| # | 任务 | 文件 | 说明 |
|---|------|------|------|
| 3.1 | 重构 companion_agent.py | agent/companion_agent.py | 使用新的分层记忆架构 |
| 3.2 | 集成 PromptBuilder | agent/companion_agent.py | 替换硬编码 prompt |
| 3.3 | 重构 conversation_manager.py | agent/conversation_manager.py | 集成摘要功能，修复 offset bug |
| 3.4 | 清理旧代码 | agent/memory_manager.py | 删除或标记废弃 |

### Phase 4: 维护与优化（优先级中）

| # | 任务 | 文件 | 说明 |
|---|------|------|------|
| 4.1 | 新建 memory_maintenance.py | agent/memory/memory_maintenance.py | 定时清理/合并/衰减 |
| 4.2 | 注册后台任务 | main.py | FastAPI 后台任务注册 |
| 4.3 | 新增管理 API | api/routes/chat.py | 记忆统计/清理接口 |

### Phase 5: 测试验证

| # | 任务 | 说明 |
|---|------|------|
| 5.1 | 单元测试 | 各模块独立测试 |
| 5.2 | 集成测试 | 完整对话流程测试 |
| 5.3 | 性能测试 | Token 消耗对比（重构前后） |
| 5.4 | 记忆质量测试 | 长对话后的记忆召回准确率 |

---

## 九、预期效果

### 9.1 Token 消耗对比

| 场景 | 重构前 | 重构后 | 优化比 |
|------|--------|--------|--------|
| 10 轮对话 | ~3000 tokens | ~2500 tokens | -17% |
| 50 轮对话 | ~6000 tokens (截断) | ~3000 tokens | -50% |
| 100 轮对话 | ~6000 tokens (丢失早期) | ~3200 tokens (摘要保留) | -47% |

### 9.2 记忆质量对比

| 维度 | 重构前 | 重构后 |
|------|--------|--------|
| 检索方式 | ILIKE 关键词模糊匹配 | pgvector 向量语义检索 |
| 记忆去重 | 无 | 相似度 > 0.85 自动合并 |
| 记忆清理 | 无（只增不减） | 定时清理 + 重要性衰减 |
| 上下文连续性 | 超过 20 条直接截断 | 摘要 + 滑动窗口混合 |
| 个性化深度 | 硬编码 prompt | PromptBuilder 动态适配 |

### 9.3 成本优化

- **LLM 调用减少**：关键词预过滤避免对无意义消息调用 LLM 提取记忆
- **Token 节省**：摘要替代原始消息，长期对话 Token 消耗降低 50%
- **模型分级**：记忆提取用 deepseek-chat，核心推理可选用更强模型
