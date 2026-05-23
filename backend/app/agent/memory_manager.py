"""
智能记忆管理器 - 记忆提取、总结、检索

职责：
1. 从对话中智能提取记忆
2. 记忆自动分类和重要性评估
3. 记忆检索（关键词 + 时间 + 重要性）
4. 记忆定期总结和归档
"""
import re
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.entities import Memory
from .models import MemoryEntry, MemoryType


class MemoryManager:
    """
    智能记忆管理器
    
    设计原则：
    1. 记忆分层：短期记忆（对话）→ 长期记忆（总结）
    2. 自动提取：从对话中识别重要信息
    3. 智能检索：关键词 + 时间衰减 + 重要性
    4. 定期总结：压缩相似记忆，保留关键信息
    """
    
    # 记忆类型权重（用于检索排序）
    MEMORY_TYPE_WEIGHTS = {
        "preference": 1.5,      # 用户偏好最重要
        "important_date": 1.4,  # 重要日期
        "event": 1.2,           # 经历事件
        "basic_info": 1.1,      # 基本信息
        "conversation_style": 0.8,  # 对话风格
        "general": 1.0,         # 通用
    }
    
    # 时间衰减参数
    TIME_DECAY_DAYS = 30  # 30天后记忆权重开始衰减
    
    def __init__(self, db: AsyncSession, llm_client=None):
        self.db = db
        self.llm_client = llm_client
    
    async def extract_and_store_memories(
        self,
        user_id: int,
        user_message: str,
        ai_response: str
    ) -> List[MemoryEntry]:
        """
        从对话中提取并存储记忆
        
        这是核心方法，每次对话后调用
        """
        # 1. 先存储对话记录
        await self._store_conversation_record(user_id, user_message, ai_response)
        
        # 2. 智能提取重要信息
        extracted = await self._extract_important_info(user_id, user_message, ai_response)
        
        # 3. 存储提取的记忆
        for entry in extracted:
            await self._store_memory_entry(entry)
        
        return extracted
    
    async def _store_conversation_record(
        self,
        user_id: int,
        user_message: str,
        ai_response: str
    ):
        """存储对话记录作为短期记忆"""
        # 用户消息
        user_entry = MemoryEntry(
            user_id=user_id,
            content=f"用户说: {user_message}",
            memory_type=MemoryType.CONVERSATION_STYLE,
            importance=2,
        )
        await self._store_memory_entry(user_entry)
        
        # 如果是重要对话，也存储完整记录
        if self._is_important_conversation(user_message, ai_response):
            full_entry = MemoryEntry(
                user_id=user_id,
                content=f"对话记录 - 用户: {user_message[:100]}... | AI: {ai_response[:100]}...",
                memory_type=MemoryType.EVENT,
                importance=4,
            )
            await self._store_memory_entry(full_entry)
    
    def _is_important_conversation(self, user_message: str, ai_response: str) -> bool:
        """判断对话是否重要"""
        important_keywords = [
            "喜欢", "讨厌", "爱", "恨", "生日", "纪念日", "重要",
            "第一次", "最", "永远", "梦想", "目标", "计划",
            "开心", "难过", "生气", "害怕", "担心", "希望"
        ]
        
        combined = user_message + ai_response
        for kw in important_keywords:
            if kw in combined:
                return True
        return False
    
    async def _extract_important_info(
        self,
        user_id: int,
        user_message: str,
        ai_response: str
    ) -> List[MemoryEntry]:
        """使用 LLM 提取重要信息"""
        if not self.llm_client:
            return []
        
        try:
            from langchain_core.messages import SystemMessage, HumanMessage
            
            response = await self.llm_client.ainvoke([
                SystemMessage(content="""你是一个专业的记忆提取助手。从用户的消息中提取重要信息。

提取规则：
1. 用户偏好（喜欢/讨厌什么）
2. 用户经历（做过什么、去过哪里）
3. 重要日期（生日、纪念日）
4. 用户情绪状态
5. 用户提到的人名、地名

返回 JSON 格式：
{
  "memories": [
    {
      "content": "用户喜欢吃辣",
      "type": "preference",
      "importance": 5
    }
  ]
}

如果没有重要信息，返回空数组。
只返回 JSON，不要其他内容。"""),
                HumanMessage(content=f"用户消息: {user_message}")
            ])
            
            # 解析响应
            content = response.content.strip()
            # 尝试提取 JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            result = json.loads(content)
            memories_data = result.get("memories", [])
            
            entries = []
            for mem in memories_data:
                try:
                    mem_type = MemoryType(mem.get("type", "general"))
                except ValueError:
                    mem_type = MemoryType.BASIC_INFO
                
                entry = MemoryEntry(
                    user_id=user_id,
                    content=mem["content"],
                    memory_type=mem_type,
                    importance=mem.get("importance", 5),
                    source="ai_extracted"
                )
                entries.append(entry)
            
            return entries
            
        except Exception as e:
            print(f"记忆提取失败: {e}")
            return []
    
    async def _store_memory_entry(self, entry: MemoryEntry):
        """存储记忆到数据库"""
        memory = Memory(
            user_id=entry.user_id,
            memory=entry.content,
            category=entry.memory_type.value if entry.memory_type else "general",
            importance=entry.importance / 10.0 if entry.importance else 0.5,
        )
        self.db.add(memory)
        await self.db.commit()
    
    async def retrieve_relevant_memories(
        self,
        user_id: int,
        query: str,
        limit: int = 5
    ) -> List[str]:
        """
        检索相关记忆
        
        返回记忆内容列表，直接可用于 Prompt
        """
        # 提取关键词
        keywords = self._extract_keywords(query)
        
        # 构建查询
        since_time = datetime.utcnow() - timedelta(days=90)
        
        query_obj = select(Memory).where(
            and_(
                Memory.user_id == user_id,
                Memory.created_at >= since_time,
            )
        )
        
        # 关键词匹配
        if keywords:
            conditions = [Memory.memory.ilike(f"%{kw}%") for kw in keywords[:5]]
            query_obj = query_obj.where(or_(*conditions))
        
        # 排序
        query_obj = query_obj.order_by(
            Memory.importance.desc(),
            Memory.created_at.desc()
        ).limit(limit * 2)
        
        result = await self.db.execute(query_obj)
        memories = result.scalars().all()
        
        # 转换为字符串列表
        memory_texts = []
        for mem in memories[:limit]:
            memory_texts.append(mem.memory)
        
        return memory_texts
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        stop_words = {
            '的', '了', '在', '是', '我', '你', '有', '和', '就', '不',
            '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
            '可以', '会', '着', '没有', '看', '好', '自己', '这', '那',
            '什么', '怎么', '吗', '吧', '呢', '啊', '哦', '嗯',
        }
        
        # 提取中文词组
        chinese = re.findall(r'[\u4e00-\u9fff]{2,}', text.lower())
        
        keywords = [w for w in chinese if w not in stop_words]
        
        # 去重
        return list(set(keywords))[:10]
    
    async def get_user_summary(self, user_id: int) -> str:
        """
        获取用户画像摘要
        
        用于 System Prompt，让 AI 了解用户
        """
        # 获取各类记忆
        result = await self.db.execute(
            select(Memory)
            .where(Memory.user_id == user_id)
            .order_by(Memory.importance.desc())
            .limit(20)
        )
        memories = result.scalars().all()
        
        if not memories:
            return "我们刚认识，还不了解用户。"
        
        # 按类型分组
        preferences = []
        events = []
        basic_info = []
        
        for mem in memories:
            content = mem.memory
            if mem.category == "preference":
                preferences.append(content)
            elif mem.category == "event":
                events.append(content)
            elif mem.category == "basic_info":
                basic_info.append(content)
        
        # 构建摘要
        summary_parts = []
        
        if basic_info:
            summary_parts.append("基本信息: " + "；".join(basic_info[:3]))
        if preferences:
            summary_parts.append("偏好: " + "；".join(preferences[:5]))
        if events:
            summary_parts.append("经历: " + "；".join(events[:3]))
        
        return "\n".join(summary_parts) if summary_parts else "暂无详细信息。"
    
    async def summarize_old_memories(self, user_id: int) -> int:
        """
        总结旧记忆，压缩存储
        
        返回压缩的记忆数量
        """
        if not self.llm_client:
            return 0
        
        # 获取30天前的记忆
        cutoff = datetime.utcnow() - timedelta(days=30)
        
        result = await self.db.execute(
            select(Memory)
            .where(
                and_(
                    Memory.user_id == user_id,
                    Memory.created_at < cutoff,
                )
            )
            .order_by(Memory.created_at.asc())
            .limit(50)
        )
        old_memories = result.scalars().all()
        
        if len(old_memories) < 10:
            return 0
        
        # 构建总结请求
        memory_text = "\n".join([f"- {m.memory}" for m in old_memories])
        
        try:
            from langchain_core.messages import HumanMessage
            
            response = await self.llm_client.ainvoke([
                HumanMessage(content=f"""请将以下记忆总结为简洁的要点，保留最重要的信息：

{memory_text}

总结格式（每条一行）：
- [类型] 内容

只返回总结内容，不要其他文字。""")
            ])
            
            # 存储总结
            summary_entry = MemoryEntry(
                user_id=user_id,
                content=f"记忆总结: {response.content[:500]}",
                memory_type=MemoryType.BASIC_INFO,
                importance=8,
            )
            await self._store_memory_entry(summary_entry)
            
            # 删除旧记忆（可选，这里保留）
            # for mem in old_memories:
            #     await self.db.delete(mem)
            # await self.db.commit()
            
            return len(old_memories)
            
        except Exception as e:
            print(f"记忆总结失败: {e}")
            return 0
