# 星灵 AI 伴侣 - 优化与待修复事项

## 目录
1. [已知 Bug](#已知-bug)
2. [待优化项](#待优化项)
3. [功能增强](#功能增强)
4. [技术债务](#技术债务)
5. [性能优化](#性能优化)

---

## 已知 Bug

### 🔴 高优先级

#### 1. 记忆引用编造问题
**状态**: 部分修复中  
**描述**: AI 在引用记忆时会编造额外细节，如用户只说"喜欢打篮球"，AI 却说"想找队友"  
**影响**: 严重影响用户体验和信任度  
**修复方案**: 
- ✅ 已强化提示词约束
- ⬜ 需要添加记忆引用验证机制
- ⬜ 考虑在后端过滤 AI 回复中的编造内容

#### 2. SQL 参数绑定问题
**状态**: 已修复  
**描述**: asyncpg 不支持 `:param::type` 语法，导致向量查询失败  
**修复**: 使用 f-string 拼接 SQL，将向量直接嵌入查询

#### 3. Embedding 维度不匹配
**状态**: 已修复  
**描述**: 豆包模型输出 2048 维，但数据库期望 1536 维  
**修复**: 
- 修改 embedder 在生成向量时降维到 1536 维
- 使用 `slice_and_normalize` 方法截取前 1536 维

#### 4. timezone 未定义错误
**状态**: 已修复  
**描述**: `datetime.timezone` 未导入导致错误  
**修复**: 在 `core_memory.py` 和 `long_term_memory.py` 中添加 `from datetime import timezone`

---

## 待优化项

### 🟡 中优先级

#### 1. 验证码存储机制
**当前**: 内存存储（重启丢失）  
**建议**: 使用 Redis 存储验证码，支持过期时间
```python
# 当前实现
verification_codes: Dict[str, Dict] = {}

# 建议实现
redis.setex(f"verify:{phone}", 300, code)  # 5分钟过期
```

#### 2. 短信服务集成
**当前**: 模拟实现（打印到控制台）  
**建议**: 接入真实短信服务商
- 阿里云短信
- 腾讯云短信
- 火山引擎短信

#### 3. 错误处理完善
**问题**: 部分 API 错误返回不够友好  
**建议**:
- 统一错误响应格式
- 添加错误码体系
- 记录详细错误日志

#### 4. 事务管理优化
**问题**: 当前事务在出错后未正确回滚  
**建议**:
```python
# 使用上下文管理器确保事务正确回滚
async with session.begin():
    # 数据库操作
    pass
```

---

## 功能增强

### 🟢 低优先级（规划）

#### 1. 多模态支持
**描述**: 支持图片、语音消息  
**技术方案**:
- 图片：使用豆包多模态 Embedding
- 语音：集成 ASR（语音识别）和 TTS（语音合成）

#### 2. 主动推送系统
**描述**: AI 主动发起对话  
**场景**:
- 早安/晚安问候
- 生日提醒
- 长时间未互动提醒
- **实现**: 使用 APScheduler 定时任务

#### 3. 情感分析增强
**当前**: 基础情感标签  
**增强**:
- 细粒度情感分析（喜怒哀乐 + 强度）
- 情感趋势图表
- 情绪异常检测

#### 4. 记忆可视化
**描述**: 用户查看自己的记忆图谱  
**技术**:
- 使用 t-SNE/UMAP 降维可视化
- 时间线展示
- 记忆关联图谱

#### 5. 日记智能生成
**描述**: 基于对话自动生成日记  
**触发条件**:
- 一天结束时的总结
- 重要事件发生后
- 用户主动请求

#### 6. 成长系统完善
**当前**: 基础等级和亲密度  
**增强**:
- 成就系统
- 解锁新功能（高等级解锁特殊对话模式）
- 成长报告（周报/月报）

#### 7. 商店系统扩展
**当前**: 基础商品购买  
**增强**:
- 虚拟货币充值
- 限时活动
- 礼物赠送

---

## 技术债务

### 🟡 中优先级

#### 1. 配置管理优化
**问题**: `.env` 配置项较多，缺乏验证  
**建议**:
```python
# 使用 Pydantic Settings 进行配置验证
class Settings(BaseSettings):
    database_url: PostgresDsn
    redis_url: RedisDsn
    deepseek_api_key: str = Field(..., min_length=10)
    # 自动验证和类型转换
```

#### 2. 测试覆盖
**当前**: 缺少单元测试和集成测试  
**建议**:
- 使用 pytest 编写测试
- 覆盖率目标：> 80%
- 关键路径：认证、聊天、记忆系统

#### 3. 日志系统完善
**当前**: 基础 print 日志  
**建议**:
```python
import structlog

logger = structlog.get_logger()
logger.info("user_login", user_id=user_id, ip=client_ip)
```

#### 4. API 版本管理
**当前**: 单版本 API  
**建议**: 规划 v2 版本，支持:
- 更完善的错误码
- 分页优化
- 字段选择

#### 5. 数据库迁移工具
**当前**: 手动迁移脚本  
**建议**: 使用 Alembic 进行版本化管理
```bash
alembic revision --autogenerate -m "add new table"
alembic upgrade head
```

---

## 性能优化

### 🟢 低优先级

#### 1. 向量检索优化
**当前**: 简单的向量相似度搜索  
**优化**:
- 使用 HNSW 索引（更高维度支持）
- 向量量化（减少存储）
- 分层检索（粗筛 + 精排）

#### 2. 缓存策略增强
**当前**: 基础 Redis 缓存  
**优化**:
```python
# 多级缓存
@cache.cached(timeout=300, key_prefix="user_profile")
async def get_user_profile(user_id: int):
    # L1: 内存缓存
    # L2: Redis 缓存
    # L3: 数据库
    pass
```

#### 3. 数据库连接池
**当前**: 默认连接池配置  
**优化**:
```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    echo=False,
)
```

#### 4. 异步任务队列
**当前**: `asyncio.create_task`  
**优化**: 使用 Celery + Redis
```python
# 记忆提取改为 Celery 任务
@celery_app.task
def extract_memories_task(conversation_id: int):
    # 后台执行记忆提取
    pass
```

#### 5. API 响应压缩
**建议**: 启用 gzip 压缩
```python
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

---

## 安全加固

### 🔴 高优先级

#### 1. 输入验证增强
**建议**:
- 使用 `pydantic` 严格验证所有输入
- 防止 SQL 注入（使用参数化查询）
- XSS 防护

#### 2. 速率限制
**建议**: 使用 `slowapi` 限制 API 调用频率
```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.post("/chat/send")
@limiter.limit("10/minute")
async def send_message(request: Request, ...):
    pass
```

#### 3. 敏感信息脱敏
**建议**:
- 日志中脱敏手机号、邮箱
- API 响应不返回敏感字段

#### 4. JWT 安全
**建议**:
- 使用 RS256 算法（非对称加密）
- 设置合理的过期时间
- 实现 Token 黑名单

---

## 监控与运维

### 🟡 中优先级

#### 1. 健康检查端点
**当前**: 基础健康检查  
**增强**:
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": await check_db(),
        "redis": await check_redis(),
        "deepseek": await check_deepseek(),
    }
```

#### 2. 指标监控
**建议**: 使用 Prometheus + Grafana
```python
from prometheus_client import Counter, Histogram

request_count = Counter('requests_total', 'Total requests')
request_duration = Histogram('request_duration_seconds', 'Request duration')
```

#### 3. 分布式追踪
**建议**: 使用 Jaeger 或 Zipkin
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("chat_request"):
    # 业务逻辑
    pass
```

---

## 近期迭代计划

### 第一阶段（1-2 周）
- [ ] 修复记忆编造问题（添加验证机制）
- [ ] 完善错误处理和日志
- [ ] 接入真实短信服务
- [ ] 编写基础测试用例

### 第二阶段（2-4 周）
- [ ] 实现主动推送系统
- [ ] 多模态消息支持
- [ ] 情感分析增强
- [ ] 性能优化（缓存、连接池）

### 第三阶段（1-2 月）
- [ ] 记忆可视化
- [ ] 成长系统完善
- [ ] 日记智能生成
- [ ] 监控与告警系统

---

## 贡献指南

### 提交 Bug 报告
请包含以下信息：
1. 问题描述
2. 复现步骤
3. 期望行为
4. 实际行为
5. 环境信息（Python 版本、数据库版本等）

### 提交功能建议
请包含以下信息：
1. 功能描述
2. 使用场景
3. 建议实现方案（可选）

---

*文档版本: 1.0*  
*最后更新: 2025-01*  
*维护者: 开发团队*
