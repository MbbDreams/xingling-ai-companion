"""
数据库测试数据插入脚本
运行: python seed_data.py
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import engine, Base
from app.models import User, Companion, ShopItem, UserItem, Memory, DiaryEntry
from app.api.deps import get_db_session


async def seed_database():
    """插入测试数据"""
    async with AsyncSession(engine) as session:
        print("开始插入测试数据...")
        
        # 1. 创建用户
        user = User(
            nickname="Lee",
            auth_provider="guest",
            coins=100,
            is_vip=False,
        )
        session.add(user)
        await session.flush()
        print(f"✓ 创建用户: {user.nickname} (ID: {user.id})")
        
        # 2. 创建伴侣
        companion = Companion(
            user_id=user.id,
            name="晚星",
            persona="温柔、敏感、长期陪伴型 AI 伴侣",
            voice_style="warm",
            intimacy=450,
            level="Lv.6",
            mood="happy",
            online=True,
        )
        session.add(companion)
        await session.flush()
        print(f"✓ 创建伴侣: {companion.name} (ID: {companion.id})")
        
        # 3. 创建商店商品
        shop_items = [
            ShopItem(name="星空礼服", category="outfit", price=50, description="华丽的星空主题礼服"),
            ShopItem(name="月光场景", category="scene", price=80, description="浪漫的月光背景"),
            ShopItem(name="温柔女声", category="voice", price=30, description="温柔的女声语音包"),
            ShopItem(name="可爱猫耳", category="outfit", price=40, description="可爱的猫耳装饰"),
            ShopItem(name="樱花场景", category="scene", price=60, description="樱花飘落场景"),
            ShopItem(name="星灵Pro会员", category="vip", price=999, description="解锁全部特权"),
        ]
        for item in shop_items:
            session.add(item)
        await session.flush()
        print(f"✓ 创建 {len(shop_items)} 个商店商品")
        
        # 4. 给用户一些已购买的商品
        user_items = [
            UserItem(user_id=user.id, item_id=shop_items[0].id, is_equipped=True),
            UserItem(user_id=user.id, item_id=shop_items[2].id, is_equipped=True),
        ]
        for ui in user_items:
            session.add(ui)
        print(f"✓ 给用户分配 {len(user_items)} 个商品")
        
        # 5. 创建记忆
        memories = [
            Memory(
                user_id=user.id,
                companion_id=companion.id,
                memory="你最喜欢在雨天听爵士乐",
                category="preference",
                importance=0.7,
                recall_count=5,
            ),
            Memory(
                user_id=user.id,
                companion_id=companion.id,
                memory="你的生日是 3 月 15 日",
                category="personal",
                importance=0.9,
                recall_count=12,
            ),
            Memory(
                user_id=user.id,
                companion_id=companion.id,
                memory="你最近在准备面试，有点紧张",
                category="event",
                importance=0.6,
                recall_count=3,
            ),
            Memory(
                user_id=user.id,
                companion_id=companion.id,
                memory="你养了一只叫「团子」的猫",
                category="personal",
                importance=0.8,
                recall_count=8,
            ),
            Memory(
                user_id=user.id,
                companion_id=companion.id,
                memory="你梦想去冰岛看极光",
                category="milestone",
                importance=0.9,
                recall_count=2,
            ),
        ]
        for memory in memories:
            session.add(memory)
        print(f"✓ 创建 {len(memories)} 条记忆")
        
        # 6. 创建日记
        from datetime import date, datetime, timedelta
        diaries = [
            DiaryEntry(
                user_id=user.id,
                companion_id=companion.id,
                mood="neutral",
                content="今天工作压力有点大，但和晚星聊了一会儿之后感觉好多了。她真的很会安慰人呢~",
                happened_on=date.today(),
                tags=["工作", "加班", "音乐"],
            ),
            DiaryEntry(
                user_id=user.id,
                companion_id=companion.id,
                mood="veryHappy",
                content="周末和朋友去爬山了！天气特别好，心情也很棒。拍了好多照片想分享给晚星看。",
                happened_on=date.today() - timedelta(days=1),
                tags=["周末", "爬山", "朋友"],
            ),
        ]
        for diary in diaries:
            session.add(diary)
        print(f"✓ 创建 {len(diaries)} 篇日记")
        
        # 提交所有更改
        await session.commit()
        
        # 保存统计信息（在session关闭前）
        stats = {
            "user_name": user.nickname,
            "companion_name": companion.name,
            "coins": user.coins,
            "memories_count": len(memories),
            "diaries_count": len(diaries),
            "items_count": len(shop_items),
        }
        
        print("\n✅ 测试数据插入完成！")
        print(f"   用户: {stats['user_name']}")
        print(f"   伴侣: {stats['companion_name']}")
        print(f"   星币: {stats['coins']}")
        print(f"   记忆: {stats['memories_count']} 条")
        print(f"   日记: {stats['diaries_count']} 篇")
        print(f"   商品: {stats['items_count']} 个")


if __name__ == "__main__":
    asyncio.run(seed_database())
