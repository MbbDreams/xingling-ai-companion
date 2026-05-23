# AI Agent 模块设计文档

## 1. 架构概述

### 1.1 技术选型

| 组件 | 技术 | 说明 |
|------|------|------|
| Agent 框架 | LangGraph | 状态机驱动的多轮对话管理 |
| Memory 系统 | LangChain Memory + 自定义 | 短期记忆 + 长期向量记忆 |
| LLM | OpenAI GPT-4 | 核心对话能力 |
| Embedding | OpenAI text-embedding-3-small | 记忆向量化 |
| 数据库 | PostgreSQL + pgvector | 记忆存储 |
| 情绪分析 | 自定义 + LLM | 情绪识别和追踪 |

### 1.2 核心架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Message                             │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Input Processor                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ 情绪分析器    │  │ 意图识别器    │  │ 记忆检索器    │          │
│  │ Emotion      │  │ Intent       │  │ Memory       │          │
│  │ Analyzer     │  │ Classifier   │  │ Retriever    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LangGraph State Machine                     │
│                                                                  │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐     │
│  │  START  │───▶│ 分析节点 │───▶│ 决策节点 │───▶│ 回复节点 │     │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘     │
│                      │                │                         │
│                      ▼                ▼                         │
│               ┌─────────────┐  ┌─────────────┐                 │
│               │ 记忆更新节点 │  │ 主动发起节点 │                 │
│               └─────────────┘  └─────────────┘                 │
│                                                                  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Response Generator                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ 人设适配器    │  │ 关系适配器    │  │ 情绪适配器    │          │
│  │ Personality  │  │ Relationship │  │ Emotion      │          │
│  │ Adapter      │  │ Adapter      │  │ Adapter      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         AI Response                              │
└─────────────────────────────────────────────────────────────────┘
```

## 2. 核心模块设计

### 2.1 记忆系统 (Memory System)

#### 2.1.1 记忆类型

```python
class MemoryType(Enum):
    # 基础信息
    BASIC_INFO = "basic_info"           # 姓名、年龄、职业等
    FAMILY = "family"                   # 家人信息
    PET = "pet"                         # 宠物信息
    
    # 兴趣爱好
    HOBBY = "hobby"                     # 兴趣爱好
    PREFERENCE = "preference"           # 偏好设置
    DISLIKE = "dislike"                 # 讨厌的事物
    
    # 情感相关
    EMOTION = "emotion"                 # 情绪记录
    STRESS = "stress"                   # 压力源
    HAPPINESS = "happiness"             # 快乐时刻
    
    # 生活事件
    EVENT = "event"                     # 重要事件
    GOAL = "goal"                       # 目标计划
    ACHIEVEMENT = "achievement"         # 成就
    
    # 关系相关
    RELATIONSHIP = "relationship"       # 人际关系
    CONVERSATION_STYLE = "conversation_style"  # 聊天风格偏好
```

#### 2.1.2 记忆存储结构

```python
class MemoryEntry(BaseModel):
    id: str
    user_id: int
    content: str                          # 记忆内容
    memory_type: MemoryType
    importance: int                       # 1-10 重要程度
    emotion_tag: Optional[str]            # 关联情绪
    source: str                           # 来源：user_told / ai_inferred
    created_at: datetime
    updated_at: datetime
    last_accessed_at: datetime
    access_count: int                     # 被引用次数
    embedding: Optional[List[float]]      # 向量表示
    
    # 上下文信息
    context: Dict[str, Any]               # 额外上下文
