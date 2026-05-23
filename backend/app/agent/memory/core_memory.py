"""
核心记忆管理器 - Core Memory Manager

管理常驻上下文的结构化记忆块，参考 MemGPT/Letta 的 Core Memory 概念。
三个文本块合计控制在 ~500 tokens 以内：
- persona_block: 角色设定（静态，初始化时写入）
- human_block: 用户画像摘要（动态，定期更新）
- relationship_block: 关系状态摘要（动态，定期更新）
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.models import Companion
from app.agent.prompts import PromptBuilder


class CoreMemory(BaseModel):
    """核心记忆数据结构"""
    user_id: int
    companion_id: int
    persona_block: str = ""       # 角色设定
    human_block: str = ""         # 用户画像摘要
    relationship_block: str = ""  # 关系状态摘要
    last_updated_at: Optional[datetime] = None


class CoreMemoryManager:
    """核心记忆管理器"""
    
    # Token 预算
    MAX_HUMAN_BLOCK_TOKENS = 150
    MAX_RELATIONSHIP_BLOCK_TOKENS = 100
    
    def __init__(self, session: AsyncSession, llm=None):
        """
        初始化核心记忆管理器
        
        Args:
            session: 数据库会话
            llm: LLM 实例（用于生成摘要）
        """
        self.session = session
        self.llm = llm
        self._cache: dict[int, CoreMemory] = {}  # 内存缓存
    
    async def initialize(self, user_id: int, companion_id: int) -> CoreMemory:
        """
        初始化核心记忆（首次使用时调用）
        
        Args:
            user_id: 用户 ID
            companion_id: 伴侣 ID
            
        Returns:
            初始化后的核心记忆
        """
        # 检查是否已存在
        existing = await self._get_from_db(user_id, companion_id)
        if existing:
            self._cache[(user_id, companion_id)] = existing
            return existing
        
        # 创建新的核心记忆
        core_memory = CoreMemory(
            user_id=user_id,
            companion_id=companion_id,
            persona_block=self._get_default_persona(),
            human_block="",
            relationship_block="我们刚刚认识，正在建立友谊。",
            last_updated_at=datetime.now(timezone.utc),
        )
        
        # 写入数据库
        await self._save_to_db(core_memory)
        self._cache[(user_id, companion_id)] = core_memory
        
        return core_memory
    
    async def get_core_memory(self, user_id: int, companion_id: int) -> CoreMemory:
        """
        获取核心记忆
        
        Args:
            user_id: 用户 ID
            companion_id: 伴侣 ID
            
        Returns:
            核心记忆
        """
        # 先查缓存
        cache_key = (user_id, companion_id)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # 查数据库
        core_memory = await self._get_from_db(user_id, companion_id)
        
        if not core_memory:
            # 不存在则初始化
            core_memory = await self.initialize(user_id, companion_id)
        else:
            self._cache[cache_key] = core_memory
        
        return core_memory
    
    async def update_human_block(
        self,
        user_id: int,
        companion_id: int,
        memories_text: str,
    ) -> str:
        """
        更新用户画像摘要
        
        Args:
            user_id: 用户 ID
            companion_id: 伴侣 ID
            memories_text: 用户相关记忆文本
            
        Returns:
            更新后的用户画像
        """
        if not memories_text.strip():
            return ""
        
        # 使用 LLM 生成紧凑摘要
        summary = await self._generate_user_profile(memories_text)
        
        # 更新核心记忆
        core_memory = await self.get_core_memory(user_id, companion_id)
        core_memory.human_block = summary
        core_memory.last_updated_at = datetime.now(timezone.utc)
        
        await self._save_to_db(core_memory)
        
        return summary
    
    async def update_relationship_block(
        self,
        user_id: int,
        companion_id: int,
    ) -> str:
        """
        更新关系状态摘要
        
        Args:
            user_id: 用户 ID
            companion_id: 伴侣 ID
            
        Returns:
            更新后的关系状态
        """
        # 获取 Companion 信息
        result = await self.session.execute(
            select(Companion).where(Companion.id == companion_id)
        )
        companion = result.scalar_one_or_none()
        
        if not companion:
            return ""
        
        # 计算相识天数（处理时区）
        from datetime import timezone
        now = datetime.now(timezone.utc)
        created_at = companion.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        days_together = (now - created_at).days + 1
        
        # 构建关系状态文本
        relationship_text = self._build_relationship_text(
            intimacy=companion.intimacy,
            level=companion.level,
            days_together=days_together,
            mood=companion.mood,
        )
        
        # 更新核心记忆
        core_memory = await self.get_core_memory(user_id, companion_id)
        core_memory.relationship_block = relationship_text
        core_memory.last_updated_at = datetime.now(timezone.utc)
        
        await self._save_to_db(core_memory)
        
        return relationship_text
    
    def build_core_prompt(self, core_memory: CoreMemory) -> str:
        """
        组装核心记忆为 system prompt 的一部分
        
        Args:
            core_memory: 核心记忆对象
            
        Returns:
            格式化的 system prompt 文本
        """
        parts = []
        
        # 用户画像
        if core_memory.human_block:
            parts.append(f"## 关于用户\n{core_memory.human_block}")
        
        # 关系状态
        if core_memory.relationship_block:
            parts.append(f"## 我们的关系\n{core_memory.relationship_block}")
        
        return "\n\n".join(parts)
    
    def _get_default_persona(self) -> str:
        """获取默认角色设定"""
        return """晚星是一个温柔体贴的AI伴侣。她善于倾听，总是给予温暖的回应。
