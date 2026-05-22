# 星灵（XingLing）AI 伴侣 - 完整规划文档

## 一、项目现状分析

### 1.1 当前已实现功能

#### 前端 (Flutter)
| 模块 | 状态 | 说明 |
|------|------|------|
| 聊天系统 | ✅ | 文本聊天、消息气泡、流式输出模拟 |
| 首页 | ✅ | 5 Tab 导航、星空背景动画 |
| 记忆系统 | ✅ | CRUD、分类筛选、缓存优化 |
| 日记系统 | ✅ | 日历视图、历史日期、标签、缓存 |
| 发现页面 | ✅ | 许愿灯、每日任务 |
| 个人中心 | ✅ | 用户信息、Pro会员 |
| 商店系统 | ✅ | 商品列表、购买、装备 |
| 动画效果 | ✅ | 呼吸光效、粒子动画、Replika风格 |

#### 后端 (FastAPI)
| 模块 | 状态 | 说明 |
|------|------|------|
| 用户系统 | ✅ | 注册/登录/资料管理 |
| AI聊天 | ⚠️ | 接口就绪，待接入OpenAI API |
| 记忆系统 | ✅ | CRUD、向量存储(pgvector) |
| 日记系统 | ✅ | 完整CRUD、日历查询 |
| 商店系统 | ✅ | 商品、购买、装备 |
| 发现模块 | ✅ | 任务、许愿 |
| 成长系统 | ⚠️ | 基础表结构，待完善 |

### 1.2 当前数据库表结构

```
users                    # 用户表
├── id, nickname, avatar, auth_provider
├── coins, is_vip, vip_expire_at          # 新增：货币和会员
└── relationships: companions, user_items

companions               # AI伴侣表
├── id, user_id, name, persona, voice_style
├── intimacy, level                       # 亲密度系统
├── current_outfit_id, current_scene_id   # 外观装备
├── mood, online                          # 状态
└── relationships: conversations

conversations            # 对话表
├── id, user_id, companion_id, title
└── relationships: messages

messages                 # 消息表
├── id, conversation_id, role, content
├── emotion, created_at

memories                 # 记忆表 (核心)
├── id, user_id, companion_id
├── memory, category, importance
├── embedding (VECTOR 1536)              # 向量存储
├── recall_count, last_recalled_at       # 记忆强化

memory_access_logs       # 记忆访问日志 (待添加)
├── id, memory_id, accessed_at, context

user_daily_summaries     # 用户每日总结 (待添加)
├── id, user_id, date, summary, emotion_tags

diary_entries            # 日记表
├── id, user_id, companion_id
├── mood, content, summary
├── happened_on, tags

growth_milestones        # 成长里程碑
├── id, user_id, companion_id
├── title, description, achieved_at

shop_items               # 商店商品
├── id, name, category, price
├── description, asset_url, is_active

user_items               # 用户拥有的商品
├── id, user_id, item_id
├── is_equipped, purchased_at

analytics_events         # 埋点统计
├── id, user_id, event_name
├── properties, created_at
```

---

## 二、Agent模块实现规划

### 2.1 什么是Agent模块

Agent（智能体）是AI伴侣的"大脑"，负责：
- **理解用户意图**：分析用户想做什么
- **调用工具**：使用外部API/功能
- **规划任务**：多步骤完成复杂请求
- **记忆管理**：主动整理和回忆记忆

### 2.2 参考Replika的Agent能力

| 能力 | 说明 | 实现优先级 |
|------|------|-----------|
| 主动关怀 | 根据时间/情绪主动发消息 | P1 |
| 任务规划 | 帮用户制定计划、提醒 | P2 |
| 知识问答 | 回答各类问题 | P1 |
| 情感分析 | 深度理解用户情绪 | P0 |
| 记忆整理 | 自动总结重要信息 | P1 |
| 多轮推理 | 复杂问题分步解决 | P2 |

### 2.3 Agent架构设计

