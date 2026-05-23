# 星灵 AI 伴侣 (Xingling AI Companion)

一个基于 Flutter + FastAPI 的 AI 伴侣应用，提供智能对话、记忆系统、成长日记、个性化定制等功能。

## 项目简介

**星灵 AI 伴侣**是一款智能 AI 陪伴应用，用户可以与虚拟伴侣"晚星"进行自然对话，记录成长日记，管理珍贵记忆，并通过完成任务获得奖励来培养与伴侣的亲密度。

### 核心特性

- 🤖 **智能对话** - 基于 GPT-4 的自然语言对话，情感理解和记忆引用
- 🧠 **记忆系统** - AI 记住用户的重要信息，创造个性化陪伴体验
- 📔 **成长日记** - 记录心情变化，AI 陪伴成长
- 🎯 **每日任务** - 完成任务获得星币和亲密度奖励
- 🛍️ **商店系统** - 星币、VIP、服装场景等虚拟商品
- 👤 **个人中心** - 完整的资料管理和账户统计

## 技术栈

### 后端
- **FastAPI** - 高性能 Web 框架
- **SQLAlchemy 2.0** - 异步 ORM
- **PostgreSQL + pgvector** - 主数据库和向量存储
- **Redis** - 缓存和消息队列
- **OpenAI API** - GPT-4 对话和 Embedding
- **JWT** - 认证机制

### 前端
- **Flutter** - 跨平台框架
- **Riverpod** - 状态管理
- **Dio** - HTTP 客户端
- **flutter_secure_storage** - 安全存储

## 快速开始

### 环境要求

- Python 3.10+
- Flutter 3.19+
- PostgreSQL 15+
- Redis 7+

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

## 项目结构

```
xingling-ai-companion/
├── backend/              # FastAPI 后端
│   ├── app/
│   │   ├── api/          # API 路由
│   │   ├── core/         # 核心配置
│   │   ├── models/       # 数据模型
│   │   ├── schemas/      # Pydantic 模型
│   │   └── services/     # 业务逻辑
│   ├── init_db.py        # 数据库初始化
│   └── requirements.txt
├── flutter_app/          # Flutter 前端
│   └── lib/
│       ├── api/          # API 客户端
│       ├── models/       # 数据模型
│       ├── providers/    # 状态管理
│       ├── screens/      # 页面
│       └── services/     # 业务服务
├── docs/                 # 项目文档
└── docker-compose.yml    # Docker 配置
```

## 功能模块

### 已实现 ✅

- [x] 用户认证（手机号+验证码、JWT）
- [x] 智能对话（GPT-4）
- [x] 记忆系统（向量存储）
- [x] 成长日记（日历视图）
- [x] 每日任务（星币奖励）
- [x] 商店系统（商品展示）
- [x] 个人中心（资料管理）
- [x] 成长系统（亲密度、等级）

### 计划中 🟡

- [ ] 语音对话
- [ ] AI 绘画
- [ ] 多人社交
- [ ] 数据导出
- [ ] 智能提醒
- [ ] 情绪分析

## API 接口

### 认证接口
```
POST /api/v1/auth/send-code          # 发送验证码
POST /api/v1/auth/login              # 登录
GET  /api/v1/auth/me                 # 获取当前用户
PUT  /api/v1/auth/me                 # 更新资料
```

### 聊天接口
```
POST /api/v1/chat/send               # 发送消息
GET  /api/v1/chat/history            # 聊天记录
GET  /api/v1/chat/suggestions        # 快捷回复
```

### 其他接口
详见 API 文档: http://localhost:8000/docs

## 截图展示

| 聊天界面 | 日记页面 | 发现页面 |
|---------|---------|---------|
| ![Chat](docs/screenshots/chat.png) | ![Diary](docs/screenshots/diary.png) | ![Discover](docs/screenshots/discover.png) |

## 开发团队

- 产品 & 设计：星灵团队
- 后端开发：FastAPI 专家组
- 前端开发：Flutter 专家组

## 许可证

MIT License

## 联系方式

- 问题反馈：GitHub Issues
- 商务合作：contact@xingling.ai

---

**星灵 AI 伴侣** - 让 AI 成为你最贴心的陪伴
