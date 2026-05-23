from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Conversation, Memory, Message
from app.schemas.chat import ChatRequest, ChatResponse, MessageRead
from app.services.bootstrap import get_or_create_companion, get_or_create_user
from app.services.emotion_service import classify_emotion
from app.services.memory_service import extract_memory_candidates
from app.services.openai_service import OpenAIService


class ChatService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.openai = OpenAIService()

    async def send_message(self, payload: ChatRequest) -> ChatResponse:
        user = await get_or_create_user(self.session, payload.user_id)
        companion = await get_or_create_companion(self.session, user, payload.companion_id)
        conversation = await self._get_or_create_conversation(payload.conversation_id, user.id, companion.id)

        emotion = classify_emotion(payload.message)
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=payload.message,
            emotion=emotion,
        )
        self.session.add(user_message)
        await self.session.flush()

        memory_candidates = extract_memory_candidates(payload.message)
        for candidate in memory_candidates:
            self.session.add(
                Memory(
                    user_id=user.id,
                    companion_id=companion.id,
                    source_message_id=user_message.id,
                    memory=candidate,
                    category="auto",
                    importance=0.6,
                )
            )

        memories = (
            await self.session.scalars(
                select(Memory)
                .where(Memory.user_id == user.id)
                .order_by(Memory.importance.desc(), Memory.created_at.desc())
                .limit(8)
            )
        ).all()
        recent_messages = (
            await self.session.scalars(
                select(Message)
                .where(Message.conversation_id == conversation.id)
                .order_by(Message.created_at.desc(), Message.id.desc())
                .limit(10)
            )
        ).all()
        recent_messages = list(reversed(recent_messages))

        reply = await self.openai.generate_reply(companion, memories, recent_messages, payload.message, emotion)
        ai_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=reply,
            emotion=emotion,
        )
        self.session.add(ai_message)
        
        # 计算亲密度增长（无上限，每100升一级）
        old_intimacy = companion.intimacy
        companion.intimacy += 1
        intimacy_gained = 1
        
        # 更新等级
        new_level = int(companion.intimacy / 100) + 1
        companion.level = f"Lv.{new_level}"
        
        await self.session.flush()
        await self.session.commit()

        return ChatResponse(
            conversation_id=conversation.id,
            reply=reply,
            emotion=emotion,
            memory_candidates=memory_candidates,
            messages=[MessageRead.model_validate(user_message), MessageRead.model_validate(ai_message)],
            intimacy_gained=intimacy_gained,
        )

    async def _get_or_create_conversation(
        self,
        conversation_id: int | None,
        user_id: int,
        companion_id: int,
    ) -> Conversation:
        if conversation_id is not None:
            conversation = await self.session.get(Conversation, conversation_id)
            if conversation is not None and conversation.user_id == user_id:
                return conversation

        conversation = Conversation(user_id=user_id, companion_id=companion_id, title="和晚星聊天")
        self.session.add(conversation)
        await self.session.flush()
        return conversation