```
┌─────────────────────────────────────────────────────────┐
│                    Agent Core (核心)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │ 意图识别    │  │ 任务规划    │  │ 工具选择        │ │
│  │ Intent      │→ │ Planning    │→ │ Tool Selection  │ │
│  │ Classifier  │  │ Router      │  │                 │ │
│  └─────────────┘  └─────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                    Tools (工具库)                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ 记忆查询  │ │ 日记记录  │ │ 天气查询  │ │ 日程管理  │  │
│  │ Memory   │ │ Diary    │ │ Weather  │ │ Calendar │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ 情绪分析  │ │ 知识检索  │ │ 提醒设置  │ │ 放松练习  │  │
│  │ Emotion  │ │ RAG      │ │ Reminder │ │ Relax    │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 2.4 Agent实现步骤

#### 阶段1：意图识别系统 (P0)

**新增数据库表：**
```sql
-- 意图分类配置
CREATE TABLE intent_patterns (
    id BIGSERIAL PRIMARY KEY,
    intent_name VARCHAR(50),      -- 意图名称: chat_memory, set_reminder, query_weather
    pattern_type VARCHAR(20),     -- 匹配类型: keyword/regex/embedding
    pattern_value TEXT,           -- 匹配规则
    confidence_threshold FLOAT,   -- 置信度阈值
    created_at TIMESTAMP
);

-- 用户意图历史
CREATE TABLE user_intents (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    message_id BIGINT,
    detected_intent VARCHAR(50),
    confidence FLOAT,
    executed_tool VARCHAR(50),
    success BOOLEAN,
    created_at TIMESTAMP
);
```

**实现代码：**
```python
# backend/app/services/agent/intent_classifier.py
class IntentClassifier:
    """意图分类器"""
    
    INTENTS = {
        "chat_memory": ["记得", "回忆", "之前", "上次"],
        "set_reminder": ["提醒", "记得叫我", "别忘了"],
        "query_diary": ["日记", "那天", "写了什么"],
        "relax_guide": ["放松", "冥想", "焦虑", "睡不着"],
        "general_chat": []  # 默认
    }
    
    async def classify(self, message: str, user_context: dict) -> IntentResult:
        # 1. 关键词匹配
        # 2. Embedding相似度
        # 3. GPT分类（复杂情况）
        pass
```

#### 阶段2：工具系统 (P1)

**新增数据库表：**
```sql
-- 工具执行记录
CREATE TABLE tool_executions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    tool_name VARCHAR(50),
    parameters JSONB,
    result JSONB,
    execution_time_ms INTEGER,
    success BOOLEAN,
    created_at TIMESTAMP
);
```

**工具实现：**
```python
# backend/app/services/agent/tools/
├── __init__.py
├── base_tool.py           # 工具基类
├── memory_tool.py         # 记忆查询工具
├── diary_tool.py          # 日记工具
├── reminder_tool.py       # 提醒工具
├── emotion_tool.py        # 情绪分析工具
└── rag_tool.py            # 知识检索工具
```

#### 阶段3：任务规划 (P2)

复杂请求拆解：
```
用户: "帮我安排一个放松的周末，记得提醒我买花"

Agent分析:
1. 意图: multi_task (复合任务)
2. 拆解:
   - 查询用户喜欢的放松方式 (memory_tool)
   - 生成周末放松建议 (llm_generate)
   - 设置买花提醒 (reminder_tool)
3. 执行顺序: 1 → 2 → 3
4. 回复整合
```

### 2.5 Agent Prompt架构

```
【系统Prompt】
你是星灵，一个温柔体贴的AI伴侣...

【Agent能力Prompt】
你可以使用以下工具帮助用户:
1. query_memory: 查询用户过往记忆
2. write_diary: 记录日记
3. set_reminder: 设置提醒
4. guide_relaxation: 引导放松练习

