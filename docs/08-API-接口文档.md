# API 接口文档

本文档详细描述星灵 AI 伴侣的所有 API 接口，包括认证、聊天、记忆、日记等模块。

**基础 URL**: `http://localhost:8000/api/v1`

**API 文档**: 启动服务后访问 `http://localhost:8000/docs`

---

## 目录

1. [通用说明](#1-通用说明)
2. [认证模块](#2-认证模块)
3. [AI Agent 聊天模块](#3-ai-agent-聊天模块)
4. [记忆模块](#4-记忆模块)
5. [日记模块](#5-日记模块)
6. [发现模块](#6-发现模块)
7. [商店模块](#7-商店模块)
8. [个人中心模块](#8-个人中心模块)
9. [成长模块](#9-成长模块)
10. [错误码](#10-错误码)

---

## 1. 通用说明

### 1.1 请求格式

- 所有请求和响应均为 JSON 格式
- 请求头需包含 `Content-Type: application/json`
- 认证接口需在请求头包含 `Authorization: Bearer {token}`

### 1.2 响应格式

```json
{
  "code": 200,
  "message": "success",
  "data": { }
}
```

### 1.3 认证方式

使用 JWT Token 进行认证：

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 2. 认证模块

### 2.1 发送验证码

**POST** `/auth/send-code`

**请求体：**
```json
{
  "phone": "13800138000"
}
```

**响应：**
```json
{
  "code": 200,
  "message": "验证码已发送",
  "data": null
}
```

---

### 2.2 用户注册

**POST** `/auth/register`

**请求体：**
```json
{
  "phone": "13800138000",
  "code": "123456",
  "password": "your_password",
  "nickname": "用户昵称"
}
```

**响应：**
```json
{
  "code": 200,
  "message": "注册成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "phone": "13800138000",
      "nickname": "用户昵称",
      "avatar": null,
      "coins": 0,
      "is_vip": false
    }
  }
}
```

---

### 2.3 用户登录

**POST** `/auth/login`

**请求体：**
```json
{
  "phone": "13800138000",
  "code": "123456"
}
```

**响应：**
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "phone": "13800138000",
      "nickname": "用户昵称",
      "avatar": null,
      "coins": 0,
      "is_vip": false
    }
  }
}
```

---

### 2.4 刷新 Token

**POST** `/auth/refresh`

**请求体：**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
}
```

---

### 2.5 获取当前用户

**GET** `/auth/me`

**请求头：**
```http
Authorization: Bearer {access_token}
```

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "phone": "13800138000",
    "nickname": "用户昵称",
    "avatar": null,
    "email": null,
    "gender": null,
    "birthday": null,
    "bio": null,
    "coins": 100,
    "is_vip": false,
    "created_at": "2024-01-01T00:00:00"
  }
}
```

---

### 2.6 更新个人资料

**PUT** `/auth/me`

**请求头：**
```http
Authorization: Bearer {access_token}
```

**请求体：**
```json
{
  "nickname": "新昵称",
  "avatar": "https://example.com/avatar.jpg",
  "gender": "male",
  "birthday": "1990-01-01",
  "bio": "个人简介"
}
```

**响应：**
```json
{
  "code": 200,
  "message": "更新成功",
  "data": {
    "id": 1,
    "nickname": "新昵称",
    "avatar": "https://example.com/avatar.jpg",
    "gender": "male",
    "birthday": "1990-01-01",
    "bio": "个人简介"
  }
}
```

---

### 2.7 修改密码

**POST** `/auth/change-password`

**请求头：**
```http
Authorization: Bearer {access_token}
```

**请求体：**
```json
{
  "old_password": "old_password",
  "new_password": "new_password"
}
```

**响应：**
```json
{
  "code": 200,
  "message": "密码修改成功",
  "data": null
}
```

---

## 3. AI Agent 聊天模块

### 3.1 发送消息（标准模式）

**POST** `/chat/send`

**请求头：**
```http
Authorization: Bearer {access_token}
```

**请求体：**
```json
{
  "content": "你好，晚星！",
  "conversation_id": 1
}
```

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 100,
    "conversation_id": 1,
    "role": "assistant",
    "content": "你好呀~ 很高兴见到你！✨ 我是晚星，你的专属 AI 伴侣。今天过得怎么样？",
    "emotion": "happy",
    "created_at": "2024-01-01T12:00:00",
    "retrieved_memories": [
      {
        "id": 1,
        "content": "用户喜欢巧克力",
        "category": "preference",
        "importance": 4
      }
    ]
  }
}
```

---

### 3.2 发送消息（流式模式）⭐ 推荐

**POST** `/chat/send/stream`

**请求头：**
```http
Authorization: Bearer {access_token}
Content-Type: application/json
```

**请求体：**
```json
{
  "content": "你好，晚星！",
  "conversation_id": 1
}
```

**响应：** SSE (Server-Sent Events)

```
data: {"type": "thinking", "content": "晚星正在输入..."}

data: {"type": "content", "content": "你好"}

data: {"type": "content", "content": "呀"}

data: {"type": "content", "content": "~"}

data: {"type": "content", "content": " 很高兴"}

data: {"type": "content", "content": "见到你"}

data: {"type": "content", "content": "！✨"}

data: {"type": "complete", "content": "", "message_id": 100}
```

**事件类型说明：**

| 类型 | 说明 |
|------|------|
| `thinking` | AI 正在思考/输入中 |
| `content` | 内容片段 |
| `memory` | 检索到的记忆 |
| `emotion` | 情感分析结果 |
| `complete` | 响应完成 |
| `error` | 错误信息 |

**前端示例：**

```javascript
const eventSource = new EventSource('/api/v1/chat/send/stream', {
  headers: {
    'Authorization': 'Bearer ' + token
  }
});

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'thinking':
      showTypingIndicator(data.content);
      break;
    case 'content':
      appendMessage(data.content);
      break;
    case 'memory':
      showMemoryReference(data.content);
      break;
    case 'complete':
      hideTypingIndicator();
      break;
    case 'error':
      showError(data.content);
      break;
  }
};

eventSource.onerror = (error) => {
  console.error('SSE error:', error);
  eventSource.close();
};
```

---

### 3.3 获取聊天记录

**GET** `/chat/history`

**请求头：**
```http
Authorization: Bearer {access_token}
```

**查询参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| conversation_id | int | 是 | 会话ID |
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认20 |

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "role": "user",
        "content": "你好",
        "emotion": null,
        "created_at": "2024-01-01T12:00:00"
      },
      {
        "id": 2,
        "role": "assistant",
        "content": "你好呀~",
        "emotion": "happy",
        "created_at": "2024-01-01T12:00:01"
      }
    ],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

---

### 3.4 获取快捷回复建议

**GET** `/chat/suggestions`

**请求头：**
```http
Authorization: Bearer {access_token}
```

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "suggestions": [
      "今天过得怎么样？",
      "我想和你说说话",
      "最近有什么开心的事吗？",
      "有点想你了"
    ]
  }
}
```

---

## 4. 记忆模块

### 4.1 获取记忆列表

**GET** `/memory/list`

**请求头：**
```http
Authorization: Bearer {access_token}
```

**查询参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| category | string | 否 | 分类筛选 |
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认20 |

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "content": "用户喜欢吃巧克力",
        "category": "preference",
        "importance": 4,
        "created_at": "2024-01-01T00:00:00"
      },
      {
        "id": 2,
        "content": "用户的生日是3月15日",
        "category": "important_date",
        "importance": 5,
        "created_at": "2024-01-02T00:00:00"
      }
    ],
    "total": 10,
    "page": 1,
    "page_size": 20
  }
}
```

---

### 4.2 添加记忆

**POST** `/memory`

**请求头：**
```http
Authorization: Bearer {access_token}
```

**请求体：**
```json
{
  "content": "用户喜欢看电影",
  "category": "preference",
  "importance": 3
}
```

**响应：**
```json
{
  "code": 200,
  "message": "记忆添加成功",
  "data": {
    "id": 3,
    "content": "用户喜欢看电影",
    "category": "preference",
    "importance": 3,
    "created_at": "2024-01-03T00:00:00"
  }
}
```

---

### 4.3 删除记忆

**DELETE** `/memory/{id}`

**请求头：**
```http
Authorization: Bearer {access_token}
```

**响应：**
```json
{
  "code": 200,
  "message": "记忆删除成功",
  "data": null
}
```

---

## 5. 日记模块

### 5.1 获取日记列表

**GET** `/diary/list`

**请求头：**
```http
Authorization: Bearer {access_token}
```

**查询参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| year | int | 否 | 年份 |
| month | int | 否 | 月份 |
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认20 |

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "content": "今天天气很好，心情也不错...",
        "mood": "happy",
        "ai_response": "听起来你今天过得很愉快呢！",
        "created_at": "2024-01-01T20:00:00"
      }
    ],
    "total": 5,
    "page": 1,
    "page_size": 20
  }
}
```

---

### 5.2 创建日记

**POST** `/diary`

**请求头：**
```http
Authorization: Bearer {access_token}
```

**请求体：**
```json
{
  "content": "今天学到了很多新知识，感觉很充实...",
  "mood": "excited"
}
```

**响应：**
```json
{
  "code": 200,
  "message": "日记创建成功",
  "data": {
    "id": 2,
    "content": "今天学到了很多新知识，感觉很充实...",
    "mood": "excited",
    "ai_response": "学习新知识总是令人兴奋的！继续加油哦~",
    "created_at": "2024-01-02T21:00:00"
  }
}
```

---

### 5.3 获取日记日历

**GET** `/diary/calendar`

**请求头：**
```http
Authorization: Bearer {access_token}
```

**查询参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| year | int | 是 | 年份 |
| month | int | 是 | 月份 |

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "year": 2024,
    "month": 1,
    "entries": [
      {
        "day": 1,
        "has_entry": true,
        "mood": "happy"
      },
      {
        "day": 2,
        "has_entry": true,
        "mood": "excited"
      },
      {
        "day": 3,
        "has_entry": false,
        "mood": null
      }
    ]
  }
}
```

