from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "local"
    api_prefix: str = "/api/v1"
    database_url: str = "postgresql+asyncpg://xingling:xingling_dev@localhost:5433/xingling_ai"
    redis_url: str = "redis://localhost:6380/0"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
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

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


# 导出 settings 实例供其他模块直接使用
settings = get_settings()
