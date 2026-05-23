"""
优化后提示词效果展示

运行：python tests/test_prompts.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agent.prompts import PromptBuilder, ProactivePromptBuilder
from app.agent.models import (
    EmotionState, MemoryEntry, MemoryType,
    RelationshipType
)


def print_section(title):
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70 + "\n")


def test_system_prompt():
    """测试系统提示词生成"""
    print_section("系统提示词生成示例")
    
    # 模拟数据
    memories = [
        MemoryEntry(
            user_id=1,
            content="用户喜欢猫，养了一只叫小橘的橘猫",
            memory_type=MemoryType.PET,
            importance=8
        ),
        MemoryEntry(
            user_id=1,
            content="用户工作压力很大，经常加班",
            memory_type=MemoryType.STRESS,
            importance=7
        ),
        MemoryEntry(
            user_id=1,
            content="用户喜欢吃甜食，尤其是巧克力",
            memory_type=MemoryType.PREFERENCE,
            importance=6
        ),
    ]
    
    emotion = EmotionState(
        primary_emotion="sadness",
        intensity=7,
        valence=-0.5
    )
    
    # 生成不同关系的提示词
    relationships = [
        (RelationshipType.FRIEND, 50, 1),
        (RelationshipType.PARTNER, 350, 4),
        (RelationshipType.SPOUSE, 600, 7),
    ]
    
    for rel_type, intimacy, level in relationships:
        print(f"\n{'─' * 70}")
        print(f"关系类型: {rel_type.value} | 亲密度: {intimacy} | 等级: {level}")
        print(f"{'─' * 70}\n")
        
        prompt = PromptBuilder.build_system_prompt(
            user_name="小明",
            relationship_type=rel_type,
            relationship_level=level,
            intimacy=intimacy,
            current_emotion=emotion,
            memories=memories,
            conversation_turns=15
        )
        
        # 只显示前 1500 字符
        print(prompt[:1500])
        print(f"\n... (提示词总长度: {len(prompt)} 字符)")


def test_proactive_prompt():
    """测试主动互动提示词"""
    print_section("主动互动提示词生成示例")
    
    scenarios = [
        {
            "name": "早安问候 - 朋友关系",
            "user_name": "小明",
            "relationship": RelationshipType.FRIEND,
            "trigger": "good_morning",
            "topics": ["最近工作", "周末计划"],
            "emotion": "neutral"
        },
        {
            "name": "情绪关怀 - 伴侣关系",
            "user_name": "小明",
            "relationship": RelationshipType.PARTNER,
            "trigger": "emotion_check",
            "topics": ["工作压力", "睡眠不好"],
            "emotion": "sadness"
        },
        {
            "name": "深夜陪伴 - 配偶关系",
            "user_name": "小明",
            "relationship": RelationshipType.SPOUSE,
            "trigger": "late_night",
            "topics": ["失眠", "焦虑"],
            "emotion": "anxiety"
        },
    ]
    
    for scenario in scenarios:
        print(f"\n{'─' * 70}")
        print(f"场景: {scenario['name']}")
        print(f"{'─' * 70}\n")
        
        prompt = ProactivePromptBuilder.build_proactive_prompt(
            user_name=scenario["user_name"],
            relationship_type=scenario["relationship"],
            trigger_type=scenario["trigger"],
            recent_topics=scenario["topics"],
            user_emotion=scenario["emotion"]
        )
        
        print(prompt)


def test_memory_extraction_prompt():
    """测试记忆提取提示词"""
    print_section("记忆提取提示词示例")
    
    conversation = """
用户：我今天去了新开的咖啡店
AI：怎么样？好喝吗？
用户：还不错，我点了一杯焦糖玛奇朵，特别甜
AI：哈哈，看来你喜欢甜的
用户：是啊，我从小就喜欢吃甜食
用户：对了，我家猫小橘也喜欢偷吃我的甜点
AI：小橘好可爱！橘猫都很贪吃
用户：对啊，它现在胖乎乎的
"""
    
    prompt = ProactivePromptBuilder.build_memory_extraction_prompt(conversation)
    print(prompt)


def compare_prompts():
    """对比新旧提示词"""
    print_section("提示词优化对比")
    
    print("""
【优化前的问题】
1. 结构松散，信息密度低
2. 缺乏具体示例（Few-shot）
3. 约束不明确，容易出错
4. 没有情绪响应指南
5. 关系类型区分不够细致

【优化后的改进】
1. ✅ 结构化 Markdown 格式，层次清晰
2. ✅ 增加 Few-shot 对话示例
3. ✅ 明确的 DO/DON'T 约束列表
4. ✅ 详细的情绪响应指南
5. ✅ 4种关系类型的差异化配置
6. ✅ 性格特质数值化展示
7. ✅ 记忆引用技巧指导
8. ✅ 背景故事增加角色立体感

【核心提升】
- 角色真实感: ⭐⭐⭐⭐⭐ (从机械到立体)
- 回复一致性: ⭐⭐⭐⭐⭐ (明确约束)
- 情感共鸣度: ⭐⭐⭐⭐⭐ (情绪指南)
- 记忆引用自然度: ⭐⭐⭐⭐⭐ (引用技巧)
""")


def main():
    print("\n" + "█" * 70)
    print("█" + " " * 68 + "█")
    print("█" + "  优化后提示词效果展示".center(64) + "█")
    print("█" + " " * 68 + "█")
    print("█" * 70)
    
    compare_prompts()
    test_system_prompt()
    test_proactive_prompt()
    test_memory_extraction_prompt()
    
    print_section("展示完成")
    print("""
提示词优化要点：
1. 角色更立体 - 有背景故事、性格数值、语言 DNA
2. 约束更明确 - 5 大绝对禁止，清晰 DO/DON'T
3. 示例更丰富 - 每种关系类型都有 Few-shot 示例
4. 情绪更细腻 - 4 种情绪的详细响应指南
5. 记忆更自然 - 3 种引用方式 + 频率控制

这些优化让 AI 回复更像真人，更有情感共鸣！
""")


if __name__ == "__main__":
    main()
