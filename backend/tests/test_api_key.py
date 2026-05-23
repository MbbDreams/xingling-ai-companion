"""
快速测试 DeepSeek API Key 是否可用
运行方式：
    cd backend
    .venv/bin/python tests/test_api_key.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from langchain_openai import ChatOpenAI

def test_api_key():
    api_key = os.getenv("OPENAI_API_KEY", "")
    model = os.getenv("OPENAI_MODEL", "deepseek-chat")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")

    print("=" * 50)
    print("DeepSeek API Key 连通性测试")
    print("=" * 50)
    print(f"  API Key:  {api_key[:8]}...{api_key[-4:]}")
    print(f"  模型:     {model}")
    print(f"  Base URL: {base_url}")
    print()

    if not api_key or api_key == "sk-你的deepseek-api-key填在这里":
        print("❌ API Key 未配置！请先编辑 backend/.env 文件")
        return False

    try:
        print("⏳ 正在连接 DeepSeek...")
        llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=0.7,
            max_tokens=100,
        )

        print("⏳ 正在发送测试消息...")
        response = llm.invoke("你好，请用一句话介绍你自己")

        print()
        print("✅ API Key 有效！连接成功！")
        print(f"  模型回复: {response.content}")
        print()
        return True

    except Exception as e:
        print()
        print(f"❌ 连接失败: {e}")
        print()
        print("常见问题排查：")
        print("  1. 检查 API Key 是否正确")
        print("  2. 检查网络是否能访问 api.deepseek.com")
        print("  3. 检查账户余额是否充足")
        print("  4. 检查 .env 文件路径是否正确")
        return False


if __name__ == "__main__":
    success = test_api_key()
    sys.exit(0 if success else 1)