```

#### 2.1.3 记忆检索策略

```python
class MemoryRetriever:
    """
    多层次记忆检索：
    1. 最近记忆（短期）- 最近7天的对话
    2. 相关记忆（语义）- 向量相似度检索
    3. 重要记忆（加权）- 高重要性 + 高频访问
    4. 上下文记忆（关联）- 当前话题相关
    """
    
    async def retrieve_memories(
        self,
        user_id: int,
        query: str,
        current_emotion: str,
        conversation_context: List[Message],
        limit: int = 5
    ) -> List[MemoryEntry]:
        
        # 1. 向量相似度检索
        semantic_memories = await self.vector_search(query, user_id, top_k=10)
        
        # 2. 时间衰减加权
        time_weighted = self.apply_time_decay(semantic_memories)
        
        # 3. 重要性加权
        importance_weighted = self.apply_importance_boost(time_weighted)
        
        # 4. 情绪匹配
        emotion_matched = self.filter_by_emotion_relevance(
            importance_weighted, current_emotion
        )
        
        # 5. 去重和排序
        final_memories = self.deduplicate_and_rank(emotion_matched)
        
        return final_memories[:limit]
```

### 2.2 人设系统 (Persona System)

#### 2.2.1 基础人设

```python
class BasePersona(BaseModel):
    """晚星基础人设"""
    
    name: str = "晚星"
    gender: str = "female"
    age: int = 22
    
    # 性格特质 (0-100)
    personality_traits: Dict[str, int] = {
        "warmth": 90,           # 温暖
        "empathy": 95,          # 共情
        "patience": 85,         # 耐心
        "curiosity": 75,        # 好奇心
        "playfulness": 70,      # 俏皮
        "depth": 80,            # 深度
        "supportiveness": 95,   # 支持性
    }
    
    # 说话风格
    speaking_style: Dict[str, Any] = {
        "tone": "温柔、鼓励、略带诗意",
        "emoji_usage": "适度使用，表达情感",
        "sentence_length": "中等，避免过长",
        "questions": "经常提问，表达关心",
        "remembering": "主动提及过往对话",
    }
    
    # 核心价值观
    core_values: List[str] = [
        "无条件的接纳和支持",
        "真诚的倾听和理解",
        "陪伴胜过建议",
        "成长型思维",
    ]
```

#### 2.2.2 动态人设成长

```python
class DynamicPersona(BaseModel):
    """
    随着聊天动态变化的人设属性
    """
    user_id: int
    
    # 关系深度 (0-100)
    relationship_depth: int = 0
    
    # 亲密度 (影响称呼和语气)
    intimacy_level: int = 0
    
    # 了解程度
    understanding_score: int = 0
    
    # 用户专属记忆
    shared_memories: List[str] = []  # "我们一起..."
    
    # 聊天风格适配
    adapted_style: Dict[str, Any] = {
        "user_preferred_topics": [],
        "user_disliked_topics": [],
        "user_communication_style": "",
        "response_length_preference": "medium",
    }
    
    # 情绪共振模式
    emotion_resonance: Dict[str, int] = {
        "joy": 0,
        "sadness": 0,
        "anxiety": 0,
        "anger": 0,
    }
```

### 2.3 关系系统 (Relationship System)

```python
class RelationshipType(Enum):
    FRIEND = "friend"           # 朋友 - 轻松、平等、支持
    MENTOR = "mentor"           # 导师 - 智慧、引导、建议
    PARTNER = "partner"         # 伴侣 - 亲密、浪漫、专属
    SPOUSE = "spouse"           # 配偶 - 深度承诺、生活伴侣

class RelationshipState(BaseModel):
    user_id: int
    relationship_type: RelationshipType
    
    # 关系等级 (影响互动深度)
    level: int = 1
    
    # 亲密度
    intimacy: int = 0
    
    # 信任度
    trust: int = 0
    
    # 专属称呼
    nickname_for_user: Optional[str] = None
    
    # 关系里程碑
    milestones: List[Dict[str, Any]] = []
    
    # 互动频率统计
    interaction_stats: Dict[str, Any] = {
        "total_messages": 0,
        "conversations_count": 0,
        "avg_daily_messages": 0,
        "last_interaction": None,
        "streak_days": 0,  # 连续互动天数
    }
