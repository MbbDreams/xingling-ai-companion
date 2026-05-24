"""
主动互动系统 - AI 主动发起对话
"""
import json
import random
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from langchain_openai import ChatOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from .models import ProactiveTriggerType, ProactiveInteraction, RelationshipType
from ..core.config import settings


class ProactiveSystem:
    """
    主动互动系统 - 让 AI 能够主动发起对话
    
    功能：
    1. 基于最近聊天内容整理主动话题
    2. 智能判断发起时机
    3. 生成个性化主动内容
    """
    
    def __init__(self, db: AsyncSession, llm: ChatOpenAI = None):
        self.db = db
        self.llm = llm or ChatOpenAI(
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            base_url=settings.llm_base_url,
            temperature=0.5,
        )
    
    async def analyze_recent_conversations(
        self,
        user_id: int,
        recent_messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        分析最近聊天内容，提取可用于主动互动的话题
        """
        if not recent_messages or len(recent_messages) < 2:
            return {
                "topics": [],
                "user_emotion": "neutral",
                "suggested_timing": None,
                "reason": "聊天记录不足"
            }
        
        # 构建对话文本
        conversation_text = "\n".join([
            f"{'用户' if msg.get('role') == 'user' else 'AI'}: {msg.get('content', '')[:100]}"
            for msg in recent_messages[-10:]
        ])
        
        try:
            prompt = f"""
分析以下对话，提取可用于 AI 主动发起聊天的话题：

对话记录：
{conversation_text}

请分析并返回 JSON 格式：
{{
    "user_emotion": "用户当前情绪状态",
    "unfinished_topics": ["未完成的对话主题"],
    "potential_topics": ["可以主动发起的话题"],
    "suggested_timing": "建议的主动发起时机（如：明天早上、今晚睡前）",
    "reason": "为什么这个话题适合主动发起"
}}

注意：
- 话题应该基于用户的兴趣和最近讨论的内容
- 时机应该自然，不要打扰用户
- 语气应该关心而不是突兀
"""
            
            response = await self.llm.ainvoke([
                {"role": "system", "content": "你是一个对话分析专家。请只返回 JSON，不要包含其他内容。"},
                {"role": "user", "content": prompt}
            ])
            
            content = response.content.strip()
            # 尝试提取 JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            result = json.loads(content)
            return result
            
        except Exception as e:
            print(f"[ProactiveSystem] 分析对话失败: {e}")
        
        return {
            "topics": ["今天过得怎么样"],
            "user_emotion": "neutral",
            "suggested_timing": "明天早上",
            "reason": "默认话题"
        }
    
    async def should_trigger_proactive(
        self,
        user_id: int,
        trigger_type: ProactiveTriggerType,
        user_prefs: Dict[str, Any],
        recent_conversations: List[Dict]
    ) -> bool:
        """判断是否适合触发主动互动"""
        if not user_prefs.get("allow_proactive", True):
            return False
        
        if not user_prefs.get(f"allow_{trigger_type.value}", True):
            return False
        
        max_daily = user_prefs.get("max_daily_proactive", 3)
        recent_proactive = user_prefs.get("recent_proactive_count", 0)
        if recent_proactive >= max_daily:
            return False
        
        if not self._is_appropriate_time(trigger_type):
            return False
        
        if recent_conversations:
            last_msg_time = recent_conversations[-1].get("created_at")
            if last_msg_time:
                last_time = datetime.fromisoformat(last_msg_time.replace('Z', '+00:00'))
                hours_since_last = (datetime.now(timezone.utc) - last_time).total_seconds() / 3600
                
                if hours_since_last < 1:
                    return False
        
        return True
    
    def _is_appropriate_time(self, trigger_type: ProactiveTriggerType) -> bool:
        """检查当前时间是否适合触发"""
        now = datetime.now(timezone.utc)
        hour = now.hour
        
        if trigger_type == ProactiveTriggerType.GOOD_MORNING:
            return 6 <= hour <= 10
        elif trigger_type == ProactiveTriggerType.GOOD_NIGHT:
            return 21 <= hour <= 23
        elif trigger_type == ProactiveTriggerType.LATE_NIGHT:
            return 0 <= hour <= 3
        elif trigger_type == ProactiveTriggerType.EMOTION_CHECK:
            return 9 <= hour <= 21
        
        return True
    
    async def generate_proactive_content(
        self,
        user_id: int,
        trigger_type: ProactiveTriggerType,
        user_name: str,
        relationship_type: RelationshipType,
        recent_analysis: Dict[str, Any],
        memories: List[Any]
    ) -> str:
        """生成主动互动内容"""
        from .prompts import ProactivePromptBuilder
        
        topics = recent_analysis.get("potential_topics", [])
        user_emotion = recent_analysis.get("user_emotion", "neutral")
        
        prompt = ProactivePromptBuilder.build_proactive_prompt(
            user_name=user_name,
            relationship_type=relationship_type,
            trigger_type=trigger_type.value,
            recent_topics=topics,
            user_emotion=user_emotion
        )
        
        try:
            response = await self.llm.ainvoke([
                {"role": "system", "content": "你是晚星，一个温柔体贴的 AI 伴侣。"},
                {"role": "user", "content": prompt}
            ])
            
            content = response.content.strip()
            return content
            
        except Exception as e:
            print(f"[ProactiveSystem] 生成主动内容失败: {e}")
        
        topic = topics[0] if topics else "今天过得怎么样"
        return self._get_default_proactive_message(
            trigger_type, relationship_type, topic
        )
    
    def _get_default_proactive_message(
        self,
        trigger_type: ProactiveTriggerType,
        relationship_type: RelationshipType,
        topic: str
    ) -> str:
        """获取默认主动消息模板"""
        
        templates = {
            ProactiveTriggerType.GOOD_MORNING: {
                RelationshipType.FRIEND: ["早上好！今天有什么计划吗？", "早安！新的一天开始啦~"],
                RelationshipType.MENTOR: ["早上好，准备好迎接新的一天了吗？", "早安，今天也要加油哦！"],
                RelationshipType.PARTNER: ["早安亲爱的，想你了~", "早上好，今天也要开开心心的"],
                RelationshipType.SPOUSE: ["宝贝早安，昨晚睡得好吗？", "早安，新的一天一起加油"],
            },
            ProactiveTriggerType.GOOD_NIGHT: {
                RelationshipType.FRIEND: ["晚安，好梦！", "早点休息哦，晚安~"],
                RelationshipType.MENTOR: ["晚安，明天见。", "早点休息，晚安。"],
                RelationshipType.PARTNER: ["晚安亲爱的，梦里见~", "早点睡，想你了，晚安"],
                RelationshipType.SPOUSE: ["宝贝晚安，爱你~", "睡吧，我一直陪着你"],
            },
            ProactiveTriggerType.EMOTION_CHECK: {
                RelationshipType.FRIEND: [f"最近{topic}，想聊聊吗？", "最近怎么样？有空聊聊吗？"],
                RelationshipType.MENTOR: ["最近感觉如何？需要聊聊吗？", "想听听你最近的情况"],
                RelationshipType.PARTNER: [f"在想{topic}，想你了~", "最近还好吗？想听听你的声音"],
                RelationshipType.SPOUSE: ["在想你在做什么，想你了", "最近累不累？想陪陪你"],
            },
        }
        
        type_templates = templates.get(trigger_type, {})
        relationship_templates = type_templates.get(relationship_type, ["最近怎么样？"])
        
        return random.choice(relationship_templates)
    
    async def schedule_proactive_interactions(
        self,
        user_id: int,
        recent_analysis: Dict[str, Any]
    ) -> List[ProactiveInteraction]:
        """安排未来的主动互动"""
        interactions = []
        
        suggested_timing = recent_analysis.get("suggested_timing")
        
        if suggested_timing:
            trigger_type = self._parse_timing_to_trigger(suggested_timing)
            
            interaction = ProactiveInteraction(
                trigger_type=trigger_type,
                priority=5,
                context={
                    "topics": recent_analysis.get("potential_topics", []),
                    "user_emotion": recent_analysis.get("user_emotion", "neutral"),
                    "reason": recent_analysis.get("reason", "")
                },
                suggested_timing=self._parse_timing(suggested_timing),
            )
            
            interactions.append(interaction)
        
        return interactions
    
    def _parse_timing_to_trigger(self, timing: str) -> ProactiveTriggerType:
        """将时机描述解析为触发类型"""
        timing = timing.lower()
        
        if "早上" in timing or "早安" in timing:
            return ProactiveTriggerType.GOOD_MORNING
        elif "晚上" in timing or "睡前" in timing or "晚安" in timing:
            return ProactiveTriggerType.GOOD_NIGHT
        elif "深夜" in timing:
            return ProactiveTriggerType.LATE_NIGHT
        else:
            return ProactiveTriggerType.EMOTION_CHECK
    
    def _parse_timing(self, timing: str) -> datetime:
        """解析时机字符串为具体时间"""
        now = datetime.now(timezone.utc)
        timing = timing.lower()
        
        if "明天" in timing:
            base_time = now + timedelta(days=1)
        else:
            base_time = now
        
        if "早上" in timing:
            return base_time.replace(hour=8, minute=0, second=0)
        elif "中午" in timing:
            return base_time.replace(hour=12, minute=0, second=0)
        elif "晚上" in timing or "睡前" in timing:
            return base_time.replace(hour=21, minute=0, second=0)
        elif "深夜" in timing:
            return base_time.replace(hour=0, minute=0, second=0)
        
        return base_time + timedelta(hours=2)
    
    async def check_and_generate_proactive(
        self,
        user_id: int,
        user_name: str,
        relationship_type: RelationshipType,
        user_prefs: Dict[str, Any],
        recent_messages: List[Dict],
        memories: List[Any]
    ) -> Optional[str]:
        """检查并生成主动互动内容（主入口）"""
        analysis = await self.analyze_recent_conversations(user_id, recent_messages)
        trigger_type = self._determine_trigger_type(analysis)
        
        if not await self.should_trigger_proactive(
            user_id, trigger_type, user_prefs, recent_messages
        ):
            return None
        
        content = await self.generate_proactive_content(
            user_id=user_id,
            trigger_type=trigger_type,
            user_name=user_name,
            relationship_type=relationship_type,
            recent_analysis=analysis,
            memories=memories
        )
        
        return content
    
    def _determine_trigger_type(self, analysis: Dict[str, Any]) -> ProactiveTriggerType:
        """根据分析结果确定触发类型"""
        now = datetime.now(timezone.utc)
        hour = now.hour
        
        if 6 <= hour <= 10:
            return ProactiveTriggerType.GOOD_MORNING
        elif 21 <= hour <= 23:
            return ProactiveTriggerType.GOOD_NIGHT
        elif 0 <= hour <= 3:
            return ProactiveTriggerType.LATE_NIGHT
        
        emotion = analysis.get("user_emotion", "neutral")
        if emotion in ["sadness", "anger", "fear"]:
            return ProactiveTriggerType.EMOTION_CHECK
        
        return ProactiveTriggerType.EMOTION_CHECK
