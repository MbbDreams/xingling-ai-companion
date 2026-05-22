# 星灵AI伴侣 — Flutter 前端功能需求文档

> 版本：v1.0  
> 日期：2026-05-22  
> 状态：待后端对接

---

## 一、文档说明

本文档基于 Flutter 前端已实现的页面和功能，梳理出**后端需要提供的全部 API 接口**。前端当前使用 Mock 数据运行，后续将替换为真实 API 调用。

### 术语约定

| 术语 | 说明 |
|------|------|
| `user_id` | 当前登录用户 ID（后续接入鉴权后通过 Token 获取） |
| `companion_id` | 当前用户的 AI 伴侣 ID |
| `conversation_id` | 会话 ID，首次聊天时由后端自动创建 |

### 通用约定

- **Base URL**: `http://<服务器地址>:8000/api/v1`
- **Content-Type**: `application/json`
- **鉴权**: 当前所有接口通过 `user_id` 参数传递，后续改为 Bearer Token
- **分页**: 列表接口统一支持 `page`（页码，从1开始）和 `page_size`（每页条数，默认20）
- **错误响应**: 统一格式 `{ "detail": "错误描述" }`

---

## 二、全局接口

### 2.1 健康检查

```
GET /health
```

**响应**:
```json
{ "status": "ok" }
```

---

## 三、聊天模块

### 3.1 发送聊天消息

```
POST /api/v1/chat/send
```

**前端使用场景**: 用户在聊天页输入消息并发送，前端需要获取 AI 回复、情绪识别结果。

