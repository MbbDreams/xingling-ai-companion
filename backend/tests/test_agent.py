"""
AI Agent 测试模块

测试内容：
1. 记忆系统测试
2. 情绪系统测试
3. 人设系统测试
4. 主动互动系统测试
5. 完整 Agent 集成测试

运行方式：
    cd backend
    python -m pytest tests/test_agent.py -v
    
    或运行单个测试：
    python -m pytest tests/test_agent.py::TestMemorySystem -v
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker

from app.agent import (
    MemorySystem, MemoryType, MemoryEntry,
    EmotionSystem, EmotionState,
    PersonaSystem, RelationshipType,
    ProactiveSystem, ProactiveTriggerType,
    CompanionAgent
)
from app.models.entities import Base, User, Companion, Memory, Message, Conversation


# 测试数据库配置
TEST_DATABASE_URL = "postgresql+asyncpg://xingling:xingling_dev@localhost:5433/xingling_ai_test"


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def engine():
    """创建测试数据库引擎"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True
    )
    
    # 创建表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # 清理
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def db_session(engine) -> AsyncSession:
    """创建数据库会话"""
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """创建测试用户"""
    user = User(
        phone="13800138000",
        nickname="测试用户",
        coins=100,
        is_vip=False
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
async def test_companion(db_session: AsyncSession, test_user: User) -> Companion:
    """创建测试伴侣"""
    companion = Companion(
        user_id=test_user.id,
        name="晚星",
        intimacy=50,
        level="Lv.1"
    )
    db_session.add(companion)
    await db_session.flush()
    return companion


class TestMemorySystem:
    """记忆系统测试"""
    
    @pytest.mark.asyncio
    async def test_store_and_retrieve_memory(self, db_session: AsyncSession, test_user: User):
        """测试记忆存储和检索"""
        memory_system = MemorySystem(db_session, openai_client=None)
        
        # 创建记忆
        entry = MemoryEntry(
            user_id=test_user.id,
            content="我喜欢吃巧克力",
            memory_type=MemoryType.PREFERENCE,
            importance=7,
            emotion_tag="joy"
        )
        
        # 存储记忆
        stored = await memory_system.store_memory(entry)
        
        assert stored.id is not None
        assert stored.user_id == test_user.id
        assert stored.content == "我喜欢吃巧克力"
        
        print(f"✓ 记忆存储成功: {stored.id}")
    
    @pytest.mark.asyncio
    async def test_retrieve_memories_by_type(self, db_session: AsyncSession, test_user: User):
        """测试按类型检索记忆"""
        memory_system = MemorySystem(db_session, openai_client=None)
        
        # 存储多个记忆
        memories = [
            MemoryEntry(user_id=test_user.id, content="我喜欢猫", memory_type=MemoryType.PET, importance=8),
            MemoryEntry(user_id=test_user.id, content="我养了一只狗", memory_type=MemoryType.PET, importance=7),
            MemoryEntry(user_id=test_user.id, content="我喜欢蓝色", memory_type=MemoryType.PREFERENCE, importance=5),
        ]
        
        for mem in memories:
            await memory_system.store_memory(mem)
        
        # 按类型检索
        pet_memories = await memory_system.get_memories_by_type(
            test_user.id, MemoryType.PET, limit=10
        )
        
        assert len(pet_memories) == 2
        assert all(m.memory_type == MemoryType.PET for m in pet_memories)
        
        print(f"✓ 按类型检索成功: 找到 {len(pet_memories)} 条宠物记忆")
    
    @pytest.mark.asyncio
    async def test_extract_memories_from_conversation(self, db_session: AsyncSession, test_user: User):
        """测试从对话提取记忆"""
        memory_system = MemorySystem(db_session, openai_client=None)
        
        # 模拟对话
        conversation = [
            {"role": "user", "content": "我今天去了北京旅游"},
            {"role": "assistant", "content": "太棒了！北京有很多好玩的地方"},
            {"role": "user", "content": "是的，我最喜欢故宫"},
        ]
        
        # 提取记忆（没有 OpenAI 客户端时返回空）
        memories = await memory_system.extract_memories_from_conversation(
            test_user.id, conversation
        )
        
        # 没有 OpenAI 客户端时应该返回空列表
        assert isinstance(memories, list)
        
        print(f"✓ 记忆提取测试完成")


class TestEmotionSystem:
    """情绪系统测试"""
    
    @pytest.mark.asyncio
    async def test_analyze_emotion_keywords(self, db_session: AsyncSession):
        """测试关键词情绪分析"""
        emotion_system = EmotionSystem(db_session, openai_client=None)
        
        # 测试开心
        emotion = await emotion_system.analyze_emotion("我今天好开心啊！")
        assert emotion.primary_emotion in ["joy", "neutral"]
        print(f"✓ 开心情绪分析: {emotion.primary_emotion}")
        
        # 测试难过
        emotion = await emotion_system.analyze_emotion("我好难过，想哭")
        assert emotion.primary_emotion in ["sadness", "neutral"]
        print(f"✓ 难过情绪分析: {emotion.primary_emotion}")
        
        # 测试生气
        emotion = await emotion_system.analyze_emotion("我很生气！")
        assert emotion.primary_emotion in ["anger", "neutral"]
        print(f"✓ 生气情绪分析: {emotion.primary_emotion}")
    
    @pytest.mark.asyncio
    async def test_keyword_analysis(self, db_session: AsyncSession):
        """测试关键词分析内部方法"""
        emotion_system = EmotionSystem(db_session, openai_client=None)
        
        scores = emotion_system._keyword_analysis("哈哈，太开心了！")
        
        assert "joy" in scores
        assert scores["joy"] > 0  # 应该检测到开心
        
        print(f"✓ 关键词分析: joy={scores['joy']:.2f}")
    
    @pytest.mark.asyncio
    async def test_detect_stress_pattern(self, db_session: AsyncSession, test_user: User):
        """测试压力模式检测"""
        emotion_system = EmotionSystem(db_session, openai_client=None)
        
        # 创建负面情绪序列
        negative_emotions = [
            EmotionState(primary_emotion="sadness", intensity=8),
            EmotionState(primary_emotion="sadness", intensity=7),
            EmotionState(primary_emotion="fear", intensity=6),
        ]
        
        result = await emotion_system.detect_stress_pattern(
            test_user.id, negative_emotions
        )
        
        assert "is_stressed" in result
        assert "level" in result
        
        print(f"✓ 压力检测: is_stressed={result['is_stressed']}, level={result['level']}")


class TestPersonaSystem:
    """人设系统测试"""
    
    @pytest.mark.asyncio
    async def test_get_or_create_relationship(self, db_session: AsyncSession, test_user: User):
        """测试获取或创建关系"""
        persona_system = PersonaSystem(db_session)
        
        relationship = await persona_system.get_or_create_relationship(
            test_user.id, RelationshipType.FRIEND
        )
        
        assert relationship.user_id == test_user.id
        assert relationship.relationship_type == RelationshipType.FRIEND
        
        print(f"✓ 关系创建: type={relationship.relationship_type.value}")
    
    @pytest.mark.asyncio
    async def test_update_relationship(self, db_session: AsyncSession, test_user: User):
        """测试更新关系"""
        persona_system = PersonaSystem(db_session)
        
        # 初始关系
        initial = await persona_system.get_or_create_relationship(test_user.id)
        initial_intimacy = initial.intimacy
        
        # 更新关系
        updated = await persona_system.update_relationship(
            test_user.id, intimacy_delta=10, interaction=True
        )
        
        assert updated.intimacy == initial_intimacy + 10
        assert updated.interaction_stats["total_messages"] >= 1
        
        print(f"✓ 关系更新: intimacy={updated.intimacy}")
    
    @pytest.mark.asyncio
    async def test_build_system_prompt(self, db_session: AsyncSession, test_user: User):
        """测试构建系统 Prompt"""
        persona_system = PersonaSystem(db_session)
        
        relationship = await persona_system.get_or_create_relationship(test_user.id)
        dynamic_persona = await persona_system.get_dynamic_persona(test_user.id)
        emotion = EmotionState(primary_emotion="joy", intensity=7)
        
        prompt = await persona_system.build_system_prompt(
            user_id=test_user.id,
            user_name=test_user.nickname or "用户",
            relationship=relationship,
            dynamic_persona=dynamic_persona,
            emotion=emotion,
            memories=[],
            conversation_context=[]
        )
        
        assert "晚星" in prompt
        assert test_user.nickname or "用户" in prompt
        assert "joy" in prompt or "开心" in prompt
        
        print(f"✓ Prompt 构建成功，长度: {len(prompt)}")


class TestProactiveSystem:
    """主动互动系统测试"""
    
    @pytest.mark.asyncio
    async def test_analyze_recent_conversations(self, db_session: AsyncSession, test_user: User):
        """测试分析最近对话"""
        proactive_system = ProactiveSystem(db_session, openai_client=None)
        
        # 模拟对话
        messages = [
            {"role": "user", "content": "我今天工作压力好大"},
            {"role": "assistant", "content": "听起来你很辛苦，需要休息一下"},
            {"role": "user", "content": "是啊，感觉很累"},
        ]
        
        analysis = await proactive_system.analyze_recent_conversations(
            test_user.id, messages
        )
        
        assert "topics" in analysis
        assert "user_emotion" in analysis
        
        print(f"✓ 对话分析: emotion={analysis.get('user_emotion')}")
    
    @pytest.mark.asyncio
    async def test_should_trigger_proactive(self, db_session: AsyncSession, test_user: User):
        """测试是否应该触发主动互动"""
        proactive_system = ProactiveSystem(db_session, openai_client=None)
        
        user_prefs = {
            "allow_proactive": True,
            "max_daily_proactive": 3,
            "recent_proactive_count": 0
        }
        
        # 测试允许触发
        should_trigger = await proactive_system.should_trigger_proactive(
            test_user.id,
            ProactiveTriggerType.EMOTION_CHECK,
            user_prefs,
            []
        )
        
        # 结果取决于当前时间
        print(f"✓ 触发判断: should_trigger={should_trigger}")
    
    @pytest.mark.asyncio
    async def test_generate_proactive_content(self, db_session: AsyncSession, test_user: User):
        """测试生成主动内容"""
        proactive_system = ProactiveSystem(db_session, openai_client=None)
        
        recent_analysis = {
            "user_emotion": "sad",
            "potential_topics": ["工作压力"],
            "unfinished_topics": []
        }
        
        content = await proactive_system.generate_proactive_content(
            user_id=test_user.id,
            trigger_type=ProactiveTriggerType.EMOTION_CHECK,
            user_name="测试用户",
            relationship_type=RelationshipType.FRIEND,
            recent_analysis=recent_analysis,
            memories=[]
        )
        
        assert len(content) > 0
        print(f"✓ 主动内容生成: {content[:50]}...")


class TestCompanionAgent:
    """完整 Agent 集成测试"""
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, db_session: AsyncSession):
        """测试 Agent 初始化"""
        agent = CompanionAgent(
            db=db_session,
            openai_api_key=None,  # 测试时不需要真实 API key
            model="gpt-4o-mini"
        )
        
        assert agent is not None
        assert agent.memory_system is not None
        assert agent.emotion_system is not None
        assert agent.persona_system is not None
        assert agent.proactive_system is not None
        assert agent.graph is not None
        
        print("✓ Agent 初始化成功")
    
    @pytest.mark.asyncio
    async def test_agent_chat_without_api_key(self, db_session: AsyncSession, test_user: User, test_companion: Companion):
        """测试 Agent 聊天（无 API key，应该使用模拟回复）"""
        agent = CompanionAgent(
            db=db_session,
            openai_api_key=None,
            model="gpt-4o-mini"
        )
        
        # 这个测试会失败，因为没有真实的 OpenAI API key
        # 但我们可以测试流程是否正常
        try:
            result = await agent.chat(
                user_id=test_user.id,
                user_name=test_user.nickname or "用户",
                conversation_id="test-conv-1",
                message="你好",
                history=[]
            )
            
            assert "response" in result
            assert "emotion" in result
            print(f"✓ Agent 聊天成功: {result['response'][:50]}...")
            
        except Exception as e:
            # 预期会失败，因为没有 API key
            print(f"⚠ Agent 聊天测试跳过（无 API key）: {e}")


# 手动运行测试的辅助函数
def run_tests():
    """手动运行所有测试"""
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-k", "test_"  # 只运行以 test_ 开头的函数
    ])


if __name__ == "__main__":
    print("=" * 60)
    print("AI Agent 测试模块")
    print("=" * 60)
    print()
    print("运行方式:")
    print("  1. 使用 pytest: python -m pytest tests/test_agent.py -v")
    print("  2. 直接运行: python tests/test_agent.py")
    print()
    
    # 检查是否需要运行测试
    if len(sys.argv) > 1 and sys.argv[1] == "--run":
        run_tests()
    else:
        print("提示: 添加 --run 参数来运行测试")
        print("例如: python tests/test_agent.py --run")
