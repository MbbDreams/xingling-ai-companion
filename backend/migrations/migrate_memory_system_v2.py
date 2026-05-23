#!/usr/bin/env python3
"""
记忆系统数据库迁移脚本 V2 - 更健壮的版本

执行方式:
    cd backend
    python migrations/migrate_memory_system_v2.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings


async def check_table_exists(conn, table_name: str) -> bool:
    """检查表是否存在"""
    result = await conn.execute(
        text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = :table_name
            )
        """),
        {"table_name": table_name}
    )
    return result.scalar()


async def check_column_exists(conn, table_name: str, column_name: str) -> bool:
    """检查字段是否存在"""
    result = await conn.execute(
        text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = :table_name
                AND column_name = :column_name
            )
        """),
        {"table_name": table_name, "column_name": column_name}
    )
    return result.scalar()


async def create_core_memories_table(conn):
    """创建 core_memories 表"""
    print("  创建 core_memories 表...")
    
    # 创建表
    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS core_memories (
            id              BIGSERIAL PRIMARY KEY,
            user_id         BIGINT REFERENCES users(id) ON DELETE CASCADE,
            companion_id    BIGINT REFERENCES companions(id) ON DELETE CASCADE,
            persona_block   TEXT DEFAULT '',
            human_block     TEXT DEFAULT '',
            relationship_block TEXT DEFAULT '',
            last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(user_id, companion_id)
        )
    """))
    
    # 创建索引
    await conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_core_memory_user ON core_memories(user_id)
    """))
    
    print("  ✓ core_memories 表创建成功")


async def create_conversation_summaries_table(conn):
    """创建 conversation_summaries 表"""
    print("  创建 conversation_summaries 表...")
    
    # 创建表
    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS conversation_summaries (
            id              BIGSERIAL PRIMARY KEY,
            conversation_id BIGINT REFERENCES conversations(id) ON DELETE CASCADE,
            user_id         BIGINT REFERENCES users(id) ON DELETE CASCADE,
            summary         TEXT NOT NULL,
            message_range   JSONB DEFAULT '{}',
            created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            is_active       BOOLEAN DEFAULT TRUE
        )
    """))
    
    # 创建索引
    await conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_conv_summaries_conv ON conversation_summaries(conversation_id)
    """))
    
    await conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_conv_summaries_user ON conversation_summaries(user_id)
    """))
    
    print("  ✓ conversation_summaries 表创建成功")


async def alter_memories_table(conn):
    """修改 memories 表"""
    print("  修改 memories 表...")
    
    # 检查并添加字段
    columns_to_add = [
        ("memory_type", "VARCHAR(32) DEFAULT 'general'"),
        ("source", "VARCHAR(32) DEFAULT 'user_told'"),
        ("is_merged", "BOOLEAN DEFAULT FALSE"),
        ("merged_from_ids", "JSONB DEFAULT '[]'"),
        ("expires_at", "TIMESTAMP WITH TIME ZONE"),
    ]
    
    for col_name, col_type in columns_to_add:
        exists = await check_column_exists(conn, "memories", col_name)
        if not exists:
            print(f"    添加字段 {col_name}...")
            await conn.execute(text(f"""
                ALTER TABLE memories ADD COLUMN {col_name} {col_type}
            """))
        else:
            print(f"    字段 {col_name} 已存在，跳过")
    
    # 创建索引
    print("  创建索引...")
    await conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(user_id, memory_type)
    """))
    await conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(user_id, importance DESC)
    """))
    await conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_memories_expires ON memories(expires_at) WHERE expires_at IS NOT NULL
    """))
    
    print("  ✓ memories 表修改完成")


async def init_core_memories(conn):
    """初始化核心记忆"""
    print("  初始化核心记忆...")
    
    await conn.execute(text("""
        INSERT INTO core_memories (user_id, companion_id, persona_block, human_block, relationship_block)
        SELECT 
            c.user_id,
            c.id,
            '晚星是一个温柔体贴的AI伴侣。她善于倾听，总是给予温暖的回应。',
            '',
            '我们刚刚认识，正在建立友谊。'
        FROM companions c
        WHERE NOT EXISTS (
            SELECT 1 FROM core_memories cm WHERE cm.user_id = c.user_id AND cm.companion_id = c.id
        )
    """))
    
    print("  ✓ 核心记忆初始化完成")


async def run_migration():
    """执行数据库迁移"""
    print("=" * 60)
    print("记忆系统数据库迁移 V2")
    print("=" * 60)
    
    engine = create_async_engine(settings.database_url, echo=False)
    
    async with engine.begin() as conn:
        print("\n[1/4] 检查并创建 core_memories 表...")
        try:
            exists = await check_table_exists(conn, "core_memories")
            if exists:
                print("  ✓ core_memories 表已存在，跳过")
            else:
                await create_core_memories_table(conn)
        except Exception as e:
            print(f"  ✗ 失败: {e}")
            raise
        
        print("\n[2/4] 检查并创建 conversation_summaries 表...")
        try:
            exists = await check_table_exists(conn, "conversation_summaries")
            if exists:
                print("  ✓ conversation_summaries 表已存在，跳过")
            else:
                await create_conversation_summaries_table(conn)
        except Exception as e:
            print(f"  ✗ 失败: {e}")
            raise
        
        print("\n[3/4] 修改 memories 表...")
        try:
            await alter_memories_table(conn)
        except Exception as e:
            print(f"  ✗ 失败: {e}")
            raise
        
        print("\n[4/4] 初始化核心记忆...")
        try:
            await init_core_memories(conn)
        except Exception as e:
            print(f"  ✗ 失败: {e}")
            raise
        
        print("\n" + "=" * 60)
        print("迁移完成！")
        print("=" * 60)
        
        # 最终验证
        print("\n验证结果:")
        for table in ["core_memories", "conversation_summaries", "memories"]:
            exists = await check_table_exists(conn, table)
            print(f"  - {table}: {'✓ 存在' if exists else '✗ 不存在'}")
    
    await engine.dispose()
    
    print("\n下一步:")
    print("  1. 重启后端服务")
    print("  2. 测试聊天功能")


if __name__ == "__main__":
    try:
        asyncio.run(run_migration())
    except Exception as e:
        print(f"\n迁移失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
