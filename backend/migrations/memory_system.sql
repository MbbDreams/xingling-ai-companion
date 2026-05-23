-- 记忆系统数据库迁移脚本
-- 执行方式: psql -U xingling -d xingling_ai -f migrations/memory_system.sql

-- 1. 创建核心记忆表
CREATE TABLE IF NOT EXISTS core_memories (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT REFERENCES users(id) ON DELETE CASCADE,
    companion_id    BIGINT REFERENCES companions(id) ON DELETE CASCADE,
    
    -- 核心记忆分区
    persona_block   TEXT DEFAULT '',    -- 角色设定（静态）
    human_block     TEXT DEFAULT '',    -- 用户画像摘要（动态）
    relationship_block TEXT DEFAULT '', -- 关系状态摘要（动态）
    
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
    message_range   JSONB DEFAULT '{}',  -- {"start_id": 1, "end_id": 15, "count": 15}
    
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

-- 5. 为 embedding 创建向量索引（IVFFlat）
-- 注意：需要先确保表中有足够的数据（建议 > 1000 行）才能创建有效的 IVFFlat 索引
-- 如果数据量小，可以先不创建，等数据量上来后再创建
-- CREATE INDEX IF NOT EXISTS idx_memories_embedding ON memories 
-- USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- 6. 初始化现有用户的核心记忆
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

-- 完成
SELECT 'Memory system migration completed successfully!' AS status;
