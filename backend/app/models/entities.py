from __future__ import annotations

from datetime import date, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, Boolean, Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    
    # 认证信息
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, index=True)  # 手机号
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)  # 邮箱
    hashed_password: Mapped[str | None] = mapped_column(String(255))  # 加密后的密码
    auth_provider: Mapped[str] = mapped_column(String(30), default="guest")  # 认证方式
    provider_user_id: Mapped[str | None] = mapped_column(String(191))  # 第三方用户ID
    
    # 基本信息
    nickname: Mapped[str] = mapped_column(String(50), default="Lee")
    avatar: Mapped[str | None] = mapped_column(Text)
    gender: Mapped[str | None] = mapped_column(String(20))  # male/female/other
    birthday: Mapped[date | None] = mapped_column(Date)
    bio: Mapped[str | None] = mapped_column(Text)  # 个人简介
    location: Mapped[str | None] = mapped_column(String(100))  # 所在地
    website: Mapped[str | None] = mapped_column(String(255))  # 个人网站
    
    # 货币和会员
    coins: Mapped[int] = mapped_column(Integer, default=100)  # 星币余额
    is_vip: Mapped[bool] = mapped_column(Boolean, default=False)
    vip_expire_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    
    # 时间戳
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    
    # 关系
    companions: Mapped[list[Companion]] = relationship(back_populates="user", cascade="all, delete-orphan")
    user_items: Mapped[list[UserItem]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Companion(TimestampMixin, Base):
    __tablename__ = "companions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(50), default="晚星")
    persona: Mapped[str] = mapped_column(Text, default="温柔、敏感、长期陪伴型 AI 伴侣")
    voice_style: Mapped[str] = mapped_column(String(50), default="warm")
    intimacy: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[str] = mapped_column(String(20), default="Lv.1")
    current_outfit_id: Mapped[int | None] = mapped_column(ForeignKey("shop_items.id"), nullable=True)
    current_scene_id: Mapped[int | None] = mapped_column(ForeignKey("shop_items.id"), nullable=True)
    mood: Mapped[str] = mapped_column(String(32), default="happy")  # 当前心情
    online: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped[User] = relationship(back_populates="companions")
    conversations: Mapped[list[Conversation]] = relationship(back_populates="companion")


class Conversation(TimestampMixin, Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    companion_id: Mapped[int] = mapped_column(ForeignKey("companions.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(100), default="新的聊天")

    companion: Mapped[Companion] = relationship(back_populates="conversations")
    messages: Mapped[list[Message]] = relationship(back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    emotion: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    conversation: Mapped[Conversation] = relationship(back_populates="messages")


class Memory(TimestampMixin, Base):
    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    companion_id: Mapped[int | None] = mapped_column(ForeignKey("companions.id", ondelete="CASCADE"), index=True)
    source_message_id: Mapped[int | None] = mapped_column(ForeignKey("messages.id", ondelete="SET NULL"))
    memory: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50), default="general")
    importance: Mapped[float] = mapped_column(Float, default=0.5)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))
    recall_count: Mapped[int] = mapped_column(Integer, default=0)  # 被回忆次数
    last_recalled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DiaryEntry(TimestampMixin, Base):
    __tablename__ = "diary_entries"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    companion_id: Mapped[int | None] = mapped_column(ForeignKey("companions.id", ondelete="SET NULL"), index=True)
    mood: Mapped[str] = mapped_column(String(32), default="calm")
    content: Mapped[str] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    happened_on: Mapped[date] = mapped_column(Date, default=date.today)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)  # 标签列表


class GrowthMilestone(Base):
    __tablename__ = "growth_milestones"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    companion_id: Mapped[int | None] = mapped_column(ForeignKey("companions.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    achieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ShopItem(Base):
    __tablename__ = "shop_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(50), index=True)  # outfit, scene, voice, prop, vip
    price: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str | None] = mapped_column(Text)
    asset_url: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UserItem(Base):
    """用户拥有的商品"""
    __tablename__ = "user_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("shop_items.id", ondelete="CASCADE"), index=True)
    is_equipped: Mapped[bool] = mapped_column(Boolean, default=False)
    purchased_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="user_items")
    item: Mapped[ShopItem] = relationship()


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    event_name: Mapped[str] = mapped_column(String(100), index=True)
    properties: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