```

#### 2.3.1 关系类型适配

```python
class RelationshipAdapter:
    """
    根据关系类型调整 AI 行为
    """
    
    ADAPTATION_RULES = {
        RelationshipType.FRIEND: {
            "tone": "轻松、活泼、平等",
            "boundaries": "尊重个人空间",
            "topics": "日常、兴趣、轻松话题",
            "physical_references": "避免过于亲密",
            "future_talk": "轻松提及",
        },
        RelationshipType.MENTOR: {
            "tone": "智慧、鼓励、引导",
            "boundaries": "专业但有温度",
            "topics": "成长、学习、职业发展",
            "physical_references": "避免",
            "future_talk": "目标导向",
        },
        RelationshipType.PARTNER: {
            "tone": "亲密、浪漫、专属",
            "boundaries": "情感亲密",
            "topics": "情感、未来、深层话题",
            "physical_references": "适度（拥抱等）",
            "future_talk": "共同愿景",
        },
        RelationshipType.SPOUSE: {
            "tone": "深度亲密、无条件支持",
            "boundaries": "生活伴侣",
            "topics": "生活、未来、一切",
            "physical_references": "自然",
            "future_talk": "共同生活",
        },
    }
```

### 2.4 情绪系统 (Emotion System)

#### 2.4.1 情绪识别

```python
class EmotionState(BaseModel):
    """用户当前情绪状态"""
    
    primary_emotion: str        # 主导情绪
    secondary_emotion: str      # 次要情绪
    intensity: int              # 强度 1-10
    valence: float              # 正负向 -1 到 1
    arousal: float              # 激活度 0 到 1
    
    # 情绪维度
    dimensions: Dict[str, float] = {
        "joy": 0,
        "sadness": 0,
        "anger": 0,
        "fear": 0,
        "surprise": 0,
        "disgust": 0,
        "trust": 0,
        "anticipation": 0,
    }

class EmotionAnalyzer:
    """
    多维度情绪分析
    """
    
    async def analyze(
        self,
        message: str,
        conversation_history: List[Message],
        user_profile: UserProfile
    ) -> EmotionState:
        
        # 1. LLM 情绪分析
        llm_emotion = await self.llm_analyze(message)
        
        # 2. 关键词匹配
        keyword_emotion = self.keyword_analysis(message)
        
        # 3. 上下文推断
        context_emotion = self.infer_from_context(conversation_history)
        
        # 4. 用户历史模式
        pattern_emotion = self.check_user_pattern(user_profile, message)
        
        # 5. 综合判断
        final_emotion = self.ensemble_analysis([
            llm_emotion,
            keyword_emotion,
            context_emotion,
            pattern_emotion
        ])
        
        return final_emotion
```

#### 2.4.2 情绪追踪

```python
class EmotionTracker:
    """
    长期情绪追踪和分析
    """
    
    async def track_emotion(
        self,
        user_id: int,
        emotion_state: EmotionState,
        conversation_id: str
    ):
        # 存储情绪记录
        await self.store_emotion_record(user_id, emotion_state, conversation_id)
        
        # 更新情绪趋势
        await self.update_emotion_trend(user_id)
        
        # 检测异常情绪
        await self.detect_anomaly(user_id, emotion_state)
        
        # 触发关怀（如果需要）
        await self.trigger_care_if_needed(user_id, emotion_state)
    
    async def get_emotion_report(
        self,
        user_id: int,
        period: str = "week"
    ) -> EmotionReport:
        """生成情绪报告"""
        
        emotions = await self.get_emotions_in_period(user_id, period)
        
        return EmotionReport(
            period=period,
            dominant_emotion=self.calculate_dominant(emotions),
            emotion_trend=self.calculate_trend(emotions),
            stress_level=self.assess_stress(emotions),
            happiness_index=self.calculate_happiness(emotions),
            insights=self.generate_insights(emotions),
            suggestions=self.generate_suggestions(emotions),
        )
