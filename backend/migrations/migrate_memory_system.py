#!/usr/bin/env python3
"""
记忆系统数据库迁移脚本

执行方式:
    cd backend
    python migrations/migrate_memory_system.py

功能:
    1. 创建 core_memories 表（核心记忆）
    2. 创建 conversation_summaries 表（对话摘要）
    3. 修改 memories 表（增加字段）
    4. 初始化现有用户的核心记忆
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


# 迁移 SQL 语句
MIGRATION_SQL = """
-- 1. 创建核心记忆表
CREATE TABLE IF NOT EXISTS core_memories (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT REFERENCES users(id) ON DELETE CASCADE,
    companion_id    BIGINT REFERENCES companions(id) ON DELETE CASCADE,
    
    -- 核心记忆分区
    persona_block   TEXT DEFAULT '',
    human_block     TEXT DEFAULT '',
    relationship_block TEXT DEFAULT '',
    
    -- 元数据
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, companion_id)
);

CREATE INDEX IF NOT EXISTS idx_core_memory_user ON core_memories(user_id);

-- 2. 创建对话摘要表
CREATE TABLE IF NOT EXISTS conversation_summaries (
    id              BIGSERIAL PRIMARY KEY,
    conversation_id BIGINT REFERENCES conversations(id) ON DELETE CASCADE,
    user_id         BIGINT REFERENCES users(id) ON DELETE CASCADE,
    
    -- 摘要内容
    summary         TEXT NOT NULL,
    message_range   JSONB DEFAULT '{}',
    
    -- 元数据
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active       BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_conv_summaries_conv ON conversation_summaries(conversation_id);
CREATE INDEX IF NOT EXISTS idx_conv_summaries_user ON conversation_summaries(user_id);

-- 3. 修改 memories 表 - 增加字段
ALTER TABLE memories ADD COLUMN IF NOT EXISTS memory_type VARCHAR(32) DEFAULT 'general';
ALTER TABLE memories ADD COLUMN IF NOT EXISTS source VARCHAR(32) DEFAULT 'user_told';
ALTER TABLE memories ADD COLUMN IF NOT EXISTS is_merged BOOLEAN DEFAULT FALSE;
ALTER TABLE memories ADD COLUMN IF NOT EXISTS merged_from_ids JSONB DEFAULT '[]';
ALTER TABLE memories ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP WITH TIME ZONE;

-- 4. 创建索引
CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(user_id, memory_type);
CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(user_id, importance DESC);
CREATE INDEX IF NOT EXISTS idx_memories_expires ON memories(expires_at) WHERE expires_at IS NOT NULL;
"""

INIT_CORE_MEMORY_SQL = """
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
);
"""


async def run_migration():
    """执行数据库迁移"""
    print("=" * 60)
    print("记忆系统数据库迁移")
    print("=" * 60)
    
    # 创建数据库引擎
    engine = create_async_engine(
        settings.database_url,
        echo=False,
    )
    
    async with engine.begin() as conn:
        print("\n[1/3] 创建新表和修改表结构...")
        try:
            # 执行迁移 SQL
            await conn.execute(text(MIGRATION_SQL))
            print("✓ 表结构迁移完成")
        except Exception as e:
            print(f"✗ 表结构迁移失败: {e}")
            raise
        
        print("\n[2/3] 初始化核心记忆...")
        try:
            result = await conn.execute(text(INIT_CORE_MEMORY_SQL))
            print(f"✓ 核心记忆初始化完成，影响了 {result.rowcount} 条记录")
        except Exception as e:
            print(f"✗ 核心记忆初始化失败: {e}")
            raise
        
        print("\n[3/3] 验证迁移结果...")
        try:
            # 检查 core_memories 表
            result = await conn.execute(text("SELECT COUNT(*) FROM core_memories"))
            core_count = result.scalar()
            print(f"  - core_memories 表: {core_count} 条记录")
            
            # 检查 conversation_summaries 表
            result = await conn.execute(text("SELECT COUNT(*) FROM conversation_summaries"))
            summary_count = result.scalar()
            print(f"  - conversation_summaries 表: {summary_count} 条记录")
            
            # 检查 memories 表的新字段
            result = await conn.execute(text("SELECT COUNT(*) FROM memories"))
            memory_count = result.scalar()
            print(f"  - memories 表: {memory_count} 条记录（已添加新字段）")
            
            print("\n✓ 迁移验证通过")
            
        except Exception as e:
            print(f"✗ 验证失败: {e}")
            raise
    
    await engine.dispose()
    
    print("\n" + "=" * 60)
    print("迁移完成！")
    print("=" * 60)
    print("\n下一步:")
    print("  1. 在 .env 文件中配置 EMBEDDING_API_KEY（见下方说明）")
    print("  2. 重启后端服务")
    print("  3. 重新构建 Flutter 应用")


if __name__ == "__main__":
    try:
        asyncio.run(run_migration())
    except Exception as e:
        print(f"\n迁移失败: {e}")
        sys.exit(1)
