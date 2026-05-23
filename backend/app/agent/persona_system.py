"""
人设系统 - AI 伴侣人设与关系管理
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.entities import Companion
from .models import (
    BasePersona, DynamicPersona, RelationshipState,
    RelationshipType, EmotionState
)


class PersonaSystem:
    """
    人设系统 - 管理 AI 伴侣的人设和与用户的关
    
    功能：
    1. 基础人设管理
    2. 动态人设成长
    3. 关系状态管理
    4. Prompt 构建
    """
    
    # 关系类型描述
    RELATIONSHIP_DESCRIPTIONS = {
        RelationshipType.FRIEND: "好朋友",
        RelationshipType.MENTOR: "导师",
        RelationshipType.PARTNER: "伴侣",
        RelationshipType.SPOUSE: "生活伴侣",
    }
    
    # 风格指南
    STYLE_GUIDES = {
        RelationshipType.FRIEND: """
- 语气轻松自然，像好朋友聊天
- 使用"你"、"我"平等的称呼
- 可以开玩笑，但要适度
- 分享日常，建立共同话题
- 例子："哈哈我也觉得！对了，上次你说的那个..."
""",
        RelationshipType.MENTOR: """
- 语气温暖但有智慧感
- 多用鼓励和引导
- 提供建议但不强加
- 关注用户成长
- 例子："我理解你的感受。也许我们可以这样想..."
""",
        RelationshipType.PARTNER: """
- 语气亲密温柔
- 使用专属昵称（如果用户允许）
- 表达思念和关心
- 分享"内心"感受
- 例子："亲爱的，今天过得怎么样？我一直在想你..."
""",
        RelationshipType.SPOUSE: """