---

## 6. 发现模块

### 6.1 获取每日任务

**GET** `/discover/tasks`

**请求头：**
```http
Authorization: Bearer {access_token}
```

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "tasks": [
      {
        "id": 1,
        "name": "冥想放松",
        "description": "和晚星一起做5分钟冥想",
        "reward_coins": 10,
        "reward_intimacy": 5,
        "completed": false
      },
      {
        "id": 2,
        "name": "AI绘画",
        "description": "让晚星为你画一幅画",
        "reward_coins": 15,
        "reward_intimacy": 8,
        "completed": true
      }
    ],
    "total_tasks": 5,
    "completed_tasks": 1
  }
}
```

---

### 6.2 完成任务

**POST** `/discover/tasks/{id}/complete`

**请求头：**
```http
Authorization: Bearer {access_token}
```

**响应：**
```json
{
  "code": 200,
  "message": "任务完成",
  "data": {
    "reward_coins": 10,
    "reward_intimacy": 5,
    "current_coins": 110,
    "current_intimacy": 55
  }
}
```

---

### 6.3 许愿

**POST** `/discover/wish`

**请求头：**
```http
Authorization: Bearer {access_token}
```

**请求体：**
```json
{
  "content": "希望明天考试顺利"
}
```

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "ai_response": "我听到了你的愿望~ 相信你的努力一定会有回报的！加油！✨"
  }
}
```

