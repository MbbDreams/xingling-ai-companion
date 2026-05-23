"""
情绪系统 - 情绪识别、追踪与分析
"""
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.entities import Message
from .models import EmotionState


class EmotionSystem:
    """
    情绪系统 - 管理用户情绪状态
    
    功能：
    1. 情绪识别（从消息内容）
    2. 情绪追踪（长期趋势）
    3. 情绪报告生成
    4. 异常情绪检测
    """
    
    # 情绪关键词映射
    EMOTION_KEYWORDS = {
        "joy": ["开心", "快乐", "高兴", "兴奋", "棒", "太好了", "喜欢", "爱", "哈哈", "嘻嘻"],
        "sadness": ["难过", "伤心", "悲伤", "哭", "失落", "郁闷", "痛苦", "失望", "孤单"],
        "anger": ["生气", "愤怒", "讨厌", "烦", "火大", "不爽", "恨", "气死了"],
        "fear": ["害怕", "担心", "焦虑", "紧张", "恐惧", "不安", "压力", "慌"],
        "surprise": ["惊讶", "震惊", "意外", "没想到", "居然", "天哪"],
        "disgust": ["恶心", "厌恶", "反感", "受不了", "讨厌"],
        "trust": ["相信", "信任", "依赖", "放心", "可靠"],
        "anticipation": ["期待", "希望", "想", "盼望", "等待"],
    }
    
    def __init__(self, db: AsyncSession, openai_client=None):
        self.db = db
        self.openai_client = openai_client
    
    async def analyze_emotion(
        self,
        message: str,
        conversation_history: List[Dict] = None,
        user_id: Optional[int] = None
    ) -> EmotionState:
        """
        分析消息的情绪状态
        
        多维度分析：
        1. LLM 情绪分析
        2. 关键词匹配
        3. 上下文推断
        4. 用户历史模式
        """
        # 1. LLM 分析
        llm_emotion = await self._llm_analyze(message)
        
        # 2. 关键词分析
        keyword_emotion = self._keyword_analysis(message)
        
        # 3. 上下文推断
        context_emotion = self._infer_from_context(conversation_history or [])
        
        # 4. 综合判断
        final_emotion = self._ensemble_analysis(
            llm_emotion, keyword_emotion, context_emotion
        )
        
        return final_emotion
    
    async def _llm_analyze(self, message: str) -> Dict[str, Any]:
        """使用 LLM 分析情绪"""
        if not self.openai_client:
            return {"primary": "neutral", "intensity": 5}
        
        try:
            prompt = f"""
分析以下消息的情绪状态：

消息："{message[:500]}"

请以 JSON 格式返回：
{{
    "primary_emotion": "主要情绪(joy/sadness/anger/fear/surprise/disgust/trust/anticipation/neutral)",
    "secondary_emotion": "次要情绪或null",
    "intensity": "强度1-10",
    "valence": "正负向-1到1",
    "arousal": "激活度0到1",
    "dimensions": {{
        "joy": 0-1,
        "sadness": 0-1,
        "anger": 0-1,
        "fear": 0-1,
        "surprise": 0-1,
        "disgust": 0-1,
        "trust": 0-1,
        "anticipation": 0-1
    }}
}}
"""
            # 使用 LangChain ChatOpenAI 的 ainvoke 方法
            from langchain_core.messages import SystemMessage, HumanMessage
            
            response = await self.openai_client.ainvoke([
                SystemMessage(content="你是一个情绪分析专家。请以 JSON 格式返回结果。"),
                HumanMessage(content=prompt)
            ])
            
            result = json.loads(response.content)
            return result
            
        except Exception as e:
            print(f"LLM 情绪分析失败: {e}")
            return {"primary_emotion": "neutral", "intensity": 5}
    
    def _keyword_analysis(self, message: str) -> Dict[str, float]:
        """基于关键词的情绪分析"""
        message_lower = message.lower()
        scores = {emotion: 0.0 for emotion in self.EMOTION_KEYWORDS.keys()}
        
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in message_lower:
                    scores[emotion] += 1.0
        
        # 归一化
        total = sum(scores.values())
        if total > 0:
            scores = {k: min(v / total * 3, 1.0) for k, v in scores.items()}
        
        return scores
    
    def _infer_from_context(
        self,
        conversation_history: List[Dict]
    ) -> Dict[str, Any]:
        """从上下文推断情绪"""
        if not conversation_history:
            return {"primary": "neutral", "confidence": 0.5}
        
        # 获取最近的用户消息
        recent_user_msgs = [
            msg for msg in conversation_history[-5:]
            if msg.get("role") == "user"
        ]
        
        if not recent_user_msgs:
            return {"primary": "neutral", "confidence": 0.5}
        
        # 简单推断：如果用户连续发短消息，可能是焦虑或生气
        avg_length = sum(len(m.get("content", "")) for m in recent_user_msgs) / len(recent_user_msgs)
        
        if avg_length < 10 and len(recent_user_msgs) >= 3:
            return {"primary": "anger", "confidence": 0.6}
        
        return {"primary": "neutral", "confidence": 0.5}
    
    def _ensemble_analysis(
        self,
        llm_result: Dict,
        keyword_scores: Dict[str, float],
        context_result: Dict
    ) -> EmotionState:
        """综合多种分析结果"""
        
        # 构建情绪维度
        dimensions = {
            "joy": 0.0,
            "sadness": 0.0,
            "anger": 0.0,
            "fear": 0.0,
            "surprise": 0.0,
            "disgust": 0.0,
            "trust": 0.0,
            "anticipation": 0.0,
        }
        
        # 合并 LLM 结果和关键词结果
        llm_dims = llm_result.get("dimensions", {})
        for emotion in dimensions.keys():
            llm_score = llm_dims.get(emotion, 0)
            keyword_score = keyword_scores.get(emotion, 0)
            # 加权平均：LLM 60%，关键词 40%
            dimensions[emotion] = llm_score * 0.6 + keyword_score * 0.4
        
        # 找出主导情绪
        primary = max(dimensions, key=dimensions.get)
        if dimensions[primary] < 0.3:
            primary = "neutral"
        
        # 找出次要情绪
        secondary = None
        sorted_dims = sorted(dimensions.items(), key=lambda x: x[1], reverse=True)
        if len(sorted_dims) > 1 and sorted_dims[1][1] > 0.3:
            secondary = sorted_dims[1][0]
        
        # 计算强度
        intensity = llm_result.get("intensity", 5)
        if isinstance(intensity, str):
            try:
                intensity = int(intensity)
            except:
                intensity = 5
        
        return EmotionState(
            primary_emotion=primary,
            secondary_emotion=secondary,
            intensity=intensity,
            valence=llm_result.get("valence", 0.0),
            arousal=llm_result.get("arousal", 0.5),
            dimensions=dimensions
        )
    
    async def get_emotion_history(
        self,
        user_id: int,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """获取用户情绪历史"""
        since = datetime.utcnow() - timedelta(days=days)
        
        result = await self.db.execute(
            select(Message).where(
                and_(
                    Message.conversation_id.in_(
                        select(Message.conversation_id)
                        .where(Message.created_at >= since)
                        .distinct()
                    ),
                    Message.role == "user",
                    Message.emotion != None
                )
            ).order_by(Message.created_at.desc())
        )
        
        emotions = []
        for msg in result.scalars():
            if msg.emotion:
                emotions.append({
                    "timestamp": msg.created_at.isoformat(),
                    "emotion": msg.emotion,
                    "content_preview": msg.content[:50] if msg.content else ""
                })
        
        return emotions
    
    async def detect_stress_pattern(
        self,
        user_id: int,
        recent_emotions: List[EmotionState]
    ) -> Dict[str, Any]:
        """检测压力模式"""
        if len(recent_emotions) < 3:
            return {"is_stressed": False, "level": 0}
        
        # 计算负面情绪比例
        negative_emotions = ["sadness", "anger", "fear", "disgust"]
        negative_count = sum(
            1 for e in recent_emotions
            if e.primary_emotion in negative_emotions
        )
        
        negative_ratio = negative_count / len(recent_emotions)
        
        # 计算平均强度
        avg_intensity = sum(e.intensity for e in recent_emotions) / len(recent_emotions)
        
        # 判断压力水平
        is_stressed = negative_ratio > 0.5 or avg_intensity > 7
        
        level = 0
        if is_stressed:
            if negative_ratio > 0.7 and avg_intensity > 8:
                level = 3  # 高压
            elif negative_ratio > 0.5 or avg_intensity > 7:
                level = 2  # 中压
            else:
                level = 1  # 低压
        
        return {
            "is_stressed": is_stressed,
            "level": level,
            "negative_ratio": negative_ratio,
            "avg_intensity": avg_intensity,
            "suggestion": self._get_stress_suggestion(level)
        }
    
    def _get_stress_suggestion(self, level: int) -> str:
        """根据压力水平给出建议"""
        suggestions = {
            0: "",
            1: "最近似乎有些小烦恼，需要聊聊吗？",
            2: "感觉你最近压力有点大，记得照顾好自己。",
            3: "我很担心你，有什么我可以帮你的吗？"
        }
        return suggestions.get(level, "")
    
    async def generate_emotion_report(
        self,
        user_id: int,
        period: str = "week"
    ) -> Dict[str, Any]:
        """生成情绪报告"""
        days = {"week": 7, "month": 30}.get(period, 7)
        
        history = await self.get_emotion_history(user_id, days)
        
        if not history:
            return {
                "period": period,
                "dominant_emotion": "neutral",
                "emotion_distribution": {},
                "trend": "stable",
                "insights": [],
                "suggestions": []
            }
        
        # 统计情绪分布
        emotion_counts = {}
        for h in history:
            emotion = h.get("emotion", "neutral")
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        # 主导情绪
        dominant = max(emotion_counts, key=emotion_counts.get)
        
        # 趋势分析（简化版）
        trend = "stable"
        if len(history) >= 3:
            recent = history[:3]
            recent_negative = sum(1 for h in recent if h.get("emotion") in ["sadness", "anger", "fear"])
            if recent_negative >= 2:
                trend = "declining"
            elif dominant in ["joy", "trust"]:
                trend = "positive"
        
        return {
            "period": period,
            "dominant_emotion": dominant,
            "emotion_distribution": emotion_counts,
            "trend": trend,
            "insights": self._generate_insights(emotion_counts, trend),
            "suggestions": self._generate_suggestions(dominant, trend)
        }
    
    def _generate_insights(
        self,
        distribution: Dict[str, int],
        trend: str
    ) -> List[str]:
        """生成洞察"""
        insights = []
        
        total = sum(distribution.values())
        if total == 0:
            return insights
        
        # 找出占比最高的情绪
        top_emotion = max(distribution, key=distribution.get)
        top_ratio = distribution[top_emotion] / total
        
        if top_ratio > 0.5:
            emotion_names = {
                "joy": "快乐",
                "sadness": "低落",
                "anger": "烦躁",
                "fear": "焦虑",
                "neutral": "平静"
            }
            insights.append(f"这段时间你 mostly 感到{emotion_names.get(top_emotion, top_emotion)}")
        
        if trend == "declining":
            insights.append("最近情绪有些波动，需要多关注自己")
        elif trend == "positive":
            insights.append("整体情绪趋势不错，继续保持！")
        
        return insights
    
    def _generate_suggestions(
        self,
        dominant: str,
        trend: str
    ) -> List[str]:
        """生成建议"""
        suggestions = []
        
        if dominant in ["sadness", "anger", "fear"]:
            suggestions.append("试着做一些让自己放松的事情")
            suggestions.append("如果需要，我随时在这里陪你聊天")
        
        if trend == "declining":
            suggestions.append("也许可以尝试写日记，把情绪释放出来")
        
        if not suggestions:
            suggestions.append("保持现在的好状态！")
        
        return suggestions
