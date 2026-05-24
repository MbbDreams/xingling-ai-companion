# 星灵 AI 伴侣 - 部署文档

## 项目概述

星灵 AI 伴侣是一个基于 FastAPI 的 AI 陪伴应用后端，采用 DeepSeek LLM 提供对话能力，豆包 Embedding 提供向量语义检索，PostgreSQL + pgvector 存储数据。

## 系统要求

### 硬件要求
- **CPU**: 2 核及以上
- **内存**: 4GB 及以上
- **存储**: 20GB 可用空间

### 软件要求
- **Python**: 3.10+
- **PostgreSQL**: 14+ (需安装 pgvector 扩展)
- **Redis**: 6+ (可选，用于缓存和任务队列)

## 部署步骤

### 1. 环境准备

#### 安装 PostgreSQL 和 pgvector

**macOS:**
```bash
brew install postgresql@14
brew install pgvector
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install postgresql-14
sudo apt-get install postgresql-14-pgvector
```

**Docker (推荐):**
```bash
docker run -d \
  --name xingling-postgres \
  -e POSTGRES_USER=xingling \
  -e POSTGRES_PASSWORD=xingling_dev \
  -e POSTGRES_DB=xingling_ai \
  -p 5433:5432 \
  ankane/pgvector:latest
```

#### 安装 Redis (可选)
```bash
# macOS
brew install redis
brew services start redis

# Ubuntu
sudo apt-get install redis-server
sudo systemctl start redis

# Docker
docker run -d --name xingling-redis -p 6380:6379 redis:7-alpine
```

### 2. 项目配置

#### 克隆项目
```bash
git clone <repository-url>
cd backend
```

#### 创建虚拟环境
```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\activate  # Windows
```

#### 安装依赖
```bash
pip install -r requirements.txt
```

#### 配置环境变量
```bash
cp .env.example .env
```

编辑 `.env` 文件，配置以下关键项：

```env
# 数据库配置
DATABASE_URL=postgresql+asyncpg://xingling:xingling_dev@localhost:5433/xingling_ai

# Redis 配置 (可选)
REDIS_URL=redis://localhost:6380/0

# DeepSeek API 配置 (必需)
DEEPSEEK_API_KEY=your-deepseek-api-key
DEEPSEEK_MODEL=deepseek-chat

# 豆包 Embedding 配置 (必需)
EMBEDDING_API_KEY=your-volcengine-api-key
EMBEDDING_MODEL=doubao-embedding-text-240715

# JWT 密钥 (生产环境必须修改)
SECRET_KEY=your-secret-key-here-change-in-production

# CORS 配置 (根据前端地址调整)
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,*
```

### 3. 获取 API 密钥

#### DeepSeek API Key
1. 访问 https://platform.deepseek.com/api_keys
2. 注册/登录账号
3. 创建 API Key
4. 复制到 `.env` 的 `DEEPSEEK_API_KEY`

#### 豆包/火山引擎 API Key
1. 访问 https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey
2. 注册/登录火山引擎账号
3. 创建 API Key
4. 复制到 `.env` 的 `EMBEDDING_API_KEY`
5. 在控制台开通 Embedding 模型权限

### 4. 数据库初始化

#### 创建数据库表
```bash
python init_db.py
```

#### 插入测试数据 (可选)
```bash
python seed_data.py
```

### 5. 启动服务

#### 开发模式 (带热重载)
```bash
python app/main.py
```
服务将在 http://localhost:8000 启动

#### 生产模式
```bash
# 使用 Gunicorn + Uvicorn
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

#### 使用自动化脚本
```bash
chmod +x start.sh
./start.sh
```

### 6. 验证部署

#### 健康检查
```bash
curl http://localhost:8000/health
```

#### API 文档
浏览器访问: http://localhost:8000/docs

## Docker 部署

### 使用 Docker Compose (推荐)

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: ankane/pgvector:latest
    environment:
      POSTGRES_USER: xingling
      POSTGRES_PASSWORD: xingling_dev
      POSTGRES_DB: xingling_ai
    ports:
      - "5433:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6380:6379"

  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://xingling:xingling_dev@postgres:5432/xingling_ai
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env
    depends_on:
      - postgres
      - redis

volumes:
  postgres_data:
```

启动:
```bash
docker-compose up -d
```

### 构建 Docker 镜像

创建 `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "app/main.py"]
```

构建并运行:
```bash
docker build -t xingling-backend .
docker run -d -p 8000:8000 --env-file .env xingling-backend
```

## 生产环境配置

### 1. 安全加固

#### 修改 JWT 密钥
```bash
# 生成强密钥
openssl rand -hex 32
```
将生成的密钥设置到 `.env` 的 `SECRET_KEY`

#### 配置 HTTPS
使用 Nginx 反向代理:

```nginx
server {
    listen 443 ssl;
    server_name api.xingling.ai;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2. 性能优化

#### 数据库连接池
在 `.env` 中添加:
```env
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
```

#### Redis 缓存
确保 Redis 配置正确，用于:
- 会话缓存
- 核心记忆缓存
- API 响应缓存

### 3. 监控和日志

#### 日志配置
```python
# 在 app/core/config.py 中添加
log_level: str = "INFO"
log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

#### 健康检查端点
```bash
curl http://localhost:8000/health
```

## 故障排查

### 常见问题

#### 1. 数据库连接失败
```
Error: connection to server at "localhost" failed
```
**解决**: 检查 PostgreSQL 是否运行，端口是否正确

#### 2. pgvector 扩展未安装
```
Error: type "vector" does not exist
```
**解决**: 安装 pgvector 扩展并重启 PostgreSQL

#### 3. API Key 无效
```
Error: 401 Unauthorized
```
**解决**: 检查 `.env` 中的 API Key 是否正确

#### 4. CORS 错误
```
Error: CORS policy violation
```
**解决**: 在 `.env` 中添加前端域名到 `CORS_ORIGINS`

#### 5. Embedding 维度不匹配
```
Error: expected 1536 dimensions, not 2048
```
**解决**: 重新初始化数据库 `python init_db.py --force`，embedder 会自动降维到 1536

## 更新部署

### 更新代码
```bash
git pull origin main
```

### 更新依赖
```bash
pip install -r requirements.txt --upgrade
```

### 重新初始化数据库（如需要）
```bash
python init_db.py --force
```

### 重启服务
```bash
# 如果使用 systemd
sudo systemctl restart xingling-backend

# 如果使用 Docker
docker-compose restart backend
```

## 备份和恢复

### 数据库备份
```bash
pg_dump -h localhost -p 5433 -U xingling -d xingling_ai > backup.sql
```

### 数据库恢复
```bash
psql -h localhost -p 5433 -U xingling -d xingling_ai < backup.sql
```

## 联系方式

如有部署问题，请联系开发团队。
