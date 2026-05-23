# 星灵 AI 伴侣 (Xingling AI Companion)

一个基于 Flutter + FastAPI 的智能 AI 伴侣应用，具备情感陪伴、长期记忆、人设成长、主动互动等能力，让 AI 更像真人。

## 项目简介

**星灵 AI 伴侣**是一款下一代 AI 陪伴应用。用户可以与虚拟伴侣"晚星"进行自然对话，AI 会记住用户的喜好和经历，在对话中自然引用，创造真正个性化的陪伴体验。

### 核心特性

- 🤖 **情感陪伴** - 基于 GPT-4 + LangGraph 的智能对话，具备共情能力
- 🧠 **长期记忆** - 向量存储 + 语义检索，AI 真正记住用户
- 💕 **人设成长** - 关系亲密度系统，AI 性格随互动进化
- 🔔 **主动互动** - AI 主动发起早安、情绪关怀等
- 📔 **成长日记** - 记录心情变化，AI 陪伴成长
- 🎯 **每日任务** - 完成任务获得星币和亲密度奖励
- ⚡ **流式输出** - 首字响应 < 100ms，像真人一样打字

## 技术栈

### 后端 (Backend)
| 技术 | 用途 | 版本 |
|------|------|------|
| **FastAPI** | Web 框架 | 0.136+ |
| **LangGraph** | Agent 状态机 | 0.3+ |
| **LangChain** | LLM 应用框架 | 0.3+ |
| **OpenAI** | GPT-4 / Embedding | 1.54+ |
| **SQLAlchemy 2.0** | 异步 ORM | 2.0.36+ |
| **PostgreSQL + pgvector** | 主数据库 + 向量存储 | 15+ |
| **Redis** | 多级缓存 + 消息队列 | 7+ |
| **JWT** | 认证机制 | 2.10+ |

### 前端 (Frontend)
| 技术 | 用途 | 版本 |
|------|------|------|
| **Flutter** | 跨平台框架 | 3.19+ |
| **Riverpod** | 状态管理 | 2.5+ |
| **Dio** | HTTP 客户端 | 5.7+ |
| **flutter_secure_storage** | 安全存储 | 9.2+ |

## 快速开始

### 环境要求

- Python 3.10+
- Flutter 3.19+
- PostgreSQL 15+ (需 pgvector 扩展)
- Redis 7+
- OpenAI API Key

### 一键启动（推荐）

```bash
# 克隆项目
git clone <repository-url>
cd xingling-ai-companion

# 添加执行权限并启动
chmod +x scripts/*.sh
./scripts/start-all.sh
```

### 手动启动

```bash
# 1. 启动基础设施
docker-compose up -d

# 2. 启动后端
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python init_db.py
python -m uvicorn app.main:app --reload --port 8000

# 3. 启动前端
cd ../flutter_app
flutter pub get
flutter run -d chrome
```

访问 http://localhost:8000/docs 查看 API 文档。

## 项目文档

详细文档请查看 `docs/` 目录：

| 文档 | 说明 |
|------|------|
| [01-项目介绍.md](docs/01-项目介绍.md) | 项目概述、架构设计、技术栈 |
| [02-部署文档.md](docs/02-部署文档.md) | 环境配置、部署指南、常见问题 |
| [03-功能模块文档.md](docs/03-功能模块文档.md) | 各功能模块详细说明 |
| [04-AI-Agent-设计文档.md](docs/04-AI-Agent-设计文档.md) | AI Agent 架构设计 |
| [05-Agent-记忆检索流程.md](docs/05-Agent-记忆检索流程.md) | 记忆检索流程详解 |
| [06-全面优化方案.md](docs/06-全面优化方案.md) | 性能优化方案 |
| [07-API-接口文档.md](docs/07-API-接口文档.md) | API 接口详细说明 |

## 项目结构

