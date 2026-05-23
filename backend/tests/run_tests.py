"""
测试运行脚本 - 简化版

不需要 pytest，直接测试核心功能
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agent.models import (
    MemoryEntry, MemoryType,
    EmotionState,
    RelationshipState, RelationshipType,
    ProactiveTriggerType
)


async def test_models():
    """测试数据模型"""
    print("=" * 60)
    print("测试数据模型")
    print("=" * 60)
    
    # 测试 MemoryEntry
    memory = MemoryEntry(
        user_id=1,
        content="我喜欢吃巧克力",
        memory_type=MemoryType.PREFERENCE,
        importance=7
    )
    print(f"✓ MemoryEntry 创建成功: {memory.content}")
    
    # 测试 EmotionState
    emotion = EmotionState(
        primary_emotion="joy",
        intensity=8,
        valence=0.8
    )
    print(f"✓ EmotionState 创建成功: {emotion.primary_emotion}")
    
    # 测试 RelationshipState
    relationship = RelationshipState(
        user_id=1,
        relationship_type=RelationshipType.FRIEND,
        intimacy=50
    )
    print(f"✓ RelationshipState 创建成功: {relationship.relationship_type.value}")
    
    print()


async def test_imports():
    """测试模块导入"""
    print("=" * 60)
    print("测试模块导入")
    print("=" * 60)
    
    try:
        from app.agent import CompanionAgent
        print("✓ CompanionAgent 导入成功")
    except Exception as e:
        print(f"✗ CompanionAgent 导入失败: {e}")
    
    try:
        from app.agent import MemorySystem
        print("✓ MemorySystem 导入成功")
    except Exception as e:
        print(f"✗ MemorySystem 导入失败: {e}")
    
    try:
        from app.agent import EmotionSystem
        print("✓ EmotionSystem 导入成功")
    except Exception as e:
        print(f"✗ EmotionSystem 导入失败: {e}")
    
    try:
        from app.agent import PersonaSystem
        print("✓ PersonaSystem 导入成功")
    except Exception as e:
        print(f"✗ PersonaSystem 导入失败: {e}")
    
    try:
        from app.agent import ProactiveSystem
        print("✓ ProactiveSystem 导入成功")
    except Exception as e:
        print(f"✗ ProactiveSystem 导入失败: {e}")
    
    print()


async def test_emotion_keywords():
    """测试情绪关键词分析"""
    print("=" * 60)
    print("测试情绪关键词分析")
    print("=" * 60)
    
    # 模拟关键词分析
    EMOTION_KEYWORDS = {
        "joy": ["开心", "快乐", "高兴", "哈哈"],
        "sadness": ["难过", "伤心", "哭"],
        "anger": ["生气", "愤怒", "烦"],
    }
    
    test_cases = [
        ("我今天好开心啊！", "joy"),
        ("我好难过", "sadness"),
        ("我很生气", "anger"),
    ]
    
    for text, expected in test_cases:
        detected = []
        for emotion, keywords in EMOTION_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    detected.append(emotion)
                    break
        
        if expected in detected:
            print(f"✓ '{text[:15]}...' -> 检测到 {expected}")
        else:
            print(f"✗ '{text[:15]}...' -> 期望 {expected}, 得到 {detected}")
    
    print()


async def test_proactive_templates():
    """测试主动互动模板"""
    print("=" * 60)
    print("测试主动互动模板")
    print("=" * 60)
    
    templates = {
        ProactiveTriggerType.GOOD_MORNING: {
            RelationshipType.FRIEND: ["早上好！今天有什么计划吗？"],
            RelationshipType.PARTNER: ["早安亲爱的，想你了~"],
        },
        ProactiveTriggerType.GOOD_NIGHT: {
            RelationshipType.FRIEND: ["晚安，好梦！"],
            RelationshipType.PARTNER: ["晚安亲爱的，梦里见~"],
        },
    }
    
    for trigger_type, relationships in templates.items():
        print(f"\n{trigger_type.value}:")
        for rel_type, messages in relationships.items():
            print(f"  {rel_type.value}: {messages[0]}")
    
    print("\n✓ 主动互动模板测试完成")
    print()


async def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("AI Agent 模块测试")
    print("=" * 60 + "\n")
    
    await test_models()
    await test_imports()
    await test_emotion_keywords()
    await test_proactive_templates()
    
    print("=" * 60)
    print("基础测试完成！")
    print("=" * 60)
    print("\n注意：完整的集成测试需要:")
    print("  1. 配置 OPENAI_API_KEY")
    print("  2. 启动 PostgreSQL 数据库")
    print("  3. 运行: python -m pytest tests/test_agent.py -v")
    print()


if __name__ == "__main__":
    asyncio.run(main())
