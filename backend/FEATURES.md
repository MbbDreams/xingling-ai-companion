# 星灵 AI 伴侣 - 功能文档

## 目录
1. [系统架构](#系统架构)
2. [核心功能模块](#核心功能模块)
3. [数据存储设计](#数据存储设计)
4. [工作流程详解](#工作流程详解)
5. [API 接口文档](#api-接口文档)

---

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         客户端 (Flutter/Web)                      │
└───────────────────────────────┬─────────────────────────────────┘
                                │ HTTP/WebSocket
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI 后端服务                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   API 路由   │  │  业务服务层  │  │      AI Agent 层         │  │
│  │  - auth     │  │  - auth     │  │  ┌─────────────────┐    │  │
│  │  - chat     │  │  - chat     │  │  │ CompanionAgent  │    │  │
│  │  - memory   │──│  - memory   │──│  │  - 对话管理      │    │  │
│  │  - diary    │  │  - diary    │  │  │  - 记忆提取      │    │  │
│  │  - shop     │  │  - shop     │  │  │  - 情感分析      │    │  │
│  └─────────────┘  └─────────────┘  │  └─────────────────┘    │  │
│                                    │  ┌─────────────────┐    │  │
│                                    │  │ ContextBuilder  │    │  │
│                                    │  │  - 上下文组装    │    │  │
│                                    │  │  - Token 管理   │    │  │
│                                    │  └─────────────────┘    │  │
│                                    │  ┌─────────────────┐    │  │
│                                    │  │  Memory System  │    │  │
│                                    │  │  - CoreMemory   │    │  │
│                                    │  │  - WorkingMem   │    │  │
│                                    │  │  - LongTermMem  │    │  │
│                                    │  └─────────────────┘    │  │
│                                    └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│  PostgreSQL   │      │    Redis      │      │   外部 API    │
│  + pgvector   │      │   (缓存)       │      │  - DeepSeek   │
│  - 用户数据   │      │  - 会话缓存    │      │  - 豆包       │
│  - 记忆向量   │      │  - 核心记忆    │      │  - 短信服务   │
│  - 聊天记录   │      │  - 任务队列    │      │               │
└───────────────┘      └───────────────┘      └───────────────┘
```

### 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| Web 框架 | FastAPI | RESTful API 服务 |
| 数据库 | PostgreSQL + pgvector | 关系型数据 + 向量存储 |
| 缓存 | Redis | 多级缓存、会话存储 |
| LLM | DeepSeek API | 对话生成 |
| Embedding | 豆包/火山引擎 | 文本向量化 |
| ORM | SQLAlchemy 2.0 | 数据库操作 |
| 认证 | JWT + bcrypt | 用户认证与密码加密 |
| 任务队列 | Celery + Redis | 异步任务处理 |

---

## 核心功能模块

### 1. 用户认证系统

#### 功能描述
- 手机号验证码登录/注册
- JWT Token 认证机制
- 用户信息管理
- 密码修改功能

#### 工作流程
```
1. 用户输入手机号
   ↓
2. 后端生成验证码并发送短信（当前为模拟）
   ↓
3. 用户输入验证码
   ↓
4. 后端验证验证码，生成 JWT Token
   ↓
5. 返回 access_token 和 refresh_token
   ↓
6. 后续请求携带 access_token 进行身份验证
```

#### 数据存储
- **表**: `users`
- **关键字段**: `phone`, `hashed_password`, `nickname`, `avatar`, `coins`, `is_vip`
- **Token 存储**: Redis (可选) 或内存

---

### 2. AI 对话系统

#### 功能描述
- 标准对话（同步响应）
- 流式对话（SSE 实时推送）
- 对话历史管理
- 快捷建议生成

#### 工作流程
```
用户发送消息
    ↓
[Chat Service]
    ↓
[CompanionAgent.chat()]
    ├── 1. 提取记忆（异步后台任务）
    │      - MemoryExtractor 分析对话
    │      - 提取事实、偏好、情感
    │      - 存入 LongTermMemory
    │
    ├── 2. 构建上下文（ContextBuilder）
    │      - 检索相关记忆
    │      - 组装 System Prompt
    │      - 管理工作记忆（对话历史）
    │      - Token 预算控制
    │
    ├── 3. 调用 DeepSeek API
    │      - 发送完整上下文
    │      - 获取 AI 回复
    │
    └── 4. 保存消息到数据库
           - 用户消息
           - AI 回复
    ↓
返回响应（标准/流式）
```

#### 数据存储
- **对话表**: `conversations` - 存储会话元数据
- **消息表**: `messages` - 存储每条消息内容、角色、情感
- **记忆表**: `memories` - 存储提取的长期记忆（含向量）

---

### 3. 分层记忆系统

#### 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                    分层记忆架构                          │
├─────────────────────────────────────────────────────────┤
│  Level 1: Core Memory (核心记忆)                         │
│  ├── 用户基本信息（昵称、生日、性别等）                    │
│  ├── 伴侣人设信息（名字、性格、声音等）                    │
│  ├── 关系状态（亲密度、等级、当前场景）                    │
│  └── 存储: Redis + PostgreSQL                           │
├─────────────────────────────────────────────────────────┤
│  Level 2: Working Memory (工作记忆)                      │
│  ├── 当前对话历史（最近 N 条消息）                        │
│  ├── 对话摘要（当历史过长时生成）                         │
│  ├── 当前话题和意图                                      │
│  └── 存储: 内存（每次请求重新加载）                       │
├─────────────────────────────────────────────────────────┤
│  Level 3: Long Term Memory (长期记忆)                    │
│  ├── 事实记忆（用户喜好、经历、观点）                      │
│  ├── 情感记忆（重要时刻、情绪波动）                        │
│  ├── 偏好记忆（饮食、娱乐、生活方式）                      │
│  └── 存储: PostgreSQL + pgvector（向量检索）              │
└─────────────────────────────────────────────────────────┘
```

#### 记忆提取流程
```
用户消息 + AI 回复
    ↓
[MemoryExtractor.extract_from_conversation()]
    ├── 1. 关键词预过滤（减少 API 调用）
    │      - 检查是否包含个人信息相关词汇
    │      - 无关键词则跳过提取
    │
    ├── 2. LLM 提取（异步执行）
    │      - 构建提取 Prompt
    │      - 调用 DeepSeek API
    │      - 解析 JSON 格式的记忆列表
    │
    └── 3. 存储记忆
           - 生成 Embedding 向量
           - 去重检查
           - 存入 memories 表
```

#### 记忆检索流程
```
用户新消息
    ↓
[LongTermMemory.retrieve_memories()]
    ├── 1. 向量化查询
    │      - 使用豆包 Embedding 生成向量
    │      - 降维到 1536 维（数据库兼容）
    │
    ├── 2. 向量相似度搜索
    │      - pgvector 的 <=> 操作符
    │      - 计算余弦相似度
    │      - 过滤过期记忆
    │
    ├── 3. 关键词搜索（备选）
    │      - 如果向量搜索失败
    │      - 使用 ILIKE 模糊匹配
    │
    └── 4. 质量评估与排序
           - 计算综合得分
           - 相似度 60% + 重要性 20% + 新鲜度 20%
           - 返回 Top N 条记忆
```

#### 数据存储
- **表**: `memories`
- **关键字段**: 
  - `user_id`, `companion_id` - 关联信息
  - `memory` - 记忆内容文本
  - `memory_type` - 类型：fact/preference/emotion/basic_info
  - `category` - 分类：hobby/work/food 等
  - `embedding` - 向量（Vector(1536)）
  - `importance` - 重要性评分（1-10）
  - `recall_count` - 被召回次数
  - `expires_at` - 过期时间（可选）

---

### 4. 亲密度与成长系统

#### 功能描述
- 亲密度计算（基于互动频率、对话质量）
- 等级系统（随亲密度提升）
- 关系类型变化（Friend → Mentor → Partner → Spouse）
- 成长里程碑记录

#### 亲密度计算规则
```python
# 每日首次对话 +5
# 用户主动分享 +3
# 用户表达感谢 +2
# 连续对话天数 bonus（每天+1，上限+7）
# 长时间未互动 -1/天
```

#### 关系类型配置
| 等级 | 关系类型 | 对话风格 | 亲密度范围 |
|------|----------|----------|------------|
| 1-20 | Friend | 朋友般的轻松随意 | 0-200 |
| 21-40 | Mentor | 导师般的专业引导 | 201-500 |
| 41-70 | Partner | 伙伴般的默契配合 | 501-1000 |
| 71+ | Spouse | 伴侣般的亲密无间 | 1000+ |

#### 数据存储
- **表**: `companions` - 存储伴侣状态
- **关键字段**: `intimacy`, `level`, `mood`, `persona`
- **表**: `growth_milestones` - 成长里程碑

---

### 5. 日记系统

#### 功能描述
- 日记列表查询
- 创建日记条目
- 日历视图
- 日记标签管理

#### 数据存储
- **表**: `diary_entries`
- **关键字段**: `user_id`, `companion_id`, `content`, `mood`, `happened_on`, `tags`

---

### 6. 商店系统

#### 功能描述
- 商品列表展示
- 用户余额查询
- 商品购买
- 装备/使用商品

#### 数据存储
- **表**: `shop_items` - 商品定义
- **表**: `user_items` - 用户拥有的商品
- **用户表字段**: `coins` - 金币余额

---

## 数据存储设计

### 数据库 ER 图

```
┌─────────────┐       ┌─────────────────┐       ┌─────────────┐
│    users    │       │   companions    │       │conversations│
├─────────────┤       ├─────────────────┤       ├─────────────┤
│ id (PK)     │◄──────┤ user_id (FK)    │◄──────┤ user_id     │
│ phone       │       │ id (PK)         │       │ companion_id│
│ email       │       │ name            │       │ id (PK)     │
│ nickname    │       │ persona         │       │ title       │
│ avatar      │       │ intimacy        │       │ created_at  │
│ coins       │       │ level           │       └──────┬──────┘
│ is_vip      │       │ mood            │              │
└─────────────┘       └─────────────────┘              │
                                                       │
                              ┌────────────────────────┘
                              │
                              ▼
                       ┌─────────────┐
                       │   messages  │
                       ├─────────────┤
                       │ id (PK)     │
                       │conversation_│
                       │   id (FK)   │
                       │ role        │
                       │ content     │
                       │ emotion     │
                       └─────────────┘

┌─────────────┐       ┌─────────────────┐       ┌─────────────┐
│   memories  │       │  diary_entries  │       │ growth_     │
├─────────────┤       ├─────────────────┤       │ milestones  │
│ id (PK)     │       │ id (PK)         │       ├─────────────┤
│ user_id(FK) │◄──────┤ user_id (FK)    │◄──────┤ id (PK)     │
│ companion_  │       │ companion_id(FK)│       │ user_id(FK) │
│   id (FK)   │       │ content         │       │ companion_  │
│ memory      │       │ mood            │       │   id (FK)   │
│ embedding   │       │ happened_on     │       │ title       │
│ memory_type │       │ tags            │       │ description │
│ importance  │       └─────────────────┘       └─────────────┘
└─────────────┘

┌─────────────┐       ┌─────────────────┐
│  shop_items │       │   user_items    │
├─────────────┤       ├─────────────────┤
│ id (PK)     │◄──────┤ item_id (FK)    │
│ name        │       │ user_id (FK)    │
│ category    │       │ is_equipped     │
│ price       │       │ acquired_at     │
│ description │       └─────────────────┘
└─────────────┘
```

### 关键表结构

#### users 表
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    phone VARCHAR(20) UNIQUE,
    email VARCHAR(255) UNIQUE,
    hashed_password VARCHAR(255),
    auth_provider VARCHAR(50) DEFAULT 'local',
    provider_user_id VARCHAR(255),
    nickname VARCHAR(100),
    avatar TEXT,
    gender VARCHAR(10),
    birthday DATE,
    bio TEXT,
    location VARCHAR(100),
    website VARCHAR(255),
    coins INTEGER DEFAULT 0,
    is_vip BOOLEAN DEFAULT FALSE,
    vip_expire_at TIMESTAMP,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### memories 表
```sql
CREATE TABLE memories (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    companion_id INTEGER REFERENCES companions(id),
    source_message_id INTEGER REFERENCES messages(id),
    memory TEXT NOT NULL,
    category VARCHAR(50),
    importance FLOAT DEFAULT 5.0,
    embedding VECTOR(1536),
    memory_type VARCHAR(50) DEFAULT 'fact',
    source VARCHAR(50) DEFAULT 'user_told',
    recall_count INTEGER DEFAULT 0,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 向量索引
CREATE INDEX idx_memories_embedding ON memories 
USING ivfflat (embedding vector_cosine_ops);
```

---

## 工作流程详解

### 1. 用户注册/登录流程

```
┌─────────┐    输入手机号    ┌─────────┐
│  用户   │ ───────────────► │  后端   │
└─────────┘                  └────┬────┘
                                  │
                                  ▼
                           ┌─────────────┐
                           │ 生成验证码   │
                           │ 存储到内存   │
                           │ 发送短信     │
                           └──────┬──────┘
                                  │
┌─────────┐    输入验证码    ┌────▼────┐
│  用户   │ ───────────────► │  后端   │
└─────────┘                  └────┬────┘
                                  │
                                  ▼
                           ┌─────────────┐
                           │ 验证验证码   │
                           │ 创建/查询用户│
                           │ 生成 JWT     │
                           └──────┬──────┘
                                  │
                                  ▼
                           ┌─────────────┐
                           │ 返回 Token  │
                           │ 登录成功     │
                           └─────────────┘
```

### 2. 发送消息流程

```
┌─────────┐    发送消息      ┌─────────┐
│  用户   │ ───────────────► │  后端   │
└─────────┘                  └────┬────┘
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
            ┌───────────┐ ┌───────────┐ ┌───────────┐
            │ 保存消息   │ │ 提取记忆   │ │ 构建上下文 │
            │ 到数据库   │ │ (异步)     │ │            │
            └───────────┘ └───────────┘ └─────┬─────┘
                                              │
                                              ▼
                                       ┌─────────────┐
                                       │ 检索相关记忆 │
                                       │ 组装 Prompt │
                                       │ Token 控制  │
                                       └──────┬──────┘
                                              │
                                              ▼
                                       ┌─────────────┐
                                       │ 调用 DeepSeek│
                                       │ 获取 AI 回复 │
                                       └──────┬──────┘
                                              │
                                              ▼
                                       ┌─────────────┐
                                       │ 保存 AI 回复 │
                                       │ 返回给用户   │
                                       └─────────────┘
```

### 3. 记忆提取流程

```
对话内容
    │
    ▼
┌─────────────────┐
│ 关键词预过滤     │
│ 检查是否包含     │
│ 个人信息相关词汇 │
└────────┬────────┘
         │
    ┌────┴────┐
    │ 有关键词 │      无关键词
    └────┬────┘         │
         │              ▼
         │        ┌─────────────┐
         │        │ 跳过提取     │
         │        └─────────────┘
         ▼
┌─────────────────┐
│ 构建提取 Prompt  │
│ 包含对话历史和   │
│ 提取指令         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 调用 DeepSeek    │
│ 请求 JSON 格式   │
│ 记忆列表         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 解析记忆列表     │
│ 生成 Embedding   │
│ 去重检查         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 存入 memories   │
│ 表               │
└─────────────────┘
```

---

## API 接口文档

### 认证模块 (/api/v1/auth)

| 方法 | 路径 | 描述 | 请求体 | 响应 |
|------|------|------|--------|------|
| POST | /send-code | 发送验证码 | `{phone, purpose}` | `{message}` |
| POST | /login | 登录/注册 | `{phone, code}` | `{access_token, refresh_token, user}` |
| POST | /refresh | 刷新 Token | `{refresh_token}` | `{access_token, refresh_token}` |
| GET | /me | 获取当前用户 | - | `User` |
| PUT | /me | 更新用户信息 | `UserUpdate` | `User` |
| POST | /change-password | 修改密码 | `{old_password, new_password}` | `{message}` |

### 聊天模块 (/api/v1/chat)

| 方法 | 路径 | 描述 | 请求体 | 响应 |
|------|------|------|--------|------|
| POST | /send | 发送消息 | `{conversation_id, content}` | `ChatResponse` |
| POST | /send/stream | 流式发送 | `{conversation_id, content}` | SSE Stream |
| GET | /conversations | 获取会话列表 | - | `List[Conversation]` |
| POST | /conversations | 创建会话 | `{companion_id, title?}` | `Conversation` |
| GET | /conversations/{id}/messages | 获取消息历史 | - | `List[Message]` |
| GET | /suggestions | 获取快捷建议 | - | `List[str]` |

### 记忆模块 (/api/v1/memory)

| 方法 | 路径 | 描述 | 请求体 | 响应 |
|------|------|------|--------|------|
| GET | / | 获取记忆列表 | `?type=&category=` | `List[Memory]` |
| POST | / | 创建记忆 | `{content, type, category}` | `Memory` |
| DELETE | /{id} | 删除记忆 | - | `{message}` |

### 其他模块

- **日记** `/api/v1/diary` - 日记 CRUD、日历视图
- **成长** `/api/v1/growth` - 成长数据、里程碑
- **商店** `/api/v1/shop` - 商品列表、购买、装备
- **个人中心** `/api/v1/profile` - 资料管理、统计

---

## 配置说明

### 环境变量 (.env)

```env
# 应用配置
APP_ENV=local
API_PREFIX=/api/v1

# 数据库
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/dbname

# Redis
REDIS_URL=redis://localhost:6379/0

# DeepSeek
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_MODEL=deepseek-chat

# Embedding
EMBEDDING_API_KEY=xxx
EMBEDDING_MODEL=doubao-embedding-text-240715

# JWT
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_HOURS=24
REFRESH_TOKEN_EXPIRE_DAYS=30

# CORS
CORS_ORIGINS=http://localhost:3000,*

# 记忆系统配置
MEMORY_MAX_TOKENS=3000
MEMORY_CONTEXT_RATIO=0.3
MEMORY_SIMILARITY_THRESHOLD=0.6
MEMORY_IMPORTANCE_THRESHOLD=0.3
MEMORY_MAX_SHORT_TERM=5
MEMORY_MAX_LONG_TERM=10
```

---

## 性能优化

### 1. 数据库优化
- 向量索引：使用 ivfflat 加速相似度搜索
- 查询优化：为常用查询字段添加索引
- 连接池：使用 SQLAlchemy 连接池管理

### 2. 缓存策略
- L1：内存缓存（核心记忆）
- L2：Redis 缓存（会话、用户数据）
- L3：数据库（持久化存储）

### 3. 异步处理
- 记忆提取：后台异步执行
- 消息保存：不阻塞响应
- 批量操作：减少数据库往返

---

*文档版本: 1.0*
*最后更新: 2025-01*
