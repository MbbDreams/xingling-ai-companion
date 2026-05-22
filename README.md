# Xingling AI Companion MVP

这是根据 `Xingling Ai Companion Full Mvp Plan.pdf` 与原型 UI 图搭建的 MVP 工程骨架。当前版本包含静态移动端 Web 原型与 FastAPI 后端骨架；后端已补齐数据库模型、核心接口、PostgreSQL + pgvector 建表脚本，以及 Redis/Celery 预留。

## 运行方式

当前前端是零依赖静态工程，可以直接打开：

```bash
open index.html
```

或用本地静态服务器运行：

```bash
python3 -m http.server 4173
```

然后访问 `http://localhost:4173`。

后端运行：

```bash
docker compose up -d postgres redis
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端地址：

- 健康检查：`http://localhost:8000/health`
- API 文档：`http://localhost:8000/docs`

## 目录说明

```text
xingling-ai-companion/
  backend/                   # FastAPI 后端服务
    app/                     # API、模型、服务层、任务队列
    db/create_database.sql   # 手动创建数据库与用户
    db/schema.sql            # PostgreSQL + pgvector 表结构
    requirements.txt         # Python 依赖
  docker-compose.yml         # PostgreSQL(pgvector) + Redis
  index.html                 # App HTML 入口
  src/styles.css             # 全局视觉、布局、组件样式
  src/app.js                 # 应用启动入口
  src/data/mockData.js       # MVP 阶段的模拟数据
  src/modules/               # 前端页面与状态模块
  src/backend/               # 前端接口契约参考
  src/assets/reference/      # 原型图参考资产
  docs/                      # 产品与开发说明
```

## 已补齐的后端能力

- `POST /api/v1/chat/send`：聊天消息、情绪识别、AI 回复、消息持久化。
- `GET /api/v1/memory/list` / `POST /api/v1/memory`：长期记忆列表与新增。
- `GET /api/v1/diary/list` / `POST /api/v1/diary`：日记与心情记录。
- `GET /api/v1/growth/summary`：亲密度、消息数、记忆数、里程碑。
- `GET /api/v1/shop/items`：商店商品列表。
- `GET /api/v1/profile/me`：当前用户与 AI 伴侣资料。
- `backend/db/schema.sql`：users、companions、conversations、messages、memories、diary_entries、growth_milestones、shop_items、analytics_events。

## 已覆盖的 MVP UI

- 聊天页：文字消息、输入框、快捷动作、底部导航。
- 伴侣主页：亲密度、记忆摘要、语音片段、任务入口。
- 形象页：角色形象、服装选项、语音包。
- 记忆页：分类筛选、记忆列表、新增按钮。
- 日记页：日期选择、心情选择、日记卡片。
- 成长页：亲密度等级、互动统计、里程碑。
- 语音通话页：通话中状态与操作按钮。
- 发现页：活动任务、许愿灯、社区入口。
- 商店页：会员、服装、场景、语音包。
- 我的页：会员状态、设置列表、退出按钮。

## 下一步建议

1. 把现有静态 Web 原型接入 `http://localhost:8000/api/v1`。
2. 接入真实用户系统与 Firebase/Supabase/Auth0 等鉴权。
3. 给记忆召回补 OpenAI Embedding 写入与 pgvector 相似度检索。
4. 接入 TTS/ASR 与主动消息推送。
5. 将静态角色图替换为可配置 Live2D、3D 或视频形象资源。