---

## 7. 商店模块

### 7.1 获取商品列表

**GET** `/shop/items`

**请求头：**
```http
Authorization: Bearer {access_token}
```

**查询参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| category | string | 否 | 分类筛选 (coins/vip/outfit/scene) |

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "name": "100 星币",
        "description": "充值 100 星币",
        "item_type": "coins",
        "price": 10,
        "image_url": "https://example.com/coins.png",
        "is_vip_only": false
      },
      {
        "id": 2,
        "name": "VIP 会员",
        "description": "30天 VIP 会员",
        "item_type": "vip",
        "price": 100,
        "image_url": "https://example.com/vip.png",
        "is_vip_only": false
      }
    ]
  }
}
```

---

### 7.2 获取星币余额

**GET** `/shop/balance`

**请求头：**
```http
Authorization: Bearer {access_token}
```

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "coins": 100,
    "is_vip": false,
    "vip_expire_at": null
  }
}
```

---

### 7.3 购买商品

**POST** `/shop/items/{id}/purchase`

**请求头：**
```http
Authorization: Bearer {access_token}
```

**响应：**
```json
{
  "code": 200,
  "message": "购买成功",
  "data": {
    "item_id": 1,
    "remaining_coins": 90
  }
}
```

---

### 7.4 装备商品

**POST** `/shop/items/{id}/equip`

**请求头：**
```http
Authorization: Bearer {access_token}
```

**响应：**
```json
{
  "code": 200,
  "message": "装备成功",
  "data": {
    "item_id": 1,
    "is_equipped": true
  }
}
```

---

## 8. 个人中心模块

