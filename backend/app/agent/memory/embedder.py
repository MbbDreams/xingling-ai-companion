"""
向量化服务 - Embedding Service

使用豆包(Doubao/火山引擎) Embedding 模型进行文本向量化。

文档:
- 快速入门: https://www.volcengine.com/docs/82379/1399008
- 多模态向量化: https://www.volcengine.com/docs/82379/1409291
"""

import os
import numpy as np
from typing import Optional, List, Dict, Any

from app.core.config import settings


class Embedder:
    """豆包向量化服务"""
    
    # 豆包文本 Embedding 模型维度映射
    TEXT_MODELS = {
        "doubao-embedding-text-240715": 1024,
        "doubao-embedding-large-text-241215": 4096,
    }
    
    # 豆包多模态 Embedding 模型维度映射
    VISION_MODELS = {
        "doubao-embedding-vision-251215": 2048,
        "doubao-embedding-vision-250615": 2048,
        "doubao-embedding-vision-250328": 2048,
        "doubao-embedding-vision-241215": 3072,  # 不支持降维
    }
    
    # 合并所有豆包模型
    MODELS = {**TEXT_MODELS, **VISION_MODELS}
    
    # 豆包 API 基础 URL
    BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """
        初始化豆包 Embedding 客户端
        
        Args:
            api_key: 豆包 API Key (从 https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey 获取)
            model: Embedding 模型名称，默认从配置读取
        """
        self.api_key = api_key or settings.embedding_api_key
        self.model = model or settings.embedding_model or "doubao-embedding-text-240715"
        self.dimension = self.MODELS.get(self.model, 1024)
        
        # 延迟导入豆包 SDK
        self._client = None
        self._init_client()
    
    def _init_client(self):
        """初始化豆包客户端"""
        if not self.api_key:
            print("[Embedder] 警告: 未配置豆包 API Key，embedding 功能不可用")
            print("[Embedder] 请在 .env 文件中设置 EMBEDDING_API_KEY")
            return
        
        try:
            from volcenginesdkarkruntime import Ark
            self._client = Ark(
                api_key=self.api_key,
                base_url=self.BASE_URL,
            )
            print(f"[Embedder] 豆包 embedding 初始化成功，模型: {self.model}，维度: {self.dimension}")
        except ImportError:
            print("[Embedder] 警告: 未安装 volcengine-python-sdk")
            print("[Embedder] 请运行: pip install volcengine-python-sdk")
            self._client = None
    
    @property
    def client(self):
        """获取豆包客户端"""
        return self._client
    
    def _is_vision_model(self) -> bool:
        """判断当前模型是否为多模态模型"""
        return self.model in self.VISION_MODELS
    
    async def embed_text(
        self,
        text: str,
        dimensions: Optional[int] = None,
    ) -> Optional[List[float]]:
        """
        生成文本的向量表示
        
        Args:
            text: 输入文本
            dimensions: 向量降维后的维度（默认 1536，适配数据库）
            
        Returns:
            向量列表，如果失败返回 None
        """
        if not self._client:
            return None
        
        if not text or not text.strip():
            return None
        
        # 默认降维到 1536（数据库兼容）
        target_dim = dimensions or 1536
        
        # 多模态模型需要用 multimodal_embeddings 接口
        if self._is_vision_model():
            embedding = await self.embed_multimodal(
                [{"type": "text", "text": text.strip()[:8000]}],
                dimensions=target_dim,  # 多模态模型会手动降维
            )
            return embedding
        
        # 文本模型用 embeddings 接口
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            
            kwargs = {
                "model": self.model,
                "input": [text.strip()[:8000]],
                "encoding_format": "float",
            }
            
            # 如果模型支持降维且需要降维
            if target_dim < self.dimension:
                kwargs["dimensions"] = target_dim
            
            resp = await loop.run_in_executor(
                None,
                lambda: self._client.embeddings.create(**kwargs)
            )
            
            if resp.data and len(resp.data) > 0:
                embedding = resp.data[0].embedding
                # 如果返回的维度仍大于目标维度，手动降维
                if len(embedding) > target_dim:
                    embedding = self.slice_and_normalize(embedding, target_dim)
                return embedding
            return None
            
        except Exception as e:
            print(f"[Embedder] 生成向量失败: {e}")
            return None
    
    async def embed_batch(
        self,
        texts: List[str],
    ) -> List[Optional[List[float]]]:
        """
        批量生成向量
        
        Args:
            texts: 文本列表
            
        Returns:
            向量列表（与输入顺序对应，失败的项为 None）
        """
        if not self._client:
            return [None] * len(texts)
        
        # 多模态模型：逐条调用 multimodal_embeddings
        if self._is_vision_model():
            results = []
            for text in texts:
                if text and text.strip():
                    emb = await self.embed_text(text)
                    results.append(emb)
                else:
                    results.append(None)
            return results
        
        # 文本模型：批量调用 embeddings
        valid_texts = []
        valid_indices = []
        for i, t in enumerate(texts):
            if t and t.strip():
                valid_texts.append(t.strip()[:8000])
                valid_indices.append(i)
        
        if not valid_texts:
            return [None] * len(texts)
        
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            
            kwargs = {
                "model": self.model,
                "input": valid_texts,
                "encoding_format": "float",
            }
            
            resp = await loop.run_in_executor(
                None,
                lambda: self._client.embeddings.create(**kwargs)
            )
            
            # 构建结果映射
            result = [None] * len(texts)
            for item in resp.data:
                original_idx = valid_indices[item.index]
                result[original_idx] = item.embedding
            
            return result
            
        except Exception as e:
            print(f"[Embedder] 批量生成向量失败: {e}")
            return [None] * len(texts)
    
    async def embed_multimodal(
        self,
        inputs: List[Dict[str, Any]],
        dimensions: Optional[int] = None,
    ) -> Optional[List[float]]:
        """
        生成多模态向量（支持文本、图片、视频混合输入）
        
        仅支持豆包多模态向量化模型
        
        Args:
            inputs: 输入列表，格式如下:
                - 文本: {"type": "text", "text": "文本内容"}
                - 图片URL: {"type": "image_url", "image_url": {"url": "图片URL"}}
                - 视频URL: {"type": "video_url", "video_url": {"url": "视频URL"}}
            dimensions: 向量降维后的维度（多模态模型不支持 API 降维，会手动降维）
            
        Returns:
            向量列表，如果失败返回 None
        """
        if not self._client:
            return None
        
        if not self._is_vision_model():
            print(f"[Embedder] 模型 {self.model} 不支持多模态输入")
            return None
        
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            
            kwargs = {
                "model": self.model,
                "input": inputs,
                "encoding_format": "float",
            }
            
            # 注意：多模态模型不支持 dimensions 参数，需要手动降维
            resp = await loop.run_in_executor(
                None,
                lambda: self._client.multimodal_embeddings.create(**kwargs)
            )
            
            # 多模态接口返回的 data 结构可能不同，兼容处理
            embedding = None
            data = resp.data
            if data is not None:
                # data 可能是列表或单个对象
                if isinstance(data, list):
                    if len(data) > 0:
                        item = data[0]
                        embedding = item.embedding if hasattr(item, 'embedding') else None
                else:
                    # 单个 MultimodalEmbedding 对象
                    embedding = data.embedding if hasattr(data, 'embedding') else None
            
            # 手动降维（多模态模型不支持 API 降维）
            if embedding and dimensions and len(embedding) > dimensions:
                embedding = self.slice_and_normalize(embedding, dimensions)
            
            return embedding
            
        except Exception as e:
            print(f"[Embedder] 多模态生成向量失败: {e}")
            return None
    
    async def embed_image(
        self,
        image_url: str,
        text: Optional[str] = None,
        dimensions: Optional[int] = None,
    ) -> Optional[List[float]]:
        """
        生成图片向量（可选配文本描述）
        
        Args:
            image_url: 图片 URL 或 Base64 编码
            text: 可选的文本描述
            dimensions: 向量降维后的维度
            
        Returns:
            向量列表，如果失败返回 None
        """
        inputs = []
        
        if text:
            inputs.append({"type": "text", "text": text})
        
        inputs.append({"type": "image_url", "image_url": {"url": image_url}})
        
        return await self.embed_multimodal(inputs, dimensions)
    
    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """
        计算两个向量的余弦相似度
        
        根据豆包文档，推荐使用 L2_norm 后的向量进行点积计算
        
        Args:
            vec_a: 向量 A
            vec_b: 向量 B
            
        Returns:
            相似度值 [-1, 1]
        """
        if not vec_a or not vec_b:
            return 0.0
        
        a = np.array(vec_a)
        b = np.array(vec_b)
        
        # L2 归一化
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        a_norm = a / norm_a
        b_norm = b / norm_b
        
        # 点积计算余弦相似度
        return float(np.dot(a_norm, b_norm))
    
    @staticmethod
    def euclidean_distance(vec_a: List[float], vec_b: List[float]) -> float:
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
    
    @staticmethod
    def slice_and_normalize(vec: List[float], dim: int) -> List[float]:
        """
        向量降维并归一化
        
        根据豆包文档，可以通过截取前 dim 维度并归一化来降维
        
        Args:
            vec: 原始向量
            dim: 目标维度
            
        Returns:
            降维并归一化后的向量
        """
        if not vec or len(vec) < dim:
            return vec
        
        sliced = vec[:dim]
        norm = np.linalg.norm(sliced)
        
        if norm == 0:
            return sliced
        
        return [v / norm for v in sliced]


# 全局单例
_embedder_instance: Optional[Embedder] = None


def get_embedder(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> Embedder:
    """
    获取全局 Embedder 实例
    
    Args:
        api_key: API key，None 则使用配置
        model: 模型名称，None 则使用配置
        
    Returns:
        Embedder 实例
    """
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = Embedder(
            api_key=api_key,
            model=model,
        )
    return _embedder_instance


def create_embedder(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> Embedder:
    """
    创建新的 Embedder 实例（非单例模式）
    
    Args:
        api_key: API key
        model: 模型名称
        
    Returns:
        新的 Embedder 实例
    """
    return Embedder(
        api_key=api_key,
        model=model,
    )
