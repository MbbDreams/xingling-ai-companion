MEMORY_HINTS = ["我喜欢", "我讨厌", "我正在", "我准备", "我想", "我养", "我叫", "我的"]


def extract_memory_candidates(text: str) -> list[str]:
    compact = " ".join(text.strip().split())
    if not compact:
        return []
    if any(hint in compact for hint in MEMORY_HINTS):
        return [compact[:240]]
    return []
