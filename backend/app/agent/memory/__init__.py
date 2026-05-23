"""
记忆系统模块

分层架构：
- CoreMemory: 核心记忆（常驻上下文）
- WorkingMemory: 工作记忆（对话历史 + 摘要）
- LongTermMemory: 长期记忆（向量检索）
- MemoryExtractor: 记忆提取器
- MemoryMaintenance: 记忆维护（清理/合并/衰减）
- Embedder: 向量化服务
"""

from .embedder import Embedder
from .core_memory import CoreMemoryManager
from .working_memory import WorkingMemoryManager
from .long_term_memory import LongTermMemoryManager
from .memory_extractor import MemoryExtractor
from .memory_maintenance import MemoryMaintenance

__all__ = [
    "Embedder",
    "CoreMemoryManager",
    "WorkingMemoryManager",
    "LongTermMemoryManager",
    "MemoryExtractor",
    "MemoryMaintenance",
]
