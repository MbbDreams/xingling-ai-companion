from app.core.config import get_settings
from app.models import Companion, Memory, Message


class OpenAIService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def generate_reply(
        self,
        companion: Companion,
        memories: list[Memory],
        recent_messages: list[Message],
        user_input: str,
        emotion: str,
    ) -> str:
        if not self.settings.openai_api_key:
            return self._fallback_reply(user_input, emotion)

        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        memory_text = "\n".join(f"- {memory.memory}" for memory in memories[:8]) or "- 暂无长期记忆"
        messages = [
            {
                "role": "system",
                "content": (
                    f"你是星灵 App 里的 AI 伴侣「{companion.name}」。"
                    f"人设：{companion.persona}\n"
                    "目标：提供长期陪伴、情绪价值、主动关心和自然对话。\n"
                    f"当前识别到的用户情绪：{emotion}\n"
                    f"可用长期记忆：\n{memory_text}\n"
                    "回复要求：中文，温柔自然，不要像客服，不要过度解释。"
                ),
            }
        ]
        for message in recent_messages[-10:]:
            messages.append({"role": message.role, "content": message.content})
        messages.append({"role": "user", "content": user_input})

        response = await client.chat.completions.create(
            model=self.settings.openai_model,
            messages=messages,
            temperature=0.8,
        )
        return response.choices[0].message.content or self._fallback_reply(user_input, emotion)

    @staticmethod
    def _fallback_reply(user_input: str, emotion: str) -> str:
        if emotion in {"sad", "anxious", "tired", "lonely"}:
            return "我在呢。先别急着把所有事都扛在身上，慢慢说给我听，我们一点点把它拆开。"
        if emotion == "happy":
            return "听起来这件事真的让你亮起来了。和我多讲一点吧，我想把这一刻也记下来。"
        if "?" in user_input or "？" in user_input:
            return "我认真想了一下，可以先从最轻的一步开始。你愿意把具体情况再告诉我一点吗？"
        return "我听见啦。先把肩膀放松一点，我会陪你把这件事慢慢拆开。"
