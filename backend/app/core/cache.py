"""
缓存管理器 - 多级缓存架构

L1: 内存缓存 (最近对话上下文)
L2: Redis 缓存 (用户会话、记忆摘要)
L3: 数据库 (完整数据)
"""
import json
import time
from typing import Any, Dict, Optional
from functools import wraps

from redis.asyncio import Redis


class CacheManager:
    """
    统一缓存管理器
    
    使用多级缓存策略：
    - L1: 本地内存 (最快，但进程隔离)
    - L2: Redis (分布式，持久)
    - L3: 数据库 (最终一致性)
    """
    
    _instance = None
    
    def __new__(cls, redis_client: Redis = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, redis_client: Redis = None):
        if self._initialized:
            return
        
        self.redis = redis_client
        self.local_cache: Dict[str, Any] = {}  # L1: 内存缓存
        self.local_cache_ttl: Dict[str, float] = {}  # 内存缓存过期时间
        
        # 统计
        self.hit_count = 0
        self.miss_count = 0
        self.local_hit_count = 0
        self.redis_hit_count = 0
        
        self._initialized = True
    
    async def get(self, key: str, default: Any = None) -> Any:
        """
        获取缓存值
        
        顺序: L1内存 -> L2Redis -> default
        """
        # L1: 检查内存缓存
        if key in self.local_cache:
            if time.time() < self.local_cache_ttl.get(key, 0):
                self.hit_count += 1
                self.local_hit_count += 1
                return self.local_cache[key]
            else:
                # 过期，清理
                del self.local_cache[key]
                del self.local_cache_ttl[key]
        
        # L2: 检查 Redis
        if self.redis:
            try:
                value = await self.redis.get(key)
                if value:
                    self.hit_count += 1
                    self.redis_hit_count += 1
                    
                    # 解析 JSON
                    try:
                        parsed = json.loads(value)
                    except:
                        parsed = value.decode() if isinstance(value, bytes) else value
                    
                    # 回填 L1 缓存
                    self.local_cache[key] = parsed
                    self.local_cache_ttl[key] = time.time() + 60  # 内存缓存 60 秒
                    
                    return parsed
            except Exception as e:
                print(f"Redis get error: {e}")
        
        # 未命中
        self.miss_count += 1
        return default
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: int = 300,
        use_local: bool = True
    ):
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: Redis 过期时间（秒）
            use_local: 是否同时写入本地缓存
        """
        # 序列化
        try:
            serialized = json.dumps(value, ensure_ascii=False, default=str)
        except:
            serialized = str(value)
        
        # L1: 写入内存缓存
        if use_local:
            self.local_cache[key] = value
            self.local_cache_ttl[key] = time.time() + min(ttl, 60)  # 内存最多 60 秒
        
        # L2: 写入 Redis
        if self.redis:
            try:
                await self.redis.setex(key, ttl, serialized)
            except Exception as e:
                print(f"Redis set error: {e}")
    
    async def delete(self, key: str):
        """删除缓存"""
        # L1
        if key in self.local_cache:
            del self.local_cache[key]
            del self.local_cache_ttl[key]
        
        # L2
        if self.redis:
            try:
                await self.redis.delete(key)
            except Exception as e:
                print(f"Redis delete error: {e}")
    
    async def get_or_set(
        self, 
        key: str, 
        getter_func, 
        ttl: int = 300
    ) -> Any:
        """
        获取或设置缓存
        
        如果缓存不存在，调用 getter_func 获取值并缓存
        """
        value = await self.get(key)
        if value is not None:
            return value
        
        # 执行获取函数
        value = await getter_func()
        
        # 写入缓存
        if value is not None:
            await self.set(key, value, ttl)
        
        return value
    
    def cached(self, ttl: int = 300, key_prefix: str = ""):
        """
        缓存装饰器
        
        使用示例:
            @cache.cached(ttl=60, key_prefix="user")
            async def get_user(user_id: int):
                return await db.get_user(user_id)
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # 构建缓存键
                cache_key = f"{key_prefix}:{func.__name__}:{args}:{kwargs}"
                
                # 尝试获取缓存
                cached_value = await self.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                # 执行函数
                result = await func(*args, **kwargs)
                
                # 写入缓存
                if result is not None:
                    await self.set(cache_key, result, ttl)
                
                return result
            return wrapper
        return decorator
    
    @property
    def hit_rate(self) -> float:
        """缓存命中率"""
        total = self.hit_count + self.miss_count
        return self.hit_count / total if total > 0 else 0
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        return {
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "local_hit_count": self.local_hit_count,
            "redis_hit_count": self.redis_hit_count,
            "hit_rate": f"{self.hit_rate:.2%}",
            "local_cache_size": len(self.local_cache),
        }
    
    async def clear_local(self):
        """清理本地缓存"""
        self.local_cache.clear()
        self.local_cache_ttl.clear()
    
    async def clear_all(self):
        """清理所有缓存"""
        await self.clear_local()
        
        if self.redis:
            try:
                await self.redis.flushdb()
            except Exception as e:
                print(f"Redis flush error: {e}")


# 全局缓存实例
cache: Optional[CacheManager] = None


def init_cache(redis_client: Redis):
    """初始化缓存"""
    global cache
    cache = CacheManager(redis_client)
    return cache


async def get_cache() -> CacheManager:
    """获取缓存实例"""
    if cache is None:
        raise RuntimeError("Cache not initialized")
    return cache


# 常用缓存键构建器
class CacheKeys:
    """缓存键命名规范"""
    
    @staticmethod
    def user(user_id: int) -> str:
        return f"user:{user_id}"
    
    @staticmethod
    def user_profile(user_id: int) -> str:
        return f"user:profile:{user_id}"
    
    @staticmethod
    def conversation(conv_id: int) -> str:
        return f"conv:{conv_id}"
    
    @staticmethod
    def conversation_messages(conv_id: int, page: int = 1) -> str:
        return f"conv:{conv_id}:messages:{page}"
    
    @staticmethod
    def memories(user_id: int, query_hash: str = "") -> str:
        return f"memories:{user_id}:{query_hash}"
    
    @staticmethod
    def relationship(user_id: int) -> str:
        return f"relationship:{user_id}"
    
    @staticmethod
    def rate_limit(key: str) -> str:
        return f"ratelimit:{key}"
    
    @staticmethod
    def lock(resource: str) -> str:
        return f"lock:{resource}"
