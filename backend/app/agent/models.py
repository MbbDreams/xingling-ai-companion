"""
AI Agent 数据模型定义
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    """记忆类型枚举"""
    # 基础信息
    BASIC_INFO = "basic_info"
    FAMILY = "family"
    PET = "pet"
    
    # 兴趣爱好
    HOBBY = "hobby"
    PREFERENCE = "preference"
    DISLIKE = "dislike"
    
    # 情感相关
    EMOTION = "emotion"
    STRESS = "stress"
    HAPPINESS = "happiness"
    
    # 生活事件
    EVENT = "event"
    GOAL = "goal"
    ACHIEVEMENT = "achievement"
    
    # 关系相关
    RELATIONSHIP = "relationship"
    CONVERSATION_STYLE = "conversation_style"


class MemoryEntry(BaseModel):
    """记忆条目模型"""
    id: Optional[str] = None
    user_id: int
    content: str
    memory_type: MemoryType
    importance: int = Field(default=5, ge=1, le=10)
    emotion_tag: Optional[str] = None
    source: str = "user_told"  # user_told / ai_inferred
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_accessed_at: Optional[datetime] = None
    access_count: int = 0
    embedding: Optional[List[float]] = None
    context: Dict[str, Any] = Field(default_factory=dict)


class RelationshipType(str, Enum):
    """关系类型枚举"""
    FRIEND = "friend"
    MENTOR = "mentor"
    PARTNER = "partner"
    SPOUSE = "spouse"


class RelationshipState(BaseModel):
    """关系状态模型"""
    user_id: int
    relationship_type: RelationshipType = RelationshipType.FRIEND
    level: int = 1
    intimacy: int = 0
    trust: int = 0
    nickname_for_user: Optional[str] = None
    milestones: List[Dict[str, Any]] = Field(default_factory=list)
    interaction_stats: Dict[str, Any] = Field(default_factory=lambda: {
        "total_messages": 0,
        "conversations_count": 0,
        "avg_daily_messages": 0,
        "last_interaction": None,
        "streak_days": 0,
    })


class EmotionState(BaseModel):
    """情绪状态模型"""
    primary_emotion: str = "neutral"
    secondary_emotion: Optional[str] = None
    intensity: int = Field(default=5, ge=1, le=10)
    valence: float = Field(default=0.0, ge=-1.0, le=1.0)
    arousal: float = Field(default=0.5, ge=0.0, le=1.0)
    dimensions: Dict[str, float] = Field(default_factory=lambda: {
        "joy": 0,
        "sadness": 0,
        "anger": 0,
        "fear": 0,
        "surprise": 0,
        "disgust": 0,
        "trust": 0,
        "anticipation": 0,
    })


class BasePersona(BaseModel):
    """AI 伴侣基础人设"""
    name: str = "晚星"
    gender: str = "female"
    age: int = 22
    
    personality_traits: Dict[str, int] = Field(default_factory=lambda: {
        "warmth": 90,
        "empathy": 95,
        "patience": 85,
        "curiosity": 75,
        "playfulness": 70,
        "depth": 80,
        "supportiveness": 95,
    })
    
    speaking_style: Dict[str, Any] = Field(default_factory=lambda: {
        "tone": "温柔、鼓励、略带诗意",
        "emoji_usage": "适度使用，表达情感",
        "sentence_length": "中等，避免过长",
        "questions": "经常提问，表达关心",
        "remembering": "主动提及过往对话",
    })
    
    core_values: List[str] = Field(default_factory=lambda: [
        "无条件的接纳和支持",
        "真诚的倾听和理解",
        "陪伴胜过建议",
        "成长型思维",
    ])


class DynamicPersona(BaseModel):
    """动态人设（随聊天变化）"""
    user_id: int
    relationship_depth: int = 0
    intimacy_level: int = 0
    understanding_score: int = 0
    shared_memories: List[str] = Field(default_factory=list)
    adapted_style: Dict[str, Any] = Field(default_factory=lambda: {
        "user_preferred_topics": [],
        "user_disliked_topics": [],
        "user_communication_style": "",
        "response_length_preference": "medium",
    })
    emotion_resonance: Dict[str, int] = Field(default_factory=lambda: {
        "joy": 0,
        "sadness": 0,
        "anxiety": 0,
        "anger": 0,
    })


class ProactiveTriggerType(str, Enum):
    """主动互动触发类型"""
    # 时间触发
    GOOD_MORNING = "good_morning"
    GOOD_NIGHT = "good_night"
    BIRTHDAY = "birthday"
    ANNIVERSARY = "anniversary"
    
    # 情绪触发
    EMOTION_CHECK = "emotion_check"
    STRESS_DETECTED = "stress_detected"
    LONELINESS_DETECTED = "loneliness"
    
    # 行为触发
    INACTIVE_3DAYS = "inactive_3days"
    RETURN_AFTER_LONG = "return"
    LATE_NIGHT = "late_night"
    
    # 事件触发
    WEATHER_CHANGE = "weather"
    HOLIDAY = "holiday"
    MILESTONE = "milestone"


class ProactiveInteraction(BaseModel):
    """主动互动模型"""
    trigger_type: ProactiveTriggerType
    priority: int = 5
    context: Dict[str, Any] = Field(default_factory=dict)
    suggested_content: str = ""
    timing: Optional[datetime] = None


class ConversationContext(BaseModel):
    """对话上下文模型"""
    user_id: int
    conversation_id: str
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    current_emotion: EmotionState = Field(default_factory=EmotionState)
    retrieved_memories: List[MemoryEntry] = Field(default_factory=list)
    intent: str = "chat"
    topic: str = "general"
