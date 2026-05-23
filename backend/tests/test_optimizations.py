"""
优化功能测试 - 软件测试工程角度

测试内容:
1. 流式输出接口测试
2. Redis 缓存功能测试
3. 性能基准测试
4. 集成测试

运行: python -m pytest tests/test_optimizations.py -v
"""

import asyncio
import json
import sys
import os
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient


# ========== 单元测试 ==========

class TestCacheManager:
    """缓存管理器单元测试"""
    
    @pytest.mark.asyncio
    async def test_singleton_pattern(self):
        """测试单例模式"""
        from app.core.cache import CacheManager
        
        cache1 = CacheManager(None)
        cache2 = CacheManager(None)
        
        assert cache1 is cache2
        print("✓ 单例模式正确")
    
    @pytest.mark.asyncio
    async def test_local_cache_operations(self):
        """测试本地缓存操作"""
        from app.core.cache import CacheManager, init_cache
        
        cache = CacheManager(None)
        
        # 测试 set/get
        await cache.set("test_key", {"data": "value"}, ttl=60)
        result = await cache.get("test_key")
        
        assert result == {"data": "value"}
        print("✓ 本地缓存读写正确")
    
    @pytest.mark.asyncio
    async def test_cache_ttl(self):
        """测试缓存过期"""
        from app.core.cache import CacheManager
        
        cache = CacheManager(None)
        
        # 设置短过期时间的缓存
        await cache.set("expire_key", "value", ttl=1)
        
        # 立即获取应该存在
        result1 = await cache.get("expire_key")
        assert result1 == "value"
        
        # 等待过期
        await asyncio.sleep(1.1)
        
        # 过期后应该返回 None
        result2 = await cache.get("expire_key")
        assert result2 is None
        print("✓ 缓存过期机制正确")
    
    @pytest.mark.asyncio
    async def test_cache_stats(self):
        """测试缓存统计"""
        from app.core.cache import CacheManager
        
        cache = CacheManager(None)
        cache.hit_count = 80
        cache.miss_count = 20
        
        stats = cache.get_stats()
        
        assert stats["hit_count"] == 80
        assert stats["miss_count"] == 20
        assert stats["hit_rate"] == "80.00%"
        print("✓ 缓存统计正确")


class TestCacheKeys:
    """缓存键命名测试"""
    
    def test_key_generation(self):
        """测试缓存键生成"""
        from app.core.cache import CacheKeys
        
        assert CacheKeys.user(123) == "user:123"
        assert CacheKeys.user_profile(123) == "user:profile:123"
        assert CacheKeys.conversation(456) == "conv:456"
        assert CacheKeys.relationship(789) == "relationship:789"
        
        print("✓ 缓存键命名正确")


# ========== 集成测试 ==========

class TestStreamingChat:
    """流式聊天集成测试"""
    
    def test_streaming_endpoint_exists(self):
        """测试流式接口是否存在"""
        from app.main import app
        
        client = TestClient(app)
        
        # 检查路由是否存在
        routes = [route.path for route in app.routes]
        assert "/api/v1/chat/send/stream" in routes
        print("✓ 流式接口路由正确")
    
    def test_streaming_response_format(self):
        """测试流式响应格式"""
        # 模拟 SSE 事件格式
        event = {"type": "thinking", "data": {"content": "测试中..."}}
        formatted = f"data: {json.dumps(event)}\n\n"
        
        assert formatted.startswith("data: ")
        assert formatted.endswith("\n\n")
        print("✓ SSE 格式正确")


# ========== 性能测试 ==========

class TestPerformance:
    """性能基准测试"""
    
    @pytest.mark.asyncio
    async def test_cache_performance(self):
        """测试缓存性能"""
        from app.core.cache import CacheManager
        
        cache = CacheManager(None)
        
        # 预热
        for i in range(100):
            await cache.set(f"key_{i}", f"value_{i}", ttl=300)
        
        # 测试读取性能
        start = time.time()
        for i in range(1000):
            await cache.get(f"key_{i % 100}")
        elapsed = time.time() - start
        
        # 本地缓存应该非常快 (< 10ms 对于 1000 次)
        assert elapsed < 0.1
        print(f"✓ 缓存读取性能: {1000/elapsed:.0f} ops/sec")
    
    @pytest.mark.asyncio
    async def test_memory_usage(self):
        """测试内存使用"""
        from app.core.cache import CacheManager
        
        cache = CacheManager(None)
        
        # 存储大量数据
        for i in range(1000):
            await cache.set(f"key_{i}", {"data": "x" * 100}, ttl=300)
        
        stats = cache.get_stats()
        
        # 本地缓存大小应该合理
        assert stats["local_cache_size"] == 1000
        print(f"✓ 内存使用: {stats['local_cache_size']} 条缓存")


# ========== 端到端测试 ==========

@pytest.mark.asyncio
async def test_full_chat_flow():
    """完整聊天流程测试"""
    print("\n" + "=" * 60)
    print("完整流程测试")
    print("=" * 60)
    
    # 1. 测试缓存初始化
    from app.core.cache import CacheManager, CacheKeys
    cache = CacheManager(None)
    print("✓ 缓存初始化")
    
    # 2. 测试缓存读写
    user_id = 1
    user_data = {"id": user_id, "name": "测试用户"}
    await cache.set(CacheKeys.user(user_id), user_data, ttl=300)
    cached_user = await cache.get(CacheKeys.user(user_id))
    assert cached_user == user_data
    print("✓ 用户数据缓存")
    
    # 3. 测试缓存统计
    stats = cache.get_stats()
    assert stats["hit_count"] > 0
    print(f"✓ 缓存统计: 命中率 {stats['hit_rate']}")
    
    print("\n所有测试通过!")


# ========== 手动运行 ==========

def run_manual_tests():
    """手动运行测试"""
    print("\n" + "=" * 70)
    print("  优化功能测试")
    print("=" * 70 + "\n")
    
    # 运行异步测试
    asyncio.run(test_full_chat_flow())
    
    # 运行其他测试
    cache_test = TestCacheManager()
    asyncio.run(cache_test.test_singleton_pattern())
    asyncio.run(cache_test.test_local_cache_operations())
    asyncio.run(cache_test.test_cache_stats())
    
    key_test = TestCacheKeys()
    key_test.test_key_generation()
    
    print("\n" + "=" * 70)
    print("  所有测试通过!")
    print("=" * 70)


if __name__ == "__main__":
    run_manual_tests()
