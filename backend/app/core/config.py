from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# .env 文件路径：config.py 在 backend/app/core/ 下，parents[2] = backend/
_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    app_env: str = "local"
    api_prefix: str = "/api/v1"
    database_url: str = "postgresql+asyncpg://xingling:xingling_dev@localhost:5433/xingling_ai"
    redis_url: str = "redis://localhost:6380/0"
    
    # DeepSeek API 配置（聊天模型）
    deepseek_api_key: str = ""  # DeepSeek API Key
    deepseek_model: str = "deepseek-chat"  # 默认使用 deepseek-chat
    deepseek_base_url: str = "https://api.deepseek.com/v1"  # DeepSeek API 地址
    
    # 兼容旧配置（用于平滑迁移）
    openai_api_key: str = ""  # 兼容旧配置，实际使用 deepseek_api_key
    openai_model: str = "deepseek-chat"  # 兼容旧配置
    openai_base_url: str = "https://api.deepseek.com/v1"  # 兼容旧配置
    
    cors_origins_raw: str = Field(
        default="http://localhost:4173,http://127.0.0.1:4173,http://localhost:3000,http://127.0.0.1:3000,http://localhost:5000,http://127.0.0.1:5000,http://localhost:8000,http://127.0.0.1:8000,*",
        validation_alias="CORS_ORIGINS",
    )
    
    # JWT 配置
    secret_key: str = Field(
        default="your-secret-key-here-change-in-production",
        validation_alias="SECRET_KEY"
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24小时
    refresh_token_expire_days: int = 30
    
    # Embedding 配置（豆包/火山引擎）
    embedding_api_key: str = ""  # 豆包 API Key (ARK_API_KEY)
    embedding_model: str = "doubao-embedding-text-240715"  # 默认豆包文本模型
    
    # 记忆系统配置
    memory_summary_threshold: int = 12  # 触发摘要的消息数阈值
    memory_keep_recent: int = 6  # 滑动窗口保留消息数
    memory_max_retrieve: int = 5  # 最大检索记忆条数
    memory_cleanup_interval: int = 86400  # 记忆清理间隔（秒）

    model_config = SettingsConfigDict(env_file=str(_ENV_PATH), env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]
    
    @property
    def llm_api_key(self) -> str:
        """获取 LLM API Key（优先使用 deepseek_api_key，兼容 openai_api_key）"""
        return self.deepseek_api_key or self.openai_api_key
    
    @property
    def llm_model(self) -> str:
        """获取 LLM 模型（优先使用 deepseek_model，兼容 openai_model）"""
        return self.deepseek_model or self.openai_model
    
    @property
    def llm_base_url(self) -> str:
        """获取 LLM Base URL（优先使用 deepseek_base_url，兼容 openai_base_url）"""
        return self.deepseek_base_url or self.openai_base_url


@lru_cache
def get_settings() -> Settings:
    return Settings()


# 导出 settings 实例供其他模块直接使用
settings = get_settings()