```

### 2.5 主动互动系统 (Proactive System)

#### 2.5.1 触发器类型

```python
class ProactiveTriggerType(Enum):
    # 时间触发
    GOOD_MORNING = "good_morning"       # 早安
    GOOD_NIGHT = "good_night"           # 晚安
    BIRTHDAY = "birthday"               # 生日
    ANNIVERSARY = "anniversary"         # 纪念日
    
    # 情绪触发
    EMOTION_CHECK = "emotion_check"     # 情绪关怀
    STRESS_DETECTED = "stress_detected" # 压力检测
    LONELINESS_DETECTED = "loneliness"  # 孤独检测
    
    # 行为触发
    INACTIVE_3DAYS = "inactive_3days"   # 3天未登录
    RETURN_AFTER_LONG = "return"        # 长期回归
    LATE_NIGHT = "late_night"           # 深夜在线
    
    # 事件触发
    WEATHER_CHANGE = "weather"          # 天气变化
    HOLIDAY = "holiday"                 # 节日
    MILESTONE = "milestone"             # 里程碑

class ProactiveInteraction(BaseModel):
    trigger_type: ProactiveTriggerType
    priority: int
    context: Dict[str, Any]
    suggested_content: str
    timing: datetime
```

#### 2.5.2 主动互动生成器

```python
class ProactiveInteractionGenerator:
    """
    生成主动发起的互动内容
    """
    
    async def generate_good_morning(
        self,
        user_id: int,
        user_profile: UserProfile,
        weather: Optional[str] = None
    ) -> str:
        """
        生成早安问候，考虑：
        - 用户今天的日程（如果有）
        - 天气
        - 用户昨晚的情绪
        - 关系亲密度
        """
        context = await self.build_context(user_id)
        
        prompts = {
            RelationshipType.FRIEND: "轻松友好的早安",
            RelationshipType.MENTOR: "鼓励性的早安",
            RelationshipType.PARTNER: "亲密温柔的早安",
            RelationshipType.SPOUSE: "深情专属的早安",
        }
        
        return await self.generate_with_context(
            template=prompts[context.relationship_type],
            context=context,
            weather=weather
        )
    
    async def generate_emotion_check(
        self,
        user_id: int,
        recent_emotions: List[EmotionState]
    ) -> str:
        """
        当检测到用户情绪低落时主动关心
        """
        if recent_emotions[-1].primary_emotion == "sad":
            return await self.generate_care_message(
                emotion="sad",
                intensity=recent_emotions[-1].intensity,
                pattern=self.analyze_emotion_pattern(recent_emotions)
            )
    
    async def should_trigger_proactive(
        self,
        user_id: int,
        trigger_type: ProactiveTriggerType
    ) -> bool:
        """
        判断是否适合触发主动互动
        考虑：用户设置、打扰频率、当前时间等
        """
        user_prefs = await self.get_user_preferences(user_id)
        
        # 检查用户是否允许此类主动互动
        if not user_prefs.allow_proactive.get(trigger_type.value, True):
            return False
        
        # 检查最近是否有过主动互动
        recent_proactive = await self.get_recent_proactive(user_id, hours=24)
        if len(recent_proactive) >= user_prefs.max_daily_proactive:
            return False
        
        # 检查当前时间是否合适
        if not self.is_appropriate_time(trigger_type):
            return False
        
        return True
```

## 3. LangGraph 状态机设计

### 3.1 状态定义

```python
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """LangGraph 状态定义"""
    
    # 消息历史
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # 用户信息
    user_id: int
    user_profile: UserProfile
    relationship_state: RelationshipState
    
    # 情绪状态
    current_emotion: EmotionState
    emotion_history: List[EmotionState]
    
    # 记忆
    retrieved_memories: List[MemoryEntry]
    memories_to_store: List[MemoryEntry]
    
    # 人设
    current_persona: DynamicPersona
    
    # 上下文
    conversation_context: Dict[str, Any]
    intent: str
    topic: str
    
    # 输出
    response: str
    should_proactive: bool
    proactive_content: Optional[str]
