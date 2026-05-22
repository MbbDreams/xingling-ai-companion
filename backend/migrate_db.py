"""
数据库迁移脚本 - 添加缺失的列
运行: python migrate_db.py
"""

import asyncio
from sqlalchemy import text
from app.core.database import engine


async def migrate_database():
    """添加缺失的数据库列"""
    
    migrations = [
        # users 表
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS coins INTEGER DEFAULT 100",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_vip BOOLEAN DEFAULT FALSE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS vip_expire_at TIMESTAMP WITH TIME ZONE",
        
        # companions 表
        "ALTER TABLE companions ADD COLUMN IF NOT EXISTS current_outfit_id INTEGER",
        "ALTER TABLE companions ADD COLUMN IF NOT EXISTS current_scene_id INTEGER",
        "ALTER TABLE companions ADD COLUMN IF NOT EXISTS mood VARCHAR(32) DEFAULT 'happy'",
        "ALTER TABLE companions ADD COLUMN IF NOT EXISTS online BOOLEAN DEFAULT TRUE",
        
        # memories 表
        "ALTER TABLE memories ADD COLUMN IF NOT EXISTS recall_count INTEGER DEFAULT 0",
        "ALTER TABLE memories ADD COLUMN IF NOT EXISTS last_recalled_at TIMESTAMP WITH TIME ZONE",
        
        # diary_entries 表
        "ALTER TABLE diary_entries ADD COLUMN IF NOT EXISTS tags JSONB DEFAULT '[]'::jsonb",
        
        # shop_items 表
        "ALTER TABLE shop_items ADD COLUMN IF NOT EXISTS description TEXT",
        "ALTER TABLE shop_items ADD COLUMN IF NOT EXISTS asset_url TEXT",
        "ALTER TABLE shop_items ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE",
        "ALTER TABLE shop_items ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
    ]
    
    async with engine.begin() as conn:
        print("开始数据库迁移...")
        
        for i, sql in enumerate(migrations, 1):
            try:
                await conn.execute(text(sql))
                print(f"✓ [{i}/{len(migrations)}] 执行成功")
            except Exception as e:
                # 忽略"列已存在"的错误
                if "already exists" in str(e) or "already" in str(e).lower():
                    print(f"○ [{i}/{len(migrations)}] 列已存在，跳过")
                else:
                    print(f"✗ [{i}/{len(migrations)}] 错误: {e}")
        
        # 创建 user_items 表（如果不存在）
        create_user_items = """
        CREATE TABLE IF NOT EXISTS user_items (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            item_id BIGINT NOT NULL REFERENCES shop_items(id) ON DELETE CASCADE,
            is_equipped BOOLEAN DEFAULT FALSE,
            purchased_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
        """
        try:
            await conn.execute(text(create_user_items))
            print("✓ 创建 user_items 表")
        except Exception as e:
            if "already exists" in str(e):
                print("○ user_items 表已存在")
            else:
                print(f"✗ 创建 user_items 表失败: {e}")
        
        # 创建索引
        indexes = [
            "CREATE INDEX IF NOT EXISTS ix_user_items_user_id ON user_items(user_id)",
            "CREATE INDEX IF NOT EXISTS ix_user_items_item_id ON user_items(item_id)",
        ]
        for idx_sql in indexes:
            try:
                await conn.execute(text(idx_sql))
            except:
                pass
        
        print("\n✅ 数据库迁移完成！")


if __name__ == "__main__":
    asyncio.run(migrate_database())