**请求体**:
```json
{
  "message": "今天加班到很晚，有点累...",
  "conversation_id": null
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| message | string | ✅ | 用户消息内容，1~4000 字符 |
| conversation_id | int | ❌ | 会话 ID，首次为 null，后续使用返回值 |

**响应体**:
```json
{
  "conversation_id": 1,
  "reply": "辛苦你了呢 💫 要不要我陪你聊会儿？",
  "emotion": "calm",
  "memory_candidates": ["用户今天加班了", "用户感到疲惫"],
  "intimacy_gained": 2,
  "messages": [
    {
      "id": 1,
      "conversation_id": 1,
      "role": "user",
      "content": "今天加班到很晚，有点累...",
      "emotion": null,
      "created_at": "2026-05-22T20:30:00Z"
    },
    {
      "id": 2,
      "conversation_id": 1,
      "role": "assistant",
      "content": "辛苦你了呢 💫 要不要我陪你聊会儿？",
      "emotion": "calm",
      "created_at": "2026-05-22T20:30:01Z"
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| conversation_id | int | 会话 ID（前端需保存，后续消息带上） |
| reply | string | AI 回复文本 |
| emotion | string | 检测到的用户情绪：happy / calm / sad / anxious / angry / neutral |
| memory_candidates | string[] | 后端建议保存的记忆片段（前端可选择性展示） |
| intimacy_gained | int | 本次对话获得的亲密度 |
| messages | array | 完整的消息列表（含历史） |

### 3.2 获取聊天历史

> ⚠️ **当前后端缺失，需要新增**

```
GET /api/v1/chat/history
```

**前端使用场景**: 进入聊天页时加载历史消息。

**查询参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| conversation_id | int | ✅ | 会话 ID |
| page | int | ❌ | 页码，默认 1 |
| page_size | int | ❌ | 每页条数，默认 20 |

**响应体**:
```json
{
  "conversation_id": 1,
  "total": 42,
  "messages": [
    {
      "id": 1,
      "conversation_id": 1,
      "role": "assistant",
      "content": "晚上好呀，今天过得怎么样？",
      "emotion": "happy",
      "created_at": "2026-05-22T18:00:00Z"
    }
  ]
}
```

### 3.3 获取快捷回复建议

> ⚠️ **当前后端缺失，需要新增**

```
GET /api/v1/chat/suggestions
```

**前端使用场景**: 聊天页展示快捷回复按钮（话题建议、冥想、AI绘画、写日记等）。

**响应体**:
```json
{
  "suggestions": [
    { "text": "今天心情怎么样", "icon": "💬" },
    { "text": "陪我聊聊天", "icon": "🌙" },
    { "text": "我想听故事", "icon": "📖" },
    { "text": "帮我放松一下", "icon": "🧘" }
  ]
}
```

---

## 四、记忆模块

### 4.1 获取记忆列表

```
GET /api/v1/memory/list
```

**前端使用场景**: 记忆页加载记忆列表，支持按分类筛选。

**查询参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| category | string | ❌ | 筛选分类：personal / event / preference / conversation / milestone |
| page | int | ❌ | 页码，默认 1 |
| page_size | int | ❌ | 每页条数，默认 20 |

**响应体**:
```json
{
  "total": 15,
  "memories": [
    {
      "id": 1,
      "memory": "用户最喜欢在雨天听爵士乐",
      "category": "preference",
      "importance": 0.8,
      "recall_count": 5,
      "created_at": "2026-05-19T10:00:00Z",
      "last_recalled_at": "2026-05-22T15:00:00Z"
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 记忆 ID |
| memory | string | 记忆内容 |
| category | string | 分类 |
| importance | float | 重要程度 0~1 |
| recall_count | int | 被回忆次数 |
| last_recalled_at | datetime | 最后一次被回忆的时间 |

### 4.2 添加记忆

```
POST /api/v1/memory
```

**前端使用场景**: 用户手动添加记忆。

**请求体**:
```json
{
  "memory": "我养了一只叫团子的猫",
  "category": "personal",
  "importance": 0.7
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| memory | string | ✅ | 记忆内容，1~1000 字符 |
| category | string | ❌ | 分类，默认 general |
| importance | float | ❌ | 重要程度 0~1，默认 0.5 |

**响应体**: 返回创建的记忆对象（同 4.1 中的单条记忆结构）。

### 4.3 删除记忆

> ⚠️ **当前后端缺失，需要新增**

```
DELETE /api/v1/memory/{memory_id}
```

**前端使用场景**: 用户左滑删除记忆。

**响应体**:
```json
{ "detail": "已删除" }
```

---

## 五、日记模块

### 5.1 获取日记列表

```
GET /api/v1/diary/list
```

**前端使用场景**: 日记页加载日记列表，支持按日期范围筛选。

**查询参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| start_date | string | ❌ | 起始日期 YYYY-MM-DD |
| end_date | string | ❌ | 结束日期 YYYY-MM-DD |
| page | int | ❌ | 页码，默认 1 |
| page_size | int | ❌ | 每页条数，默认 20 |

**响应体**:
```json
{
  "total": 8,
  "diaries": [
    {
      "id": 1,
      "mood": "neutral",
      "content": "今天工作压力有点大，但和晚星聊了一会儿之后感觉好多了。",
      "summary": "工作压力大，与AI伴侣聊天后缓解",
      "happened_on": "2026-05-22",
      "tags": ["工作", "加班", "音乐"],
      "created_at": "2026-05-22T22:30:00Z"
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 日记 ID |
| mood | string | 心情：very_happy / happy / neutral / sad / very_sad |
| content | string | 日记正文 |
| summary | string | AI 生成的摘要（可为 null） |
| happened_on | string | 日记日期 |
| tags | string[] | 标签列表 |

### 5.2 创建日记

```
POST /api/v1/diary
```

**前端使用场景**: 用户写完日记后保存。

**请求体**:
```json
{
  "content": "今天工作压力有点大...",
  "mood": "neutral",
  "happened_on": "2026-05-22",
  "tags": ["工作", "加班", "音乐"]
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| content | string | ✅ | 日记内容，1~5000 字符 |
| mood | string | ❌ | 心情，默认 calm |
| happened_on | string | ❌ | 日期，默认当天 |
| tags | string[] | ❌ | 标签列表 |

**响应体**: 返回创建的日记对象（同 5.1 中的单条日记结构）。

### 5.3 获取某月日记统计

> ⚠️ **当前后端缺失，需要新增**

```
GET /api/v1/diary/calendar
```

**前端使用场景**: 日记页日历视图，标记哪些日期有日记。

**查询参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| year | int | ✅ | 年份 |
| month | int | ✅ | 月份 1~12 |

**响应体**:
```json
{
  "year": 2026,
  "month": 5,
  "dates": [
    { "day": 3, "mood": "happy" },
    { "day": 7, "mood": "neutral" },
    { "day": 15, "mood": "very_happy" },
    { "day": 22, "mood": "neutral" }
  ]
}
```

---

## 六、成长模块

### 6.1 获取成长摘要

```
GET /api/v1/growth/summary
```

**前端使用场景**: 伴侣主页展示亲密度、统计数据；成长页展示详细进度。

**查询参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | int | ❌ | 用户 ID |
| companion_id | int | ❌ | 伴侣 ID |

**响应体**:
```json
{
  "user_id": 1,
  "companion_id": 1,
  "intimacy": 82,
  "level": "星河挚友",
  "level_number": 6,
  "next_level_intimacy": 100,
  "message_count": 256,
  "memory_count": 15,
  "diary_count": 8,
  "voice_call_count": 3,
  "voice_call_duration": 450,
  "milestones": [
    {
      "id": 1,
      "title": "初次相遇",
      "description": "和晚星第一次对话",
      "achieved_at": "2024-04-01T10:00:00Z"
    },
    {
      "id": 2,
      "title": "百日陪伴",
      "description": "和晚星互动满100天",
      "achieved_at": "2024-07-10T00:00:00Z"
    },
    {
      "id": 3,
      "title": "心灵相通",
      "description": "亲密度达到80",
      "achieved_at": "2024-04-15T14:30:00Z"
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| intimacy | int | 当前亲密度数值 |
| level | string | 等级名称（如"星河挚友"） |
| level_number | int | 等级数字 |
| next_level_intimacy | int | 升到下一级所需亲密度 |
| message_count | int | 总消息数 |
| memory_count | int | 总记忆数 |
| diary_count | int | 总日记数 |
| voice_call_count | int | 语音通话次数 |
| voice_call_duration | int | 语音通话总时长（秒） |
| milestones | array | 里程碑列表 |

---

## 七、商店模块

### 7.1 获取商品列表

```
GET /api/v1/shop/items
```

**前端使用场景**: 商店页加载商品，支持按分类筛选。

**查询参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| category | string | ❌ | 分类：outfit / scene / voice / prop / vip |
| page | int | ❌ | 页码，默认 1 |
| page_size | int | ❌ | 每页条数，默认 20 |

**响应体**:
```json
{
  "total": 24,
  "items": [
    {
      "id": 1,
      "name": "星空裙",
      "category": "outfit",
      "price": 200,
      "description": "梦幻星空主题连衣裙",
      "asset_url": "https://cdn.example.com/outfits/starry-dress.png",
      "is_active": true,
      "is_owned": false,
      "is_equipped": false,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 商品 ID |
| name | string | 商品名称 |
| category | string | 分类 |
| price | int | 价格（星币） |
| description | string | 商品描述 |
| asset_url | string | 资源图片 URL |
| is_owned | bool | 当前用户是否已拥有 |
| is_equipped | bool | 当前用户是否已装备 |

### 7.2 购买商品

> ⚠️ **当前后端缺失，需要新增**

```
POST /api/v1/shop/items/{item_id}/purchase
```

**前端使用场景**: 用户点击购买按钮。

**响应体**:
```json
{
  "success": true,
  "remaining_coins": 320,
  "item": { ... }
}
```

### 7.3 装备商品

> ⚠️ **当前后端缺失，需要新增**

```
POST /api/v1/shop/items/{item_id}/equip
```

**前端使用场景**: 用户装备已拥有的服装/场景/语音包。

**响应体**:
```json
{
  "success": true,
  "item": { ... }
}
```

### 7.4 获取用户星币余额

> ⚠️ **当前后端缺失，需要新增**

```
GET /api/v1/shop/balance
```

**响应体**:
```json
{
  "coins": 520
}
```

---

## 八、用户与伴侣模块

### 8.1 获取用户档案

```
GET /api/v1/profile/me
```

**前端使用场景**: 个人中心页加载用户信息；伴侣主页加载伴侣信息。

**响应体**:
```json
{
  "user": {
    "id": 1,
    "nickname": "Lee",
    "avatar": "https://cdn.example.com/avatars/lee.png",
    "is_vip": false,
    "vip_expire_at": null,
    "created_at": "2024-01-15T00:00:00Z"
  },
  "companion": {
    "id": 1,
    "name": "晚星",
    "persona": "温柔体贴的AI伴侣，善于倾听和安慰",
    "voice_style": "温柔女声",
    "avatar_url": "https://cdn.example.com/companion/wanxing.png",
    "intimacy": 82,
    "level": "星河挚友",
    "level_number": 6,
    "mood": "开心",
    "online": true
  }
}
```

### 8.2 更新伴侣形象

> ⚠️ **当前后端缺失，需要新增**

```
PUT /api/v1/profile/companion/appearance
```

**前端使用场景**: 形象设置页更换服装/场景/语音包。

**请求体**:
```json
{
  "outfit_id": 3,
  "scene_id": null,
  "voice_id": null
}
```

**响应体**:
```json
{
  "success": true,
  "companion": { ... }
}
```

### 8.3 更新用户资料

> ⚠️ **当前后端缺失，需要新增**

```
PUT /api/v1/profile/me
```

**请求体**:
```json
{
  "nickname": "新昵称",
  "avatar": "https://cdn.example.com/avatars/new.png"
}
```

**响应体**: 返回更新后的用户对象。

---

## 九、发现模块

### 9.1 获取每日任务

> ⚠️ **当前后端缺失，需要新增**

```
GET /api/v1/discover/tasks
```

**前端使用场景**: 发现页加载每日任务列表。

**响应体**:
```json
{
  "date": "2026-05-22",
  "tasks": [
    {
      "id": 1,
      "title": "冥想放松",
      "description": "和晚星一起做5分钟冥想",
      "icon": "🧘",
      "reward": 10,
      "is_completed": false
    },
    {
      "id": 2,
      "title": "AI绘画",
      "description": "让晚星为你画一幅画",
      "icon": "🎨",
      "reward": 15,
      "is_completed": true
    }
  ]
}
```

### 9.2 完成任务

> ⚠️ **当前后端缺失，需要新增**

```
POST /api/v1/discover/tasks/{task_id}/complete
```

**响应体**:
```json
{
  "success": true,
  "reward": 10,
  "total_intimacy_gained": 10
}
```

### 9.3 许愿灯

> ⚠️ **当前后端缺失，需要新增**

```
POST /api/v1/discover/wish
```

**请求体**:
```json
{
  "content": "希望今年能去冰岛看极光"
}
```

**响应体**:
```json
{
  "success": true,
  "wish_id": 1
}
```

---

## 十、语音通话模块

### 10.1 发起语音通话

> ⚠️ **当前后端缺失，需要新增**

```
POST /api/v1/call/start
```

**响应体**:
```json
{
  "call_id": "abc123",
  "ws_url": "wss://server/call/abc123",
  "tts_url": "wss://server/tts/abc123"
}
```

### 10.2 结束通话

> ⚠️ **当前后端缺失，需要新增**

```
POST /api/v1/call/{call_id}/end
```

**请求体**:
```json
{
  "duration": 156
}
```

**响应体**:
```json
{
  "success": true,
  "intimacy_gained": 5,
  "call_summary": "和晚星聊了2分36秒，讨论了今天的工作和明天的计划"
}
```

---

## 十一、接口总览

### 已有接口（可直接对接）

| # | 方法 | 路径 | 前端页面 | 状态 |
|---|------|------|---------|------|
| 1 | POST | /api/v1/chat/send | 聊天页 | ✅ 可用 |
| 2 | GET | /api/v1/memory/list | 记忆页 | ✅ 可用 |
| 3 | POST | /api/v1/memory | 记忆页 | ✅ 可用 |
| 4 | GET | /api/v1/diary/list | 日记页 | ✅ 可用 |
| 5 | POST | /api/v1/diary | 日记页 | ✅ 可用 |
| 6 | GET | /api/v1/growth/summary | 伴侣主页/成长页 | ✅ 可用 |
| 7 | GET | /api/v1/shop/items | 商店页 | ✅ 可用 |
| 8 | GET | /api/v1/profile/me | 个人中心 | ✅ 可用 |

### 需要新增的接口

| # | 方法 | 路径 | 前端页面 | 优先级 |
|---|------|------|---------|--------|
| 1 | GET | /api/v1/chat/history | 聊天页 | 🔴 高 |
| 2 | GET | /api/v1/chat/suggestions | 聊天页 | 🟡 中 |
| 3 | DELETE | /api/v1/memory/{id} | 记忆页 | 🟡 中 |
| 4 | GET | /api/v1/diary/calendar | 日记页 | 🔴 高 |
| 5 | POST | /api/v1/shop/items/{id}/purchase | 商店页 | 🔴 高 |
| 6 | POST | /api/v1/shop/items/{id}/equip | 商店页 | 🔴 高 |
| 7 | GET | /api/v1/shop/balance | 商店页 | 🔴 高 |
| 8 | PUT | /api/v1/profile/me | 个人中心 | 🟡 中 |
| 9 | PUT | /api/v1/profile/companion/appearance | 形象设置页 | 🟡 中 |
| 10 | GET | /api/v1/discover/tasks | 发现页 | 🔴 高 |
| 11 | POST | /api/v1/discover/tasks/{id}/complete | 发现页 | 🔴 高 |
| 12 | POST | /api/v1/discover/wish | 发现页 | 🟡 中 |
| 13 | POST | /api/v1/call/start | 通话页 | 🟢 低 |
| 14 | POST | /api/v1/call/{id}/end | 通话页 | 🟢 低 |

---

## 十二、已有接口需要调整的字段

以下已有接口的响应结构需要补充字段，才能满足前端需求：

### POST /api/v1/chat/send

需要新增返回字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| intimacy_gained | int | 本次对话获得的亲密度 |

### GET /api/v1/memory/list

需要新增返回字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| recall_count | int | 被回忆次数 |
| last_recalled_at | datetime | 最后一次被回忆时间 |

### GET /api/v1/diary/list

需要新增返回字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| tags | string[] | 标签列表 |

### GET /api/v1/growth/summary

需要新增返回字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| level_number | int | 等级数字 |
| next_level_intimacy | int | 升到下一级所需亲密度 |
| diary_count | int | 总日记数 |
| voice_call_count | int | 语音通话次数 |
| voice_call_duration | int | 语音通话总时长（秒） |

### GET /api/v1/shop/items

需要新增返回字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| description | string | 商品描述 |
| is_owned | bool | 当前用户是否已拥有 |
| is_equipped | bool | 当前用户是否已装备 |

### GET /api/v1/profile/me

companion 对象需要新增字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| avatar_url | string | 伴侣头像 URL |
| level_number | int | 等级数字 |
| mood | string | 伴侣当前心情 |
| online | bool | 是否在线 |

user 对象需要新增字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| is_vip | bool | 是否 VIP |
| vip_expire_at | datetime | VIP 到期时间 |

---

## 十三、后续对接计划

### 第一阶段：核心功能（优先级 🔴）

1. **聊天对接**: 对接 `/chat/send`，替换 Mock 数据
2. **记忆对接**: 对接 `/memory/list` 和 `/memory`
3. **日记对接**: 对接 `/diary/list` 和 `/diary`
4. **新增**: `/chat/history`、`/diary/calendar`
5. **商店**: 新增购买/装备/余额接口

### 第二阶段：完善功能（优先级 🟡）

1. **成长数据**: 对接 `/growth/summary`，补充字段
2. **用户资料**: 对接 `/profile/me`，新增编辑接口
3. **发现模块**: 新增任务/许愿接口
4. **记忆删除**: 新增 DELETE 接口

### 第三阶段：高级功能（优先级 🟢）

1. **语音通话**: WebSocket + TTS/ASR
2. **用户鉴权**: JWT Token 认证
3. **推送通知**: 主动消息推送
4. **Live2D/3D**: 角色形象渲染