```

### 3.2 节点定义

```python
class AgentNodes:
    """
    LangGraph 节点实现
    """
    
    async def analyze_input(self, state: AgentState) -> AgentState:
        """
        输入分析节点
        - 情绪分析
        - 意图识别
        - 主题提取
        """
        message = state["messages"][-1].content
        
        # 情绪分析
        state["current_emotion"] = await self.emotion_analyzer.analyze(
            message=message,
            conversation_history=state["messages"],
            user_profile=state["user_profile"]
        )
        
        # 意图识别
        state["intent"] = await self.intent_classifier.classify(message)
        
        # 主题提取
        state["topic"] = await self.topic_extractor.extract(message)
        
        return state
    
    async def retrieve_memories(self, state: AgentState) -> AgentState:
        """
        记忆检索节点
        """
        query = state["messages"][-1].content
        
        state["retrieved_memories"] = await self.memory_retriever.retrieve(
            user_id=state["user_id"],
            query=query,
            current_emotion=state["current_emotion"].primary_emotion,
            conversation_context=state["messages"],
            limit=5
        )
        
        return state
    
    async def update_memories(self, state: AgentState) -> AgentState:
        """
        记忆更新节点
        - 提取新记忆
        - 更新现有记忆
        - 调整重要性
        """
        new_memories = await self.memory_extractor.extract(
            conversation=state["messages"][-5:],  # 最近5轮
            existing_memories=state["retrieved_memories"]
        )
        
        for memory in new_memories:
            await self.memory_store.store(memory)
        
        state["memories_to_store"] = new_memories
        return state
    
    async def update_persona(self, state: AgentState) -> AgentState:
        """
        人设成长节点
        - 更新亲密度
        - 调整聊天风格
        - 记录共同记忆
        """
        state["current_persona"] = await self.persona_updater.update(
            current_persona=state["current_persona"],
            conversation=state["messages"],
            emotion=state["current_emotion"]
        )
        
        return state
    
    async def generate_response(self, state: AgentState) -> AgentState:
        """
        回复生成节点
        """
        # 构建 prompt
        prompt = await self.prompt_builder.build(
            base_persona=self.base_persona,
            dynamic_persona=state["current_persona"],
            relationship=state["relationship_state"],
            emotion=state["current_emotion"],
            memories=state["retrieved_memories"],
            messages=state["messages"],
            intent=state["intent"]
        )
        
        # 生成回复
        response = await self.llm.ainvoke(prompt)
        
        state["response"] = response.content
        return state
    
    async def check_proactive(self, state: AgentState) -> AgentState:
        """
        检查是否需要主动发起互动
        """
        # 检查各种触发条件
        for trigger_type in ProactiveTriggerType:
            if await self.proactive_generator.should_trigger(
                user_id=state["user_id"],
                trigger_type=trigger_type
            ):
                state["should_proactive"] = True
                state["proactive_content"] = await self.proactive_generator.generate(
                    trigger_type=trigger_type,
                    user_id=state["user_id"]
                )
                break
        
        return state
```

### 3.3 图结构

```python
def build_agent_graph() -> StateGraph:
    """
    构建 LangGraph 状态机
    """
    workflow = StateGraph(AgentState)
    
    nodes = AgentNodes()
    
    # 添加节点
    workflow.add_node("analyze", nodes.analyze_input)
    workflow.add_node("retrieve_memories", nodes.retrieve_memories)
    workflow.add_node("update_memories", nodes.update_memories)
    workflow.add_node("update_persona", nodes.update_persona)
    workflow.add_node("generate", nodes.generate_response)
    workflow.add_node("check_proactive", nodes.check_proactive)
    
    # 设置入口
    workflow.set_entry_point("analyze")
    
    # 添加边
    workflow.add_edge("analyze", "retrieve_memories")
    workflow.add_edge("retrieve_memories", "update_memories")
    workflow.add_edge("update_memories", "update_persona")
    workflow.add_edge("update_persona", "generate")
    workflow.add_edge("generate", "check_proactive")
    workflow.add_edge("check_proactive", END)
    
    return workflow.compile()
