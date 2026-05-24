# 星灵 AI 伴侣 (Xingling AI Companion)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/FastAPI-0.115+-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/PostgreSQL-14+-blue.svg" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
</p>

<p align="center">
  <b>一个有记忆、有温度、会成长的 AI 伴侣</b>
</p>

---

## 项目简介

星灵 AI 伴侣是一个基于 FastAPI 构建的智能陪伴应用后端，采用先进的分层记忆架构，让 AI 能够真正"记住"用户，提供个性化、有温度的对话体验。

### 核心特性

- **分层记忆系统**: 核心记忆 + 工作记忆 + 长期记忆，实现真正的长期陪伴
- **亲密度成长**: 随着互动深入，AI 与用户的亲密度会不断提升，解锁新的对话风格
- **向量语义检索**: 使用豆包 Embedding + pgvector，精准召回相关记忆
- **拟人化对话**: 基于火山引擎 SP 框架的角色扮演，让 AI 回复更自然、更有人情味
- **流式响应**: SSE 实现首字响应 < 100ms 的实时对话体验

---

## 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| Web 框架 | [FastAPI](https://fastapi.tiangolo.com/) | 高性能异步 API 框架 |
| 数据库 | [PostgreSQL](https://www.postgresql.org/) + [pgvector](https://github.com/pgvector/pgvector) | 关系型数据 + 向量存储 |
| 缓存 | [Redis](https://redis.io/) | 多级缓存、会话存储 |
| LLM | [DeepSeek](https://platform.deepseek.com/) | 对话生成 |
| Embedding | [豆包/火山引擎](https://www.volcengine.com/) | 文本向量化 |
| ORM | [SQLAlchemy 2.0](https://docs.sqlalchemy.org/) | 异步数据库操作 |
| 认证 | JWT + bcrypt | 用户认证与密码加密 |

---

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd backend

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库和 API 密钥
```

### 3. 启动数据库

```bash
# 使用 Docker（推荐）
docker run -d \
  --name xingling-postgres \
  -e POSTGRES_USER=xingling \
  -e POSTGRES_PASSWORD=xingling_dev \
  -e POSTGRES_DB=xingling_ai \
  -p 5433:5432 \
  ankane/pgvector:latest
```

### 4. 初始化数据库

```bash
python init_db.py
python seed_data.py  # 可选：插入测试数据
```

### 5. 启动服务

```bash
python app/main.py
```

服务将在 http://localhost:8000 启动

---

## 项目结构

```
backend/
├── app/
│   ├── main.py                 # FastAPI 应用入口
│   ├── agent/                  # AI Agent 核心模块
│   │   ├── companion_agent.py  # AI 伴侣主 Agent
│   │   ├── context_builder.py  # 上下文组装器
│   │   ├── prompts.py          # 提示词系统
│   │   └── memory/             # 分层记忆系统
│   │       ├── core_memory.py
│   │       ├── long_term_memory.py
│   │       ├── working_memory.py
│   │       └── embedder.py
│   ├── api/                    # API 层
│   │   ├── router.py
│   │   └── routes/             # 路由模块
│   ├── core/                   # 核心基础设施
│   ├── models/                 # 数据库模型
│   ├── schemas/                # Pydantic 数据模型
│   └── services/               # 业务服务层
├── init_db.py                  # 数据库初始化
├── seed_data.py                # 测试数据
└── requirements.txt
```

---

## 核心功能

### 1. 分层记忆架构

```
┌─────────────────────────────────────────────────────────┐
│  Level 1: Core Memory (核心记忆)                         │
│  ├── 用户基本信息（昵称、生日、性别等）                    │
│  ├── 伴侣人设信息（名字、性格、声音等）                    │
│  └── 关系状态（亲密度、等级、当前场景）                    │
├─────────────────────────────────────────────────────────┤
│  Level 2: Working Memory (工作记忆)                      │
│  ├── 当前对话历史（最近 N 条消息）                        │
│  ├── 对话摘要（当历史过长时生成）                         │
│  └── 当前话题和意图                                      │
├─────────────────────────────────────────────────────────┤
│  Level 3: Long Term Memory (长期记忆)                    │
│  ├── 事实记忆（用户喜好、经历、观点）                      │
│  ├── 情感记忆（重要时刻、情绪波动）                        │
│  └── 偏好记忆（饮食、娱乐、生活方式）                      │
└─────────────────────────────────────────────────────────┘
```

### 2. 亲密度成长系统

| 等级 | 关系类型 | 对话风格 | 亲密度范围 |
|------|----------|----------|------------|
| 1-20 | Friend | 朋友般的轻松随意 | 0-200 |
| 21-40 | Mentor | 导师般的专业引导 | 201-500 |
| 41-70 | Partner | 伙伴般的默契配合 | 501-1000 |
| 71+ | Spouse | 伴侣般的亲密无间 | 1000+ |

### 3. API 接口

- **认证** `/api/v1/auth` - 手机号验证码登录、JWT Token
- **聊天** `/api/v1/chat` - 标准/流式对话、历史记录
- **记忆** `/api/v1/memory` - 记忆管理
- **日记** `/api/v1/diary` - 日记记录
- **成长** `/api/v1/growth` - 亲密度、里程碑
- **商店** `/api/v1/shop` - 虚拟商品

完整 API 文档见 [FEATURES.md](./FEATURES.md)

---

## 文档

| 文档 | 说明 |
|------|------|
| [DEPLOYMENT.md](./DEPLOYMENT.md) | 详细部署指南，包含 Docker 部署 |
| [FEATURES.md](./FEATURES.md) | 功能架构文档，包含数据流和 API 详情 |
| [TODO.md](./TODO.md) | 待修复问题和优化计划 |

---

## 环境变量配置

```env
# 数据库
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/dbname

# DeepSeek API
DEEPSEEK_API_KEY=your-deepseek-api-key
DEEPSEEK_MODEL=deepseek-chat

# 豆包 Embedding
EMBEDDING_API_KEY=your-volcengine-api-key
EMBEDDING_MODEL=doubao-embedding-text-240715

# JWT
SECRET_KEY=your-secret-key

# CORS
CORS_ORIGINS=http://localhost:3000,*
```

---

## 开发

### 运行测试

```bash
pytest
```

### 代码格式化

```bash
black app/
isort app/
```

### 数据库迁移

```bash
# 创建新迁移
alembic revision --autogenerate -m "description"

# 执行迁移
alembic upgrade head
```

---

## 部署

### Docker Compose（推荐）

```bash
docker-compose up -d
```

### 生产环境

```bash
# 使用 Gunicorn
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

详细部署指南见 [DEPLOYMENT.md](./DEPLOYMENT.md)

---

## 贡献

欢迎提交 Issue 和 Pull Request！

### 提交 Bug 报告
请包含：
1. 问题描述
2. 复现步骤
3. 期望行为 vs 实际行为
4. 环境信息

---

## 许可证

[MIT License](./LICENSE)

---

## 联系方式

如有问题或建议，欢迎联系开发团队。

---

<p align="center">
  Made with ❤️ by 星灵团队
</p>
