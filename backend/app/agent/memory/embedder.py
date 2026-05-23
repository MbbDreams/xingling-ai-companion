"""
向量化服务 - Embedding Service

统一管理文本向量化，支持多种 Embedding 模型。
默认使用 OpenAI text-embedding-3-small (1536维)。
提供降级方案：embedding API 不可用时回退到关键词匹配。
"""

import numpy as np
from typing import Optional
import httpx
from openai import AsyncOpenAI

from app.core.config import settings


class Embedder:
    """向量化服务"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "text-embedding-3-small",
    ):
        """
        初始化 Embedding 客户端
        
        Args:
            api_key: OpenAI API key（用于 embedding）
            base_url: API 基础 URL
            model: Embedding 模型名称
        """
        # Embedding 必须使用 OpenAI 官方 API（DeepSeek 不提供 embedding）
        self.api_key = api_key or settings.embedding_api_key or settings.openai_api_key
        # 强制使用 OpenAI 官方地址，忽略可能配置的 DeepSeek 地址
        self.base_url = base_url or settings.embedding_base_url or "https://api.openai.com/v1"
        self.model = model or settings.embedding_model or "text-embedding-3-small"
        self.dimension = 1536  # text-embedding-3-small 的维度
        
        # 初始化 OpenAI 客户端
        if self.api_key:
            # 如果 base_url 包含 deepseek，强制使用 OpenAI 官方地址
            if self.base_url and "deepseek" in self.base_url.lower():
                print("[Embedder] 检测到 DeepSeek URL，强制使用 OpenAI 官方 embedding API")
                self.base_url = "https://api.openai.com/v1"
            
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url if self.base_url else None,
            )
        else:
            print("[Embedder] 警告: 未配置 API key，embedding 功能不可用")
            self.client = None
    
    async def embed_text(self, text: str) -> Optional[list[float]]:
        """
        生成文本的向量表示
        
        Args:
            text: 输入文本
            
        Returns:
            向量列表，如果失败返回 None
        """
        if not self.client:
            return None
        
        if not text or not text.strip():
            return None
        
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text.strip()[:8000],  # 限制长度，避免超长文本
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"[Embedder] 生成向量失败: {e}")
            return None
    
    async def embed_batch(self, texts: list[str]) -> list[Optional[list[float]]]:
        """
        批量生成向量（提高效率）
        
        Args:
            texts: 文本列表
            
        Returns:
            向量列表（与输入顺序对应，失败的项为 None）
        """
        if not self.client:
            return [None] * len(texts)
        
        # 过滤空文本
        valid_texts = [t.strip()[:8000] if t else "" for t in texts]
        
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=valid_texts,
            )
            # 按 index 排序
            embeddings = {item.index: item.embedding for item in response.data}
            return [embeddings.get(i) for i in range(len(texts))]
        except Exception as e:
            print(f"[Embedder] 批量生成向量失败: {e}")
            return [None] * len(texts)
    
    @staticmethod
    def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
        """
        计算两个向量的余弦相似度
        
        Args:
            vec_a: 向量 A
            vec_b: 向量 B
            
        Returns:
            相似度值 [0, 1]
        """
        if not vec_a or not vec_b:
            return 0.0
        
        a = np.array(vec_a)
        b = np.array(vec_b)
        
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(dot_product / (norm_a * norm_b))
    
    @staticmethod
    def euclidean_distance(vec_a: list[float], vec_b: list[float]) -> float:
        """
        计算两个向量的欧氏距离
        
        Args:
            vec_a: 向量 A
            vec_b: 向量 B
            
        Returns:
            距离值
        """
        if not vec_a or not vec_b:
            return float('inf')
        
        a = np.array(vec_a)
        b = np.array(vec_b)
        
        return float(np.linalg.norm(a - b))


# 全局单例
_embedder_instance: Optional[Embedder] = None


def get_embedder() -> Embedder:
    """获取全局 Embedder 实例"""
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = Embedder()
    return _embedder_instance
