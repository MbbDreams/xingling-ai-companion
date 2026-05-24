"""
AI Agent 模块 - 星灵 AI 伴侣核心智能系统

提供情感陪伴、长期记忆、人设成长、主动互动等能力
"""

from .companion_agent import CompanionAgent
from .models import MemoryType, MemoryEntry, RelationshipType, EmotionState
from .proactive_system import ProactiveSystem

__all__ = [
    "CompanionAgent",
    "MemoryType",
    "MemoryEntry",
    "RelationshipType",
    "EmotionState",
    "ProactiveSystem",
]
