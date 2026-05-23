#!/usr/bin/env python3
"""
验证记忆系统数据库迁移结果

执行方式:
    cd backend
    python migrations/check_migration.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings


async def check_migration():
    """检查迁移状态"""
    print("=" * 60)
    print("记忆系统数据库迁移检查")
    print("=" * 60)
    
    engine = create_async_engine(settings.database_url, echo=False)
    
    async with engine.connect() as conn:
        # 1. 检查 core_memories 表
        print("\n[1/5] 检查 core_memories 表...")
        try:
            result = await conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'core_memories'
            """))
            columns = result.fetchall()
            if columns:
                print(f"✓ 表存在，字段数: {len(columns)}")
                for col in columns:
                    print(f"  - {col[0]}: {col[1]}")
            else:
                print("✗ 表不存在或没有字段")
        except Exception as e:
            print(f"✗ 检查失败: {e}")
        
        # 2. 检查 conversation_summaries 表
        print("\n[2/5] 检查 conversation_summaries 表...")
        try:
            result = await conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'conversation_summaries'
            """))
            columns = result.fetchall()
            if columns:
                print(f"✓ 表存在，字段数: {len(columns)}")
                for col in columns:
                    print(f"  - {col[0]}: {col[1]}")
            else:
                print("✗ 表不存在或没有字段")
        except Exception as e:
            print(f"✗ 检查失败: {e}")
        
        # 3. 检查 memories 表的新字段
        print("\n[3/5] 检查 memories 表新字段...")
        try:
            result = await conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'memories' 
                AND column_name IN ('memory_type', 'source', 'is_merged', 'merged_from_ids', 'expires_at')
            """))
            columns = result.fetchall()
            if columns:
                print(f"✓ 新字段已添加，共 {len(columns)} 个:")
                for col in columns:
                    print(f"  - {col[0]}: {col[1]}")
            else:
                print("✗ 新字段未找到")
        except Exception as e:
            print(f"✗ 检查失败: {e}")
        
        # 4. 检查索引
        print("\n[4/5] 检查索引...")
        try:
            result = await conn.execute(text("""
                SELECT indexname, tablename 
                FROM pg_indexes 
                WHERE tablename IN ('core_memories', 'conversation_summaries', 'memories')
                AND indexname LIKE 'idx_%'
            """))
            indexes = result.fetchall()
            print(f"✓ 找到 {len(indexes)} 个索引:")
            for idx in indexes:
                print(f"  - {idx[0]} (表: {idx[1]})")
        except Exception as e:
            print(f"✗ 检查失败: {e}")
        
        # 5. 检查数据
        print("\n[5/5] 检查数据...")
        try:
            # core_memories 记录数
            result = await conn.execute(text("SELECT COUNT(*) FROM core_memories"))
            core_count = result.scalar()
            print(f"  - core_memories: {core_count} 条记录")
            
            # conversation_summaries 记录数
            result = await conn.execute(text("SELECT COUNT(*) FROM conversation_summaries"))
            summary_count = result.scalar()
            print(f"  - conversation_summaries: {summary_count} 条记录")
            
            # memories 记录数
            result = await conn.execute(text("SELECT COUNT(*) FROM memories"))
            memory_count = result.scalar()
            print(f"  - memories: {memory_count} 条记录")
            
            # 检查 memories 的 memory_type 分布
            result = await conn.execute(text("""
                SELECT memory_type, COUNT(*) 
                FROM memories 
                GROUP BY memory_type
            """))
            type_dist = result.fetchall()
            if type_dist:
                print(f"  - memories 类型分布:")
                for t, c in type_dist:
                    print(f"    {t}: {c}")
            
        except Exception as e:
            print(f"✗ 检查失败: {e}")
    
    await engine.dispose()
    
    print("\n" + "=" * 60)
    print("检查完成!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(check_migration())
    except Exception as e:
        print(f"\n检查失败: {e}")
        sys.exit(1)