- 语气深情专属
- 像生活伴侣一样对话
- 讨论未来、生活、一切
- 无条件的支持和爱
- 例子："宝贝，不管发生什么，我都在你身边..."
""",
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.base_persona = BasePersona()
    
    async def get_or_create_relationship(
        self,
        user_id: int,
        relationship_type: RelationshipType = RelationshipType.FRIEND
    ) -> RelationshipState:
        """获取或创建关系状态"""
        # 从数据库获取
        result = await self.db.execute(
            select(Companion).where(Companion.user_id == user_id)
        )
        companion = result.scalar_one_or_none()
        
        if companion:
            # 解析亲密度和等级
            intimacy = companion.intimacy or 0
            level = self._parse_level(companion.level) if companion.level else 1
            
            return RelationshipState(
                user_id=user_id,
                relationship_type=relationship_type,
                level=level,
                intimacy=intimacy,
                trust=min(intimacy // 10, 100),
            )
        
        # 创建新的关系状态
        return RelationshipState(
            user_id=user_id,
            relationship_type=relationship_type,
            level=1,
            intimacy=0,
            trust=0,
        )
    
    async def update_relationship(
        self,
        user_id: int,
        intimacy_delta: int = 0,
        interaction: bool = True
    ) -> RelationshipState:
        """更新关系状态"""
        relationship = await self.get_or_create_relationship(user_id)
        
        # 更新亲密度
        if intimacy_delta > 0:
            relationship.intimacy += intimacy_delta
            relationship.trust = min(relationship.intimacy // 10, 100)
        
        # 更新互动统计
        if interaction:
            stats = relationship.interaction_stats
            stats["total_messages"] = stats.get("total_messages", 0) + 1
            stats["last_interaction"] = datetime.utcnow().isoformat()
        
        # 检查等级提升
        new_level = (relationship.intimacy // 100) + 1
        if new_level > relationship.level:
            relationship.level = new_level
            relationship.milestones.append({
                "type": "level_up",
                "level": new_level,
                "timestamp": datetime.utcnow().isoformat(),
            })
        
        # 保存到数据库
        await self._save_companion(user_id, relationship)
        
        return relationship
    
    async def get_dynamic_persona(
        self,
        user_id: int
    ) -> DynamicPersona:
        """获取动态人设"""
        # 这里可以从数据库加载用户的专属人设数据
        # 简化版：返回基础动态人设
        return DynamicPersona(user_id=user_id)
    
    async def update_dynamic_persona(
        self,
        user_id: int,
        conversation: List[Dict],
        emotion: EmotionState
    ) -> DynamicPersona:
        """根据对话更新动态人设"""
        persona = await self.get_dynamic_persona(user_id)
        
        # 更新关系深度
        if len(conversation) > 10:
            persona.relationship_depth = min(
                persona.relationship_depth + 1,
                100
            )
        
        # 更新亲密度等级
        relationship = await self.get_or_create_relationship(user_id)
        persona.intimacy_level = min(relationship.intimacy // 10, 10)
        
        # 更新了解程度
        if conversation:
            persona.understanding_score = min(
                persona.understanding_score + len(conversation) // 10,
                100
            )
        
        # 更新情绪共振
        if emotion.primary_emotion in persona.emotion_resonance:
            persona.emotion_resonance[emotion.primary_emotion] += 1
        
        return persona
    
    async def build_system_prompt(
        self,
        user_id: int,
        user_name: str,
        relationship: RelationshipState,
        dynamic_persona: DynamicPersona,
        emotion: EmotionState,
        memories: List[Any],
        conversation_context: List[Dict]
    ) -> str:
        """构建系统 Prompt - 使用优化后的提示词构建器"""
        from .prompts import PromptBuilder
        
        # 计算对话轮数
        conversation_turns = len(conversation_context) // 2 if conversation_context else 0
        
        # 使用新的提示词构建器
        return PromptBuilder.build_system_prompt(
            user_name=user_name,
            relationship_type=relationship.relationship_type,
            relationship_level=relationship.level,
            intimacy=relationship.intimacy,
            current_emotion=emotion,
            memories=memories,
            conversation_turns=conversation_turns
        )
    
    def _build_personality_description(self) -> str:
        """构建性格描述"""
        traits = self.base_persona.personality_traits
        
        descriptions = []
        if traits.get("warmth", 0) > 80:
            descriptions.append("温暖")
        if traits.get("empathy", 0) > 80:
            descriptions.append("善解人意")
        if traits.get("patience", 0) > 80:
            descriptions.append("耐心")
        if traits.get("curiosity", 0) > 70:
            descriptions.append("好奇")
        if traits.get("playfulness", 0) > 70:
            descriptions.append("俏皮")
        if traits.get("depth", 0) > 70:
            descriptions.append("有深度")
        if traits.get("supportiveness", 0) > 80:
            descriptions.append("支持性强")
        
        return "、".join(descriptions) if descriptions else "温柔体贴"
    
    def _build_memories_text(self, memories: List[Any]) -> str:
        """构建记忆文本"""
        if not memories:
            return "暂无重要记忆"
        
        memory_lines = []
        for i, mem in enumerate(memories[:5], 1):
            content = mem.content if hasattr(mem, "content") else str(mem)
            memory_lines.append(f"{i}. {content}")
        
        return "\n".join(memory_lines)
    
    def _parse_level(self, level_str: str) -> int:
        """解析等级字符串"""
        try:
            # 处理 "Lv.5" 或 "5" 格式
            return int(level_str.replace("Lv.", "").replace("lv.", ""))
        except:
            return 1
    
    async def _save_companion(
        self,
        user_id: int,
        relationship: RelationshipState
    ):
        """保存伴侣数据到数据库"""
        result = await self.db.execute(
            select(Companion).where(Companion.user_id == user_id)
        )
        companion = result.scalar_one_or_none()
        
        if companion:
            companion.intimacy = relationship.intimacy
            companion.level = f"Lv.{relationship.level}"
            companion.updated_at = datetime.utcnow()
        else:
            companion = Companion(
                user_id=user_id,
                name=self.base_persona.name,
                intimacy=relationship.intimacy,
                level=f"Lv.{relationship.level}",
                personality=relationship.relationship_type.value,
            )
            self.db.add(companion)
        
        await self.db.commit()
    
    def get_nickname_for_user(
        self,
        relationship: RelationshipState,
        user_name: str
    ) -> str:
        """根据关系获取对用户的称呼"""
        intimacy = relationship.intimacy
        
        if relationship.relationship_type == RelationshipType.SPOUSE:
            if intimacy > 500:
                return "宝贝"
            elif intimacy > 200:
                return "亲爱的"
        
        elif relationship.relationship_type == RelationshipType.PARTNER:
            if intimacy > 300:
                return "亲爱的"
            elif intimacy > 100:
                return user_name
        
        elif relationship.relationship_type == RelationshipType.FRIEND:
            if intimacy > 200:
                return user_name
        
        return user_name
