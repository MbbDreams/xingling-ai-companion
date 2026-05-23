"""
数据库初始化脚本 - 创建所有表结构
运行: python init_db.py
"""

import asyncio
from sqlalchemy import text
from app.core.database import engine, Base
from app.models.entities import (
    User, Companion, Conversation, Message,
    Memory, DiaryEntry, GrowthMilestone,
    ShopItem, UserItem, AnalyticsEvent
)


async def init_database():
    """初始化数据库 - 创建所有表"""
    
    print("=" * 50)
    print("  星灵 AI 伴侣 - 数据库初始化")
    print("=" * 50)
    print()
    
    async with engine.begin() as conn:
        # 检查表是否存在
        result = await conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """))
        existing_tables = {row[0] for row in result.fetchall()}
        
        if existing_tables:
            print(f"⚠️  发现已有表: {', '.join(sorted(existing_tables))}")
            print()
            response = input("是否删除现有表并重新创建? (yes/no): ")
            if response.lower() != 'yes':
                print("\n❌ 操作已取消")
                return
            
            print("\n🗑️  删除现有表...")
            await conn.run_sync(Base.metadata.drop_all)
            print("✅ 现有表已删除")
        
        print("\n📦 创建新表...")
        await conn.run_sync(Base.metadata.create_all)
        
        # 验证创建结果
        result = await conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        created_tables = [row[0] for row in result.fetchall()]
        
        print()
        print("✅ 以下表已创建:")
        for table in created_tables:
            print(f"   • {table}")
        
        print()
        print("=" * 50)
        print("  数据库初始化完成!")
        print("=" * 50)


async def check_tables():
    """检查现有表结构"""
    
    print("\n📋 当前数据库表结构:")
    print("-" * 50)
    
    async with engine.begin() as conn:
        result = await conn.execute(text("""
            SELECT table_name, column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
        """))
        
        current_table = None
        for row in result.fetchall():
            table, column, dtype, nullable = row
            if table != current_table:
                current_table = table
                print(f"\n📁 {table}")
            nullable_str = "NULL" if nullable == "YES" else "NOT NULL"
            print(f"   • {column}: {dtype} ({nullable_str})")
    
    print()


async def seed_data():
    """插入初始数据"""
    
    from sqlalchemy import select
    from app.models.entities import ShopItem
    
    print("\n🌱 插入初始数据...")
    
    async with engine.begin() as conn:
        # 检查是否已有商品
        result = await conn.execute(select(ShopItem).limit(1))
        if result.scalar_one_or_none():
            print("⚠️  已有商品数据，跳过")
            return
        
        # 插入默认商品
        default_items = [
            # 服装
            {"name": "默认服装", "category": "outfit", "price": 0, "description": "经典默认装扮"},
            {"name": "星空礼服", "category": "outfit", "price": 100, "description": "闪耀的星空主题服装"},
            {"name": "月光长裙", "category": "outfit", "price": 150, "description": "优雅的月光系列"},
            # 场景
            {"name": "默认房间", "category": "scene", "price": 0, "description": "温馨的起居室"},
            {"name": "星空露台", "category": "scene", "price": 200, "description": "可以仰望星空的露台"},
            {"name": "樱花庭院", "category": "scene", "price": 250, "description": "落英缤纷的日式庭院"},
            # 语音
            {"name": "温柔女声", "category": "voice", "price": 0, "description": "默认温柔女声"},
            {"name": "活泼少女", "category": "voice", "price": 300, "description": "元气满满的少女音"},
            # VIP
            {"name": "星灵 Pro", "category": "vip", "price": 999, "description": "解锁全部特权"},
        ]
        
        for item_data in default_items:
            await conn.execute(
                text("""
                    INSERT INTO shop_items (name, category, price, description, is_active)
                    VALUES (:name, :category, :price, :description, true)
                """),
                item_data
            )
        
        print(f"✅ 已插入 {len(default_items)} 个默认商品")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "check":
            asyncio.run(check_tables())
        elif command == "seed":
            asyncio.run(seed_data())
        else:
            print("用法: python init_db.py [check|seed]")
            print("  check - 检查现有表结构")
            print("  seed  - 插入初始数据")
    else:
        # 默认执行完整初始化
        asyncio.run(init_database())
        asyncio.run(seed_data())
