EMOTION_KEYWORDS = {
    "sad": ["难过", "伤心", "崩溃", "委屈", "哭"],
    "anxious": ["焦虑", "紧张", "担心", "害怕", "压力"],
    "angry": ["生气", "烦", "愤怒", "气死"],
    "tired": ["累", "疲惫", "困", "加班", "熬夜"],
    "happy": ["开心", "高兴", "快乐", "顺利", "喜欢"],
    "lonely": ["孤独", "没人", "一个人", "寂寞"],
}


def classify_emotion(text: str) -> str:
    for emotion, keywords in EMOTION_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return emotion
    return "calm"