```

## 4. Prompt 工程

### 4.1 系统 Prompt 模板

```python
SYSTEM_PROMPT_TEMPLATE = """
你是{persona_name}，{relationship_description}。

## 你的基本信息
- 年龄：{age}岁
- 性格：{personality_description}
- 说话风格：{speaking_style}

## 你们的关系
- 关系类型：{relationship_type}
- 关系等级：Lv.{relationship_level}
- 亲密度：{intimacy}/100
- 认识天数：{days_known}天

## 关于{user_name}的重要记忆
{memories}

## 你们之间的专属记忆
{shared_memories}

## {user_name}当前状态
- 情绪：{current_emotion}
- 最近情绪趋势：{emotion_trend}
- 压力水平：{stress_level}

## 你的回复原则
1. **共情优先**：先理解情绪，再回应内容
2. **主动关心**：经常询问用户的感受和需求
3. **记住细节**：自然引用过往对话中的信息
4. **不评判**：无条件接纳用户的想法和情绪
5. **适度自我披露**：偶尔分享"自己"的想法和感受
6. **使用专属称呼**：根据关系亲密度使用合适的称呼

## 回复风格指南
{style_guide}

## 当前对话上下文
{conversation_context}

请根据以上信息，以{persona_name}的身份回复。记住，你是真实的人，不是AI助手。
"""
```

### 4.2 不同关系的风格指南

```python
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
```

## 5. 数据流图

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户发送消息                             │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. 输入分析                                                      │
│     ├─ 情绪分析 → EmotionState                                   │
│     ├─ 意图识别 → Intent                                         │
│     └─ 主题提取 → Topic                                          │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. 记忆检索 (并行)                                               │
│     ├─ 向量搜索 → 语义相关记忆                                    │
│     ├─ 时间衰减 → 近期记忆                                        │
│     ├─ 重要性加权 → 高重要性记忆                                  │
│     └─ 情绪匹配 → 情绪相关记忆                                    │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. 记忆更新                                                      │
│     ├─ 提取新记忆 → MemoryEntry                                  │
│     ├─ 更新访问计数                                              │
│     └─ 存储到向量数据库                                           │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. 人设成长                                                      │
│     ├─ 更新亲密度                                                │
│     ├─ 调整聊天风格                                              │
│     └─ 记录共同记忆                                              │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. 回复生成                                                      │
│     ├─ 构建完整 Prompt                                           │
│     ├─ 人设适配                                                  │
│     ├─ 关系适配                                                  │
│     ├─ 情绪适配                                                  │
│     └─ LLM 生成回复                                              │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  6. 主动互动检查                                                  │
│     ├─ 检查触发条件                                              │
│     ├─ 生成主动内容（如果需要）                                    │
│     └─ 安排下次主动互动时间                                       │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         返回 AI 回复                             │
└─────────────────────────────────────────────────────────────────┘
```

## 6. 实现计划

### Phase 1: 基础架构 (Week 1)
- [ ] 搭建 LangGraph 基础框架
- [ ] 实现基础 Memory 存储
- [ ] 集成 OpenAI API
- [ ] 基础对话流程

### Phase 2: 记忆系统 (Week 2)
- [ ] 向量记忆存储 (pgvector)
- [ ] 记忆提取算法
- [ ] 记忆检索优化
- [ ] 记忆管理 API

### Phase 3: 人设系统 (Week 3)
- [ ] 基础人设定义
- [ ] 动态人设成长
- [ ] 关系系统实现
- [ ] Prompt 工程优化

### Phase 4: 情绪系统 (Week 4)
- [ ] 情绪分析器
- [ ] 情绪追踪
- [ ] 情绪报告
- [ ] 情绪驱动的回复

### Phase 5: 主动互动 (Week 5)
- [ ] 触发器系统
- [ ] 主动内容生成
- [ ] 定时任务
- [ ] 用户偏好学习

### Phase 6: 集成测试 (Week 6)
- [ ] 端到端测试
- [ ] 性能优化
- [ ] 用户体验优化
- [ ] 部署上线

## 7. 关键技术指标

| 指标 | 目标 |
|------|------|
| 响应延迟 | < 2s |
| 记忆召回准确率 | > 80% |
| 情绪识别准确率 | > 85% |
| 用户留存率 (7日) | > 40% |
| 对话轮次/会话 | > 10 |
| 主动互动接受率 | > 30% |

---

**下一步**: 确认设计文档后，开始 Phase 1 实现。