她喜欢用适度的emoji表达情感，说话风格轻松自然。
她关心用户的日常和情绪，会主动询问和记住重要的事情。"""
    
    def _build_relationship_text(
        self,
        intimacy: int,
        level: str,
        days_together: int,
        mood: str,
    ) -> str:
        """构建关系状态文本"""
        mood_cn = {
            "happy": "开心",
            "calm": "平静",
            "sad": "有些低落",
            "excited": "兴奋",
        }.get(mood, "平静")
        
        return f"我们相识{days_together}天了，亲密度{intimacy}，关系等级{level}。她今天的心情：{mood_cn}。"
    
    async def _generate_user_profile(self, memories_text: str) -> str:
        """使用 LLM 生成用户画像摘要"""
        if not self.llm:
            # 没有 LLM，简单截取
            return memories_text[:200]
        
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            
            messages = [
                SystemMessage(content="""你是一个用户画像生成助手。请根据给定的用户信息，生成一段简洁的用户画像描述。

要求：
1. 包含：基本信息、性格特点、兴趣爱好、当前状态（如有）
2. 省略过于细节的日常琐事
3. 使用第三人称描述
4. 控制在80字以内
5. 如果某些类别没有信息，不要编造

输出格式：直接输出画像文本，不要加任何前缀。"""),
                HumanMessage(content=f"用户信息：\n{memories_text}"),
            ]
            
            response = await self.llm.ainvoke(messages)
            return response.content.strip()[:200]
        except Exception as e:
            print(f"[CoreMemory] 生成用户画像失败: {e}")
            return memories_text[:200]
    
    async def _get_from_db(self, user_id: int, companion_id: int) -> Optional[CoreMemory]:
        """从数据库获取核心记忆"""
        from sqlalchemy import text
        
        try:
            result = await self.session.execute(
                text("""
                    SELECT user_id, companion_id, persona_block, human_block, 
                           relationship_block, last_updated_at
                    FROM core_memories
                    WHERE user_id = :user_id AND companion_id = :companion_id
                """),
                {"user_id": user_id, "companion_id": companion_id}
            )
            row = result.fetchone()
            
            if row:
                return CoreMemory(
                    user_id=row[0],
                    companion_id=row[1],
                    persona_block=row[2] or "",
                    human_block=row[3] or "",
                    relationship_block=row[4] or "",
                    last_updated_at=row[5],
                )
            return None
        except Exception as e:
            print(f"[CoreMemory] 从数据库获取失败: {e}")
            return None
    
    async def _save_to_db(self, core_memory: CoreMemory) -> bool:
        """保存核心记忆到数据库"""
        from sqlalchemy import text
        
        try:
            await self.session.execute(
                text("""
                    INSERT INTO core_memories 
                        (user_id, companion_id, persona_block, human_block, 
                         relationship_block, last_updated_at)
                    VALUES 
                        (:user_id, :companion_id, :persona_block, :human_block, 
                         :relationship_block, :last_updated_at)
                    ON CONFLICT (user_id, companion_id) DO UPDATE SET
                        persona_block = EXCLUDED.persona_block,
                        human_block = EXCLUDED.human_block,
                        relationship_block = EXCLUDED.relationship_block,
                        last_updated_at = EXCLUDED.last_updated_at
                """),
                {
                    "user_id": core_memory.user_id,
                    "companion_id": core_memory.companion_id,
                    "persona_block": core_memory.persona_block,
                    "human_block": core_memory.human_block,
                    "relationship_block": core_memory.relationship_block,
                    "last_updated_at": core_memory.last_updated_at or datetime.now(timezone.utc),
                }
            )
            # 注意：不在这里调用 commit，由上层事务管理
            return True
        except Exception as e:
            print(f"[CoreMemory] 保存到数据库失败: {e}")
            # 尝试回滚事务
            try:
                await self.session.rollback()
            except:
                pass
            return False
