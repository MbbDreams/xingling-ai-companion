"""
认证模块数据库迁移 - 添加用户认证和个人信息字段
运行: python migrate_auth.py
"""

import asyncio
from sqlalchemy import text
from app.core.database import engine


async def migrate_auth():
    """添加认证相关字段"""
    
    migrations = [
        # users 表
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(20) UNIQUE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255) UNIQUE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS hashed_password VARCHAR(255)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS gender VARCHAR(20)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS birthday DATE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS bio TEXT",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS location VARCHAR(100)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS website VARCHAR(255)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP WITH TIME ZONE",
        
        # 添加索引
        "CREATE INDEX IF NOT EXISTS ix_users_phone ON users(phone)",
        "CREATE INDEX IF NOT EXISTS ix_users_email ON users(email)",
    ]
    
    async with engine.begin() as conn:
        print("开始认证模块数据库迁移...")
        
        for i, sql in enumerate(migrations, 1):
            try:
                await conn.execute(text(sql))
                print(f"✓ [{i}/{len(migrations)}] 执行成功")
            except Exception as e:
                if "already exists" in str(e) or "already" in str(e).lower():
                    print(f"○ [{i}/{len(migrations)}] 字段已存在，跳过")
                else:
                    print(f"✗ [{i}/{len(migrations)}] 错误: {e}")
        
        print("\n✅ 认证模块数据库迁移完成！")


if __name__ == "__main__":
    asyncio.run(migrate_auth())
