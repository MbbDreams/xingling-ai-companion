# 星灵AI伴侣 Flutter App

基于 Flutter 的跨平台 AI 伴侣应用，支持 Android 和 iOS。

## 技术栈

- **Flutter 3.x** - 跨平台 UI 框架
- **Riverpod** - 状态管理
- **Dio** - HTTP 客户端
- **SQLite/SharedPreferences** - 本地存储

## 项目结构

```
lib/
├── main.dart              # 应用入口
├── api/
│   └── api_client.dart    # API 客户端配置
├── models/
│   ├── user.dart          # 用户/伴侣模型
│   ├── message.dart        # 消息模型
│   ├── memory.dart         # 记忆模型
│   ├── diary.dart          # 日记模型
│   ├── growth.dart         # 成长数据模型
│   └── shop.dart           # 商店模型
├── services/
│   ├── api_services.dart   # API 服务层
│   └── providers.dart      # Riverpod Providers
├── screens/
│   ├── home_screen.dart    # 主页面
│   ├── chat/               # 聊天页面
│   ├── companion/          # 伴侣主页
│   ├── memory/             # 记忆页面
│   ├── diary/              # 日记页面
│   ├── shop/               # 商店页面
│   ├── profile/            # 个人中心
│   └── growth/             # 成长数据
└── utils/
    └── theme.dart          # 主题配置
```

## 快速开始

### 环境要求

- Flutter SDK >= 3.0.0
- Dart SDK >= 3.0.0

### 安装依赖

```bash
cd flutter_app
flutter pub get
```

### 运行应用

```bash
# 开发模式
flutter run

# 构建 APK
flutter build apk

# 构建 iOS
flutter build ios
```

### 配置后端地址

编辑 `lib/api/api_client.dart` 中的 `ApiConfig.baseUrl`:

```dart
static const String baseUrl = 'http://你的服务器地址:8000/api/v1';
```

## 功能模块

1. **伴侣主页** - 查看 AI 伴侣状态、亲密度、快速入口
2. **聊天** - 与 AI 伴侣对话，支持情绪识别
3. **记忆** - 管理长期记忆，按分类筛选
4. **日记** - 记录日记，选择心情
5. **商店** - 购买服装、场景、语音包
6. **成长** - 查看亲密度等级和里程碑
7. **个人中心** - 用户信息、会员、设置

## 与后端对接

确保后端服务已启动：

```bash
# 启动后端
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API 端点：
- `POST /api/v1/chat/send` - 发送消息
- `GET /api/v1/growth/summary` - 获取成长数据
- `GET /api/v1/memory/list` - 获取记忆列表
- `POST /api/v1/memory` - 添加记忆
- `GET /api/v1/diary/list` - 获取日记列表
- `POST /api/v1/diary` - 添加日记
- `GET /api/v1/shop/items` - 获取商店商品
- `GET /api/v1/profile/me` - 获取用户信息
