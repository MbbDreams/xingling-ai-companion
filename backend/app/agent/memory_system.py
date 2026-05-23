"""
记忆系统 - 长期记忆存储与检索（增强版）
支持：关键词匹配 + 时间排序 + 对话历史记忆
"""
import uuid
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.entities import Memory
from .models import MemoryEntry, MemoryType


class MemorySystem:
    """
    增强版记忆系统 - 管理用户的长期记忆
    
    功能：
    1. 记忆存储（支持对话历史）
    2. 记忆检索（关键词匹配 + 时间排序）
    3. 智能记忆提取（从对话中提取关键信息）
    4. 对话历史记忆（保存完整对话片段）
    """
    
    def __init__(self, db: AsyncSession, openai_client=None):
        self.db = db
        self.openai_client = openai_client
    
    async def store_memory(self, entry: MemoryEntry) -> MemoryEntry:
        """存储记忆到数据库"""
        if not entry.id:
            entry.id = str(uuid.uuid4())
        
        now = datetime.utcnow()
        if not entry.created_at:
            entry.created_at = now
        entry.updated_at = now
        entry.last_accessed_at = now
        
        memory_entity = Memory(
            user_id=entry.user_id,
            memory=entry.content,
            category=entry.memory_type.value if entry.memory_type else "general",
            importance=entry.importance / 10.0 if entry.importance else 0.5,
            embedding=None,  # DeepSeek 不支持 embedding
        )
        
        self.db.add(memory_entity)
        await self.db.commit()
        
        return entry
    
    async def store_conversation_memory(
        self, 
        user_id: int, 
        user_message: str, 
        ai_response: str,
        topic: str = "general"
    ) -> None:
        """
        存储对话历史作为记忆
        保存用户说的话和AI的回复，方便后续引用
        """
        # 存储用户消息
        user_entry = MemoryEntry(
            user_id=user_id,
            content=f"用户说过: {user_message}",
            memory_type=MemoryType.CONVERSATION_STYLE,
            importance=3,  # 对话历史中等重要
        )
        await self.store_memory(user_entry)
        
        # 如果AI回复包含重要信息，也存储
        if len(ai_response) > 20 and not ai_response.startswith("收到"):
            ai_entry = MemoryEntry(
                user_id=user_id,
                content=f"我们聊过: {user_message[:50]}... 我回复说: {ai_response[:100]}",
                memory_type=MemoryType.EVENT,
                importance=2,
            )
            await self.store_memory(ai_entry)
    
    async def retrieve_memories(
        self,
        user_id: int,
        query: str,
        current_emotion: str = "neutral",
        conversation_context: List[Dict] = None,
        memory_type: Optional[MemoryType] = None,
        limit: int = 5,
        recency_days: int = 90  # 增加到90天，获取更多历史
    ) -> List[MemoryEntry]:
        """
        检索相关记忆 - 增强版
        
        策略：
        1. 关键词匹配（从查询中提取关键词）
        2. 时间加权（近期优先）
        3. 重要性排序
        """
        since_time = datetime.utcnow() - timedelta(days=recency_days)
        
        # 提取查询中的关键词
        keywords = self._extract_keywords(query)
        
        # 构建查询条件
        query_obj = select(Memory).where(
            and_(
                Memory.user_id == user_id,
                Memory.created_at >= since_time,
            )
        )
        
        # 关键词匹配
        if keywords:
            keyword_conditions = []
            for kw in keywords:
                keyword_conditions.append(
                    Memory.memory.ilike(f"%{kw}%")
                )
            query_obj = query_obj.where(or_(*keyword_conditions))
        
        # 类型过滤
        if memory_type:
            query_obj = query_obj.where(Memory.category == memory_type.value)
        
        # 排序：重要性降序，时间降序
        query_obj = query_obj.order_by(
            Memory.importance.desc(),
            Memory.created_at.desc()
        ).limit(limit * 2)  # 获取更多候选
        
        result = await self.db.execute(query_obj)
        
        memories = []
        for row in result.scalars():
            try:
                mem_type = MemoryType(row.category) if row.category else MemoryType.BASIC_INFO
            except ValueError:
                mem_type = MemoryType.BASIC_INFO
            
            entry = MemoryEntry(
                id=str(row.id),
                user_id=row.user_id,
                content=row.memory,
                memory_type=mem_type,
                importance=int(row.importance * 10) if row.importance else 5,
                emotion_tag=None,
                source="user_told",
                created_at=row.created_at,
                updated_at=row.updated_at,
                access_count=row.recall_count or 0,
            )
            memories.append(entry)
        
        # 如果没有关键词匹配，返回最近的记忆
        if not memories and keywords:
            # 放宽条件，只按时间排序
            query_obj = select(Memory).where(
                and_(
                    Memory.user_id == user_id,
                    Memory.created_at >= since_time,
                )
            ).order_by(Memory.created_at.desc()).limit(limit)
            
            result = await self.db.execute(query_obj)
            for row in result.scalars():
                try:
                    mem_type = MemoryType(row.category) if row.category else MemoryType.BASIC_INFO
                except ValueError:
                    mem_type = MemoryType.BASIC_INFO
                
                entry = MemoryEntry(
                    id=str(row.id),
                    user_id=row.user_id,
                    content=row.memory,
                    memory_type=mem_type,
                    importance=int(row.importance * 10) if row.importance else 5,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    access_count=row.recall_count or 0,
                )
                memories.append(entry)
        
        return memories[:limit]
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        从文本中提取关键词
        
        策略：
        1. 提取名词短语
        2. 去除停用词
        3. 保留长度>=2的词
        """
        # 常见停用词
        stop_words = {
            '的', '了', '在', '是', '我', '你', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '可以', '会', '着', '没有', '看', '好', '自己', '这', '那', '什么', '怎么', '吗', '吧', '呢', '啊', '哦', '嗯', '对', '行', '好', '是', '不是', '没有', '有', '这个', '那个', '怎么', '什么', '为什么', '吗', '呢', '吧', '啊', '哦', '嗯', '对', '行', '好', '是', '不是', '没有', '有', '这个', '那个', '怎么', '什么', '为什么',
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare', 'ought', 'used', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'and', 'but', 'if', 'or', 'because', 'until', 'while',
        }
        
        # 清理文本
        text = text.lower()
        # 提取中文字符和英文单词
        chinese_chars = re.findall(r'[\u4e00-\u9fff]{2,}', text)
        english_words = re.findall(r'[a-z]{2,}', text)
        
        keywords = []
        
        # 处理中文
        for phrase in chinese_chars:
            if phrase not in stop_words and len(phrase) >= 2:
                keywords.append(phrase)
        
        # 处理英文
        for word in english_words:
            if word not in stop_words:
                keywords.append(word)
        
        # 去重并限制数量
        unique_keywords = list(set(keywords))[:10]
        
        return unique_keywords
    
    async def extract_memories_from_conversation(
        self,
        user_id: int,
        conversation: List[Dict[str, Any]]
    ) -> List[MemoryEntry]:
        """从对话中提取新记忆 - 增强版"""
        if not self.openai_client or len(conversation) < 2:
            return []
        
        # 构建对话文本
        conversation_text = "\n".join([
            f"{'用户' if msg.get('role') == 'user' else 'AI'}: {msg.get('content', '')}"
            for msg in conversation[-6:]
        ])
        
        try:
            from langchain_core.messages import SystemMessage, HumanMessage
            
            response = await self.openai_client.ainvoke([
                SystemMessage(content=(
                    "你是一个记忆提取助手。从对话中提取用户的重要信息。\n"
                    "提取规则：\n"
                    "1. 用户的喜好（喜欢什么、不喜欢什么）\n"
                    "2. 用户的经历（做过什么、去过哪里）\n"
                    "3. 重要日期（生日、纪念日等）\n"
                    "4. 用户的情绪状态\n"
                    "5. 用户提到的人或物\n"
                    "只提取事实性信息，不要推测。\n"
                    "以 JSON 格式返回: {\"memories\": [{\"content\": \"...\", \"memory_type\": \"preference\", \"importance\": 5}]}"
                )),
                HumanMessage(content=conversation_text)
            ])
            
            import json
            result = json.loads(response.content)
            memories_data = result.get("memories", [])
            
            entries = []
            for mem_data in memories_data:
                try:
                    mem_type = MemoryType(mem_data.get("memory_type", "basic_info"))
                except ValueError:
                    mem_type = MemoryType.BASIC_INFO
                
                entry = MemoryEntry(
                    user_id=user_id,
                    content=mem_data["content"],
                    memory_type=mem_type,
                    importance=mem_data.get("importance", 5),
                    emotion_tag=mem_data.get("emotion_tag"),
                    source="ai_inferred"
                )
                entries.append(entry)
            
            return entries
            
        except Exception as e:
            print(f"记忆提取失败: {e}")
            return []
    
    async def get_memories_by_type(
        self,
        user_id: int,
        memory_type: MemoryType,
        limit: int = 10
    ) -> List[MemoryEntry]:
        """按类型获取记忆"""
        result = await self.db.execute(
            select(Memory).where(
                and_(
                    Memory.user_id == user_id,
                    Memory.category == memory_type.value
                )
            ).order_by(Memory.importance.desc()).limit(limit)
        )
        
        memories = []
        for row in result.scalars():
            try:
                mem_type = MemoryType(row.category) if row.category else MemoryType.BASIC_INFO
            except ValueError:
                mem_type = MemoryType.BASIC_INFO
            
            entry = MemoryEntry(
                id=str(row.id),
                user_id=row.user_id,
                content=row.memory,
                memory_type=mem_type,
                importance=int(row.importance * 10) if row.importance else 5,
                created_at=row.created_at,
                updated_at=row.updated_at,
                access_count=row.recall_count or 0,
            )
            memories.append(entry)
        
        return memories
    
    async def delete_memory(self, memory_id: str) -> bool:
        """删除记忆"""
        result = await self.db.execute(
            select(Memory).where(Memory.id == memory_id)
        )
        memory = result.scalar_one_or_none()
        
        if memory:
            await self.db.delete(memory)
            await self.db.commit()
            return True
        return False
    
    async def _update_access_count(self, memory_id: str):
        """更新记忆访问计数"""
        result = await self.db.execute(
            select(Memory).where(Memory.id == memory_id)
        )
        memory = result.scalar_one_or_none()
        
        if memory:
            memory.recall_count = (memory.recall_count or 0) + 1
            memory.last_recalled_at = datetime.utcnow()
            await self.db.commit()