```
xingling-ai-companion/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── agent/             # AI Agent 核心模块
│   │   │   ├── __init__.py
│   │   │   ├── companion_agent.py      # LangGraph Agent
│   │   │   ├── memory_system.py        # 记忆系统
│   │   │   ├── emotion_system.py       # 情绪系统
│   │   │   ├── persona_system.py       # 人设系统
│   │   │   ├── proactive_system.py     # 主动互动
│   │   │   ├── prompts.py              # 提示词工程
│   │   │   └── models.py               # 数据模型
│   │   ├── api/               # API 路由层
│   │   │   ├── routes/
│   │   │   │   ├── auth.py    # 认证相关
│   │   │   │   ├── chat.py    # 聊天相关 (含流式)
│   │   │   │   ├── diary.py   # 日记相关
│   │   │   │   ├── discover.py # 发现/任务
│   │   │   │   ├── growth.py  # 成长系统
│   │   │   │   ├── memories.py # 记忆管理
│   │   │   │   ├── profile.py # 个人中心
│   │   │   │   └── shop.py    # 商店系统
│   │   │   └── deps.py        # 依赖注入
│   │   ├── core/              # 核心配置
│   │   │   ├── config.py      # 应用配置
│   │   │   ├── database.py    # 数据库连接
│   │   │   └── cache.py       # 缓存管理器
│   │   ├── models/            # 数据模型 (SQLAlchemy)
│   │   │   └── entities.py    # 数据库实体
│   │   ├── schemas/           # Pydantic 模型
│   │   ├── services/          # 业务逻辑层
│   │   │   ├── chat_service.py           # 标准聊天服务
│   │   │   ├── chat_service_streaming.py # 流式聊天服务
│   │   │   └── ...
│   │   └── main.py            # 应用入口
│   ├── tests/                 # 测试模块
│   ├── init_db.py             # 数据库初始化
│   ├── requirements.txt       # Python 依赖
│   └── seed_data.py           # 初始数据
│
├── flutter_app/               # Flutter 前端
│   └── lib/
│       ├── api/               # API 客户端
│       ├── models/            # 数据模型
│       ├── providers/         # 状态管理 (Riverpod)
│       ├── screens/           # 页面
│       ├── services/          # 业务服务
│       └── main.dart          # 应用入口
│
├── docs/                      # 项目文档
├── scripts/                   # 自动化脚本
├── docker-compose.yml         # Docker 配置
└── README.md                  # 项目说明
```

## 功能模块

### 已实现 ✅

#### AI 核心能力
- [x] **LangGraph Agent** - 状态机驱动的对话系统
- [x] **长期记忆系统** - 向量存储 + 语义检索
- [x] **情绪识别** - 多维度情绪分析
- [x] **人设成长** - 关系亲密度 + 等级系统
- [x] **主动互动** - 基于上下文的主动发起
- [x] **流式输出** - SSE 实时响应

#### 应用功能
- [x] 用户认证（手机号+验证码、JWT）
- [x] 智能对话（GPT-4 + 记忆引用）
- [x] 记忆管理（查看、添加、删除）
- [x] 成长日记（日历视图）
- [x] 每日任务（星币奖励）
- [x] 商店系统（商品展示）
- [x] 个人中心（资料管理）
- [x] 多级缓存（L1内存 + L2Redis）

### 计划中 🟡

- [ ] 语音对话（语音输入/输出）
- [ ] AI 绘画（图片生成）
- [ ] 情绪报告（长期趋势分析）
- [ ] 多人社交（好友系统）
- [ ] 数据导出（聊天记录备份）

## API 接口

### 认证接口
```
POST /api/v1/auth/send-code          # 发送验证码
POST /api/v1/auth/login              # 登录
GET  /api/v1/auth/me                 # 获取当前用户
PUT  /api/v1/auth/me                 # 更新资料
POST /api/v1/auth/change-password    # 修改密码
```

### 聊天接口
```
POST /api/v1/chat/send               # 发送消息（标准）
POST /api/v1/chat/send/stream        # 发送消息（流式）⭐
GET  /api/v1/chat/history            # 聊天记录
GET  /api/v1/chat/suggestions        # 快捷回复建议
```

### 记忆接口
```
GET  /api/v1/memory/list             # 获取记忆列表
POST /api/v1/memory                  # 添加记忆
DELETE /api/v1/memory/{id}           # 删除记忆
```

### 其他接口
详见 API 文档: http://localhost:8000/docs

## 性能指标

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 首字响应时间 | 2s | **100ms** | 95% |
| 完整响应时间 | 3s | **500ms** | 83% |
| 缓存命中率 | 0% | **80%+** | - |
| 并发处理能力 | 100 | **1000+** | 10x |

## 技术亮点

### 1. LangGraph Agent 架构
- 状态机驱动的对话流程
- 意图识别 → 记忆检索 → 回复生成
- 支持复杂的多轮对话管理

### 2. 多级记忆检索
- 粗排：向量相似度（15条候选）
- 精排：多维度加权（情绪+时间+重要性）
- 选择：意图驱动（不同场景不同数量）

### 3. 流式输出优化
- SSE (Server-Sent Events) 实时推送
- 异步记忆检索（不阻塞生成）
- 首字响应 < 100ms

### 4. 多级缓存架构
- L1: 内存缓存（60秒，10,000+ ops/sec）
- L2: Redis（300秒，分布式）
- L3: PostgreSQL（持久化）

## 开发团队

- 产品 & 设计：星灵团队
- 后端开发：FastAPI + LangChain 专家组
- 前端开发：Flutter 专家组

## 许可证

MIT License

## 联系方式

- 问题反馈：GitHub Issues
- 商务合作：contact@xingling.ai

---

**星灵 AI 伴侣** - 让 AI 成为你最贴心的陪伴 💕
