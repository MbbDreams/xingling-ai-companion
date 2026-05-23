from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# .env 文件路径：优先当前目录，其次 backend 目录
_ENV_PATH = Path(".env").resolve()
if not _ENV_PATH.exists():
    _ENV_PATH = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    app_env: str = "local"
    api_prefix: str = "/api/v1"
    database_url: str = "postgresql+asyncpg://xingling:xingling_dev@localhost:5433/xingling_ai"
    redis_url: str = "redis://localhost:6380/0"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_base_url: str = ""  # 留空则使用 OpenAI 默认地址，DeepSeek 填 https://api.deepseek.com/v1
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
    
    # Embedding 配置（用于记忆向量化）
    embedding_api_key: str = ""  # 留空则使用 openai_api_key
    embedding_base_url: str = ""  # 留空则使用 OpenAI 默认地址
    embedding_model: str = "text-embedding-3-small"
    
    # 记忆系统配置
    memory_summary_threshold: int = 12  # 触发摘要的消息数阈值
    memory_keep_recent: int = 6  # 滑动窗口保留消息数
    memory_max_retrieve: int = 5  # 最大检索记忆条数
    memory_cleanup_interval: int = 86400  # 记忆清理间隔（秒）

    model_config = SettingsConfigDict(env_file=str(_ENV_PATH), env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


# 导出 settings 实例供其他模块直接使用
settings = get_settings()