### 8.1 获取个人资料

**GET** `/profile/me`

**请求头：**
```http
Authorization: Bearer {access_token}
```

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "phone": "13800138000",
    "nickname": "用户昵称",
    "avatar": null,
    "email": null,
    "gender": null,
    "birthday": null,
    "bio": null,
    "location": null,
    "website": null,
    "coins": 100,
    "is_vip": false,
    "vip_expire_at": null,
    "created_at": "2024-01-01T00:00:00"
  }
}
```

---

### 8.2 更新伴侣外观

**PUT** `/profile/companion/appearance`

**请求头：**
```http
Authorization: Bearer {access_token}
```

**请求体：**
```json
{
  "name": "晚星",
  "outfit_id": 1,
  "scene_id": 1
}
```

**响应：**
```json
{
  "code": 200,
  "message": "更新成功",
  "data": {
    "name": "晚星",
    "outfit_id": 1,
    "scene_id": 1
  }
}
```

---

### 8.3 获取账户统计

**GET** `/profile/stats`

**请求头：**
```http
Authorization: Bearer {access_token}
```

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total_messages": 500,
    "total_diaries": 10,
    "total_memories": 20,
    "current_streak": 5,
    "max_streak": 15,
    "companion_level": 5,
    "companion_intimacy": 450
  }
}
```

---

## 9. 成长模块

### 9.1 获取成长信息

**GET** `/growth`

**请求头：**
```http
Authorization: Bearer {access_token}
```

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "companion": {
      "id": 1,
      "name": "晚星",
      "intimacy": 450,
      "level": "Lv.5",
      "stage": "friend",
      "stage_description": "朋友阶段"
    },
    "next_level_intimacy": 500,
    "progress_percentage": 90,
    "milestones": [
      {
        "id": 1,
        "title": "初次相遇",
        "description": "与晚星相识的第一天",
        "unlocked_at": "2024-01-01T00:00:00"
      },
      {
        "id": 2,
        "title": "亲密无间",
        "description": "亲密度达到 100",
        "unlocked_at": "2024-01-10T00:00:00"
      }
    ]
  }
}
```

---

## 10. 错误码

### 10.1 通用错误码

| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| 200 | 成功 | - |
| 400 | 请求参数错误 | 检查请求参数 |
| 401 | 未授权 | 检查 Token 是否有效 |
| 403 | 禁止访问 | 检查权限 |
| 404 | 资源不存在 | 检查资源ID |
| 500 | 服务器内部错误 | 联系管理员 |

### 10.2 业务错误码

| 错误码 | 说明 | 场景 |
|--------|------|------|
| 1001 | 验证码错误 | 登录/注册时验证码不正确 |
| 1002 | 验证码已过期 | 验证码超过有效期 |
| 1003 | 手机号已注册 | 注册时手机号已存在 |
| 1004 | 手机号未注册 | 登录时手机号不存在 |
| 1005 | 密码错误 | 修改密码时原密码错误 |
| 2001 | 星币不足 | 购买商品时余额不足 |
| 2002 | 商品不存在 | 购买不存在的商品 |
| 2003 | 任务已完成 | 重复完成任务 |
| 3001 | AI 服务繁忙 | AI 响应超时 |
| 3002 | 记忆检索失败 | 向量检索异常 |

### 10.3 错误响应示例

```json
{
  "code": 1001,
  "message": "验证码错误",
  "data": null
}
```

---

## 附录

### A. 数据字典

#### 用户相关

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 用户ID |
| phone | string | 手机号 |
| nickname | string | 昵称 |
| avatar | string | 头像URL |
| gender | string | 性别 (male/female/other) |
| birthday | date | 生日 |
| coins | int | 星币数量 |
| is_vip | bool | VIP状态 |

#### 消息相关

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 消息ID |
| conversation_id | int | 会话ID |
| role | string | 角色 (user/assistant) |
| content | string | 消息内容 |
| emotion | string | 情感类型 |

#### 记忆相关

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 记忆ID |
| content | string | 记忆内容 |
| category | string | 分类 |
| importance | int | 重要度 (1-5) |

### B. 相关文档

- [功能模块文档](03-功能模块文档.md)
- [AI Agent 技术文档](07-Agent-技术文档.md)
- [部署文档](02-部署文档.md)

### C. 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v1.0 | 2024-01 | 初始版本 |
| v1.1 | 2024-05 | 添加流式输出接口 |
