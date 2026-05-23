"""
记忆提取器 - Memory Extractor

从对话中智能提取结构化记忆。
采用关键词预过滤 + LLM 提取的两阶段策略。

核心优化：
1. 关键词预过滤：避免对无意义消息调用 LLM
2. 使用轻量模型：降低成本
3. 去重合并：避免重复存储
"""

import json
from typing import Optional
from pydantic import BaseModel

from app.agent.memory.long_term_memory import LongTermMemoryManager


class ExtractedMemory(BaseModel):
    """提取的记忆"""
    content: str
    type: str = "general"
    importance: int = 5  # 1-10


class MemoryExtractor:
    """记忆提取器"""
    
    # 提取触发关键词（参考星野的动态触发规则）
    EXTRACTION_KEYWORDS = {
        'basic_info': ['我叫', '我是', '我的名字', '我今年', '我住', '我在', '我的工作', '我从事'],
        'preference': ['喜欢', '讨厌', '不爱', '最爱', '偏好', '习惯', '一般会', '通常'],
        'family': ['爸爸', '妈妈', '哥哥', '姐姐', '弟弟', '妹妹', '家里', '家人', '父母', '孩子'],
        'pet': ['猫', '狗', '宠物', '养了', '我家有'],
        'hobby': ['爱好', '平时', '周末', '运动', '游戏', '音乐', '电影', '看书', '追剧'],
        'emotion': ['开心', '难过', '生气', '焦虑', '压力', '累', '烦', '郁闷', '孤独', '害怕'],
        'event': ['昨天', '上周', '前几天', '最近', '发生', '去了', '参加了', '出差'],
        'goal': ['计划', '打算', '目标', '想', '准备', '要', '希望', '梦想'],
        'relationship': ['男朋友', '女朋友', '老公', '老婆', '对象', '暗恋', '分手', '结婚'],
    }
    
    # 无意义消息模式（跳过提取）
    SKIP_PATTERNS = [
        '嗯', '好的', '好', '哦', '啊', '是吗', '对的', '是的',
        '谢谢', '感谢', '不客气', '没关系',
        '哈哈', '嘿嘿', '呵呵', '...',
    ]
    
    def __init__(self, llm=None, long_term_memory: LongTermMemoryManager = None):
        """
        初始化记忆提取器
        
        Args:
            llm: LLM 实例
            long_term_memory: 长期记忆管理器
        """
        self.llm = llm
        self.long_term_memory = long_term_memory
    
    async def extract_from_conversation(
        self,
        user_message: str,
        ai_response: str,
        user_id: int,
        companion_id: int,
    ) -> list[ExtractedMemory]:
        """
        从一轮对话中提取记忆
        
        流程：
        1. 快速判断：检查是否包含提取关键词 → 不包含则跳过
        2. LLM 提取：调用轻量模型
        3. 解析结果：JSON 数组 → ExtractedMemory 列表
        4. 存储：写入长期记忆
        
        Args:
            user_message: 用户消息
            ai_response: AI 回复
            user_id: 用户 ID
            companion_id: 伴侣 ID
            
        Returns:
            提取的记忆列表
        """
        # 1. 快速判断是否需要提取
        if not self.should_extract(user_message):
            return []
        
        # 2. LLM 提取
        extracted = await self._llm_extract(user_message, ai_response)
        
        if not extracted:
            return []
        
        # 3. 存储到长期记忆
        stored_memories = []
        for memory in extracted:
            if self.long_term_memory:
                memory_id = await self.long_term_memory.store_memory(
                    user_id=user_id,
                    companion_id=companion_id,
                    content=memory.content,
                    memory_type=memory.type,
                    importance=memory.importance / 10.0,  # 转换为 0-1
                    source="user_told",
                )
                if memory_id:
                    stored_memories.append(memory)
        
        return stored_memories
    
    def should_extract(self, user_message: str) -> bool:
        """
        快速判断是否需要提取记忆（关键词预过滤）
        
        Args:
            user_message: 用户消息
            
        Returns:
            是否需要提取
        """
        if not user_message or not user_message.strip():
            return False
        
        message = user_message.strip()
        
        # 检查是否为无意义消息
        if message in self.SKIP_PATTERNS:
            return False
        
        if len(message) < 3:
            return False
        
        # 检查是否包含关键词
        for category, keywords in self.EXTRACTION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in message:
                    return True
        
        return False
    
    def detect_memory_type(self, user_message: str) -> str:
        """
        检测记忆类型
        
        Args:
            user_message: 用户消息
            
        Returns:
            记忆类型
        """
        for category, keywords in self.EXTRACTION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in user_message:
                    return category
        return "general"
    
    async def _llm_extract(
        self,
        user_message: str,
        ai_response: str,
    ) -> list[ExtractedMemory]:
        """
        使用 LLM 提取记忆
        
        Args:
            user_message: 用户消息
            ai_response: AI 回复
            
        Returns:
            提取的记忆列表
        """
        if not self.llm:
            # 没有 LLM，使用简单规则提取
            return self._rule_based_extract(user_message)
        
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            
            messages = [
                SystemMessage(content=self._get_extraction_prompt()),
                HumanMessage(content=f"用户: {user_message}\nAI: {ai_response}"),
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # 解析 JSON 结果
            return self._parse_extraction_result(response.content)
            
        except Exception as e:
            print(f"[MemoryExtractor] LLM 提取失败: {e}")
            return self._rule_based_extract(user_message)
    
    def _get_extraction_prompt(self) -> str:
        """获取记忆提取提示词"""
        return """你是一个记忆提取助手。请从以下对话中提取关于用户的关键信息。

## 提取规则
1. 只提取关于**用户**的信息，不提取关于 AI 的信息
2. 每条记忆应该是独立的、具体的事实或偏好
3. 忽略寒暄、确认等无信息量内容（如"好的"、"嗯嗯"）
4. 重要性评分 1-10：基本信息 8-10，偏好 5-7，闲聊 1-3
5. 如果没有值得记忆的信息，返回空数组

## 记忆类型
- basic_info: 姓名、年龄、职业、住址等基本信息
- preference: 喜欢/讨厌的事物、习惯
- family: 家庭成员信息
- pet: 宠物信息
- hobby: 兴趣爱好
- emotion: 情绪状态（当前）
- event: 重要事件或经历
- goal: 计划或目标
- relationship: 人际关系信息

## 输出格式（JSON 数组）
```json
[
  {"content": "用户叫张三", "type": "basic_info", "importance": 9},
  {"content": "用户喜欢猫", "type": "preference", "importance": 6}
]
```

如果没有值得记忆的信息，返回: []"""
    
    def _parse_extraction_result(self, response: str) -> list[ExtractedMemory]:
        """解析 LLM 返回的 JSON 结果"""
        try:
            # 提取 JSON 部分
            text = response.strip()
            
            # 尝试找到 JSON 数组
            start = text.find('[')
            end = text.rfind(']') + 1
            
            if start == -1 or end == 0:
                return []
            
            json_str = text[start:end]
            data = json.loads(json_str)
            
            result = []
            for item in data:
                if isinstance(item, dict) and 'content' in item:
                    result.append(ExtractedMemory(
                        content=item.get('content', ''),
                        type=item.get('type', 'general'),
                        importance=item.get('importance', 5),
                    ))
            
            return result
            
        except Exception as e:
            print(f"[MemoryExtractor] 解析 JSON 失败: {e}")
            return []
    
    def _rule_based_extract(self, user_message: str) -> list[ExtractedMemory]:
        """基于规则的记忆提取（无 LLM 时的降级方案）"""
        memories = []
        
        # 检测记忆类型
        memory_type = self.detect_memory_type(user_message)
        
        if memory_type != "general":
            # 简单提取：直接使用用户消息作为记忆内容
            memories.append(ExtractedMemory(
                content=user_message,
                type=memory_type,
                importance=6,
            ))
        
        return memories