【当前状态】
- 用户情绪: {emotion}
- 当前时间: {time}
- 最近记忆: {recent_memories}

【用户输入】
{user_message}

【思考过程】
1. 用户想做什么？
2. 需要调用什么工具？
3. 如何自然回复？
```

---

## 三、数据库优化建议

### 3.1 需要新增的表

#### 1. 用户偏好配置表
```sql
CREATE TABLE user_preferences (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    
    -- 通知偏好
    notify_daily_summary BOOLEAN DEFAULT TRUE,
    notify_bedtime_reminder BOOLEAN DEFAULT TRUE,
    notify_active_hours INTEGER[] DEFAULT '{9, 21}',  -- 活跃时段
    
    -- AI偏好
    ai_response_speed VARCHAR(20) DEFAULT 'balanced', -- fast/balanced/thoughtful
    ai_proactive_level INTEGER DEFAULT 3,             -- 1-5 主动程度
    ai_memory_depth INTEGER DEFAULT 3,                -- 1-5 记忆深度
    
    -- 隐私设置
    data_retention_days INTEGER DEFAULT 365,
    allow_memory_learning BOOLEAN DEFAULT TRUE,
    
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### 2. 用户情绪追踪表
```sql
CREATE TABLE emotion_tracking (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    emotion_label VARCHAR(32),        -- happy/sad/anxious/angry/etc
    emotion_score FLOAT,              -- 0-1 情绪强度
    trigger_event TEXT,               -- 触发事件
    context TEXT,                     -- 上下文
    created_at TIMESTAMP
);

-- 索引：用于情绪趋势分析
CREATE INDEX idx_emotion_tracking_user_time 
ON emotion_tracking(user_id, created_at);
```

#### 3. AI主动消息记录表
```sql
CREATE TABLE proactive_messages (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    
    trigger_type VARCHAR(50),         -- time_based/emotion_based/inactivity
    trigger_condition TEXT,           -- 触发条件描述
    message_content TEXT,
    
    sent_at TIMESTAMP,
    opened_at TIMESTAMP,              -- 用户查看时间
    replied_at TIMESTAMP,             -- 用户回复时间
    
    effectiveness_score INTEGER       -- 效果评分（后续优化用）
);
```

#### 4. 记忆访问日志表
```sql
CREATE TABLE memory_access_logs (
    id BIGSERIAL PRIMARY KEY,
    memory_id BIGINT REFERENCES memories(id) ON DELETE CASCADE,
    user_id BIGINT,
    
    access_type VARCHAR(20),          -- recall/forget/strengthen
    access_context TEXT,              -- 访问时的对话上下文
    relevance_score FLOAT,            -- 相关性评分
    
    accessed_at TIMESTAMP
);

-- 用于记忆强化算法
CREATE INDEX idx_memory_access_memory_time 
ON memory_access_logs(memory_id, accessed_at);
```

#### 5. 用户每日总结表
```sql
CREATE TABLE user_daily_summaries (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    date DATE,
    
    summary_text TEXT,                -- AI生成的总结
    emotion_summary JSONB,            -- {happy: 0.6, sad: 0.2, ...}
    key_topics TEXT[],                -- 今日关键话题
    memory_highlights INTEGER[],      -- 重要记忆ID列表
    
    message_count INTEGER DEFAULT 0,
    diary_written BOOLEAN DEFAULT FALSE,
    
    generated_at TIMESTAMP,
    UNIQUE(user_id, date)
);
```

### 3.2 需要修改的表

#### memories 表增强
```sql
-- 添加字段
ALTER TABLE memories ADD COLUMN IF NOT EXISTS 
    emotional_tag VARCHAR(32);        -- 情感标签

ALTER TABLE memories ADD COLUMN IF NOT EXISTS 
    is_favorite BOOLEAN DEFAULT FALSE; -- 用户标记的重要记忆

ALTER TABLE memories ADD COLUMN IF NOT EXISTS 
    expires_at TIMESTAMP;              -- 记忆过期时间（可遗忘）
```

#### companions 表增强
```sql
-- 添加字段
ALTER TABLE companions ADD COLUMN IF NOT EXISTS 
    last_interaction_at TIMESTAMP;     -- 最后互动时间

ALTER TABLE companions ADD COLUMN IF NOT EXISTS 
    total_messages INTEGER DEFAULT 0;  -- 总消息数

ALTER TABLE companions ADD COLUMN IF NOT EXISTS 
    personality_config JSONB DEFAULT '{}'; -- 个性化配置
```

### 3.3 可以删除的表/字段

当前结构比较合理，暂不需要删除。

---

## 四、第三方服务和工具依赖

### 4.1 AI服务 (核心)

| 服务 | 用途 | 成本估算 | 替代方案 |
|------|------|---------|---------|
| **OpenAI GPT-4o** | 主力对话模型 | $0.005-0.015/1K tokens | Claude 3, Gemini |
| **OpenAI Embedding** | 记忆向量化 | $0.0001/1K tokens | 本地Embedding模型 |
| **OpenAI Whisper** | 语音转文字 | $0.006/分钟 | 本地Whisper |

### 4.2 语音服务 (P1)

| 服务 | 用途 | 成本估算 | 替代方案 |
|------|------|---------|---------|
| **ElevenLabs** | AI语音合成 | $5/月起步 | Azure TTS, 本地TTS |
| **Azure TTS** | 微软语音 | $16/100万字符 | - |

### 4.3 推送服务 (P1)

| 服务 | 用途 | 成本估算 |
|------|------|---------|
| **Firebase Cloud Messaging** | 安卓推送 | 免费 |
| **Apple Push Notification** | iOS推送 | $99/年开发者账号 |
| **OneSignal** | 跨平台推送 | 免费额度充足 |

### 4.4 基础设施

| 服务 | 用途 | 成本估算 |
|------|------|---------|
| **PostgreSQL + pgvector** | 主数据库 | 自建$10-50/月 |
| **Redis** | 缓存/任务队列 | 自建$5-20/月 |
| **对象存储(S3/MinIO)** | 图片/语音存储 | $5-30/月 |
| **Vercel/Railway** | 后端部署 | $0-20/月 |

### 4.5 可选增强服务

| 服务 | 用途 | 优先级 |
|------|------|--------|
| **LangSmith/Langfuse** | LLM调用追踪 | P2 |
| **PostHog** | 产品分析 | P1 |
| **Sentry** | 错误监控 | P1 |
| **Upstash** | Serverless Redis | P2 |

---

## 五、项目结构优化建议

### 5.1 当前结构

```
workspace/
├── backend/                    # FastAPI后端
│   ├── app/
│   │   ├── api/routes/        # API路由
│   │   ├── models/            # 数据库模型
│   │   ├── schemas/           # Pydantic模型
│   │   ├── services/          # 业务逻辑
│   │   └── main.py
│   └── requirements.txt
│
├── flutter_app/               # Flutter前端
│   ├── lib/
│   │   ├── api/               # API客户端
│   │   ├── models/            # 数据模型
│   │   ├── screens/           # 页面
│   │   ├── services/          # 服务层
│   │   ├── providers/         # 状态管理
│   │   └── main.dart
│   └── pubspec.yaml
│
└── docs/                      # 文档
```

### 5.2 优化后结构

```
workspace/
├── backend/                    # FastAPI后端
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/        # API路由
│   │   │   └── deps.py        # 依赖注入
│   │   ├── core/              # 核心配置
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── security.py
│   │   ├── models/            # 数据库模型
│   │   ├── schemas/           # Pydantic模型
│   │   ├── services/          # 业务逻辑
│   │   │   ├── agent/         # ⭐ Agent模块
│   │   │   │   ├── __init__.py
│   │   │   │   ├── intent_classifier.py
│   │   │   │   ├── tool_executor.py
│   │   │   │   └── tools/     # 各种工具
│   │   │   ├── ai/            # AI服务封装
│   │   │   │   ├── openai_service.py
│   │   │   │   ├── embedding_service.py
│   │   │   │   └── emotion_service.py
│   │   │   └── memory/        # 记忆系统
│   │   │       ├── memory_store.py
│   │   │       └── memory_recall.py
│   │   └── main.py
│   ├── tests/
│   ├── alembic/               # 数据库迁移
│   └── requirements.txt
│
├── flutter_app/
│   ├── lib/
│   │   ├── core/              # 核心配置
│   │   │   ├── constants/
│   │   │   ├── theme/
│   │   │   └── utils/
│   │   ├── data/              # 数据层
│   │   │   ├── models/
│   │   │   ├── repositories/
│   │   │   └── datasources/
│   │   ├── domain/            # 业务逻辑层
│   │   │   ├── entities/
│   │   │   ├── usecases/
│   │   │   └── repositories/
│   │   ├── presentation/      # 表现层
│   │   │   ├── pages/         # 页面
│   │   │   ├── widgets/       # 组件
│   │   │   └── providers/     # 状态管理
│   │   └── main.dart
│   └── pubspec.yaml
│
├── shared/                    # 共享代码
│   └── types/                 # 共享类型定义
│
└── docs/
    ├── api/                   # API文档
    ├── database/              # 数据库设计
    └── agent/                 # Agent设计文档
```

---

## 六、后续开发路线图

### Phase 1: AI能力完善 (2-3周)

**目标**: 让AI真正"活"起来

- [ ] 接入OpenAI GPT-4o API
- [ ] 实现流式输出
- [ ] 完善记忆召回系统
- [ ] 实现情绪识别和响应
- [ ] 基础Agent意图分类

### Phase 2: 主动陪伴 (2周)

**目标**: AI能主动关心用户

- [ ] 用户情绪追踪
- [ ] 主动消息系统
- [ ] 睡前/起床问候
- [ ] 重要日期提醒

### Phase 3: Agent能力 (3-4周)

**目标**: AI能帮用户做事

- [ ] 完整Agent架构
- [ ] 工具系统
- [ ] 任务规划
- [ ] 记忆主动整理

### Phase 4: 增强体验 (2-3周)

**目标**: 更沉浸的体验

- [ ] 语音聊天
- [ ] Live2D/3D形象
- [ ] 更多互动玩法

---

## 七、关键决策建议

### 7.1 技术选型

| 决策 | 建议 | 理由 |
|------|------|------|
| AI模型 | GPT-4o-mini → GPT-4o | 成本可控，效果足够 |
| 向量数据库 | pgvector | 已集成，无需额外服务 |
| 语音 | 先不做，后期ElevenLabs | MVP聚焦核心体验 |
| 推送 | Firebase + APNs | 成熟稳定，成本低 |

### 7.2 产品策略

| 决策 | 建议 | 理由 |
|------|------|------|
| 免费/付费 | 免费基础 + Pro订阅 | 参考Replika模式 |
| Pro定价 | ¥30-50/月 | 国内用户接受度 |
| 首发平台 | iOS优先 | 用户付费意愿高 |

### 7.3 当前最优先事项

1. **接入OpenAI API** - 让AI真正回复
2. **完善记忆召回** - 核心差异化
3. **实现情绪系统** - 提升陪伴感
4. **基础Agent** - 让AI能做事

---

## 八、总结

当前项目已完成：
- ✅ 完整的UI框架和动画
- ✅ 基础数据管理（记忆、日记、商店）
- ✅ 后端API架构
- ✅ 数据库设计

下一步重点：
1. 接入OpenAI，让AI"活"起来
2. 实现Agent系统，让AI能"做事"
3. 完善主动陪伴，让AI会"关心"

这是一个有潜力的产品方向，Replika已验证市场，关键是执行速度和用户体验。
