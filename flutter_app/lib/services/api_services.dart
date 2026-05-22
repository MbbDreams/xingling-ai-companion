import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/api_client.dart';
import '../models/models.dart';

/// 聊天服务 Provider
final chatServiceProvider = Provider<ChatService>((ref) {
  final apiService = ref.watch(apiServiceProvider);
  return ChatService(apiService);
});

/// 聊天服务
class ChatService {
  final ApiService _api;

  ChatService(this._api);

  /// 发送聊天消息
  Future<ChatResponse> sendMessage(ChatRequest request) async {
    try {
      final response = await _api.post(
        '/chat/send',
        data: request.toJson(),
      );
      return ChatResponse.fromJson(response.data);
    } catch (e) {
      rethrow;
    }
  }

  /// 获取聊天历史
  Future<ChatHistoryResponse> getChatHistory({
    required int conversationId,
    int page = 1,
    int pageSize = 20,
  }) async {
    try {
      final response = await _api.get(
        '/chat/history',
        queryParameters: {
          'conversation_id': conversationId,
          'page': page,
          'page_size': pageSize,
        },
      );
      return ChatHistoryResponse.fromJson(response.data);
    } catch (e) {
      rethrow;
    }
  }

  /// 获取快捷回复建议
  Future<List<ChatSuggestion>> getSuggestions() async {
    try {
      final response = await _api.get('/chat/suggestions');
      final List<dynamic> data = response.data['suggestions'] ?? [];
      return data.map((json) => ChatSuggestion.fromJson(json)).toList();
    } catch (e) {
      rethrow;
    }
  }
}

/// 成长服务 Provider
final growthServiceProvider = Provider<GrowthService>((ref) {
  final apiService = ref.watch(apiServiceProvider);
  return GrowthService(apiService);
});

/// 成长服务
class GrowthService {
  final ApiService _api;

  GrowthService(this._api);

  /// 获取成长数据摘要
  Future<GrowthSummary> getSummary({int? userId, int? companionId}) async {
    try {
      final response = await _api.get(
        '/growth/summary',
        queryParameters: {
          if (userId != null) 'user_id': userId,
          if (companionId != null) 'companion_id': companionId,
        },
      );
      return GrowthSummary.fromJson(response.data);
    } catch (e) {
      rethrow;
    }
  }

  /// 获取成长总结
  Future<GrowthSummary> getGrowthSummary() async {
    try {
      final response = await _api.get('/growth/summary');
      return GrowthSummary.fromJson(response.data);
    } catch (e) {
      rethrow;
    }
  }

  /// 获取里程碑列表
  Future<List<GrowthMilestone>> getMilestones() async {
    try {
      final response = await _api.get('/growth/milestones');
      final List<dynamic> data = response.data ?? [];
      return data.map((json) => GrowthMilestone.fromJson(json)).toList();
    } catch (e) {
      rethrow;
    }
  }
}

/// 记忆服务 Provider
final memoryServiceProvider = Provider<MemoryService>((ref) {
  final apiService = ref.watch(apiServiceProvider);
  return MemoryService(apiService);
});

/// 记忆服务
class MemoryService {
  final ApiService _api;

  MemoryService(this._api);

  /// 获取记忆列表
  Future<List<Memory>> getMemories({
    String? category,
    int page = 1,
    int pageSize = 20,
  }) async {
    try {
      final response = await _api.get(
        '/memory/list',
        queryParameters: {
          if (category != null) 'category': category,
          'page': page,
          'page_size': pageSize,
        },
      );
      final List<dynamic> data = response.data;
      return data.map((json) => Memory.fromJson(json)).toList();
    } catch (e) {
      rethrow;
    }
  }

  /// 添加新记忆
  Future<Memory> addMemory(AddMemoryRequest request) async {
    try {
      final response = await _api.post(
        '/memory',
        data: request.toJson(),
      );
      return Memory.fromJson(response.data);
    } catch (e) {
      rethrow;
    }
  }

  /// 删除记忆
  Future<void> deleteMemory(int memoryId) async {
    try {
      await _api.delete('/memory/$memoryId');
    } catch (e) {
      rethrow;
    }
  }
}

/// 日记服务 Provider
final diaryServiceProvider = Provider<DiaryService>((ref) {
  final apiService = ref.watch(apiServiceProvider);
  return DiaryService(apiService);
});

/// 日记服务
class DiaryService {
  final ApiService _api;

  DiaryService(this._api);

  /// 获取日记列表
  Future<List<DiaryEntry>> getDiaries({
    DateTime? startDate,
    DateTime? endDate,
    int page = 1,
    int pageSize = 20,
  }) async {
    try {
      final response = await _api.get(
        '/diary/list',
        queryParameters: {
          if (startDate != null) 'start_date': startDate.toIso8601String().split('T')[0],
          if (endDate != null) 'end_date': endDate.toIso8601String().split('T')[0],
          'page': page,
          'page_size': pageSize,
        },
      );
      final List<dynamic> data = response.data;
      return data.map((json) => DiaryEntry.fromJson(json)).toList();
    } catch (e) {
      rethrow;
    }
  }

  /// 添加日记
  Future<DiaryEntry> addDiary(AddDiaryRequest request) async {
    try {
      final response = await _api.post(
        '/diary',
        data: request.toJson(),
      );
      return DiaryEntry.fromJson(response.data);
    } catch (e) {
      rethrow;
    }
  }

  /// 获取日记日历
  Future<DiaryCalendarResponse> getCalendar(int year, int month) async {
    try {
      final response = await _api.get(
        '/diary/calendar',
        queryParameters: {
          'year': year,
          'month': month,
        },
      );
      return DiaryCalendarResponse.fromJson(response.data);
    } catch (e) {
      rethrow;
    }
  }
}

/// 商店服务 Provider
final shopServiceProvider = Provider<ShopService>((ref) {
  final apiService = ref.watch(apiServiceProvider);
  return ShopService(apiService);
});

/// 商店服务
class ShopService {
  final ApiService _api;

  ShopService(this._api);

  /// 获取商品列表
  Future<List<ShopItem>> getItems({String? category}) async {
    try {
      final response = await _api.get(
        '/shop/items',
        queryParameters: {
          if (category != null) 'category': category,
        },
      );
      final List<dynamic> data = response.data;
      return data.map((json) => ShopItem.fromJson(json)).toList();
    } catch (e) {
      rethrow;
    }
  }

  /// 获取星币余额
  Future<int> getBalance() async {
    try {
      final response = await _api.get('/shop/balance');
      return response.data['coins'] ?? 0;
    } catch (e) {
      rethrow;
    }
  }

  /// 购买商品
  Future<PurchaseResponse> purchaseItem(int itemId) async {
    try {
      final response = await _api.post('/shop/items/$itemId/purchase');
      return PurchaseResponse.fromJson(response.data);
    } catch (e) {
      rethrow;
    }
  }

  /// 装备商品
  Future<EquipResponse> equipItem(int itemId) async {
    try {
      final response = await _api.post('/shop/items/$itemId/equip');
      return EquipResponse.fromJson(response.data);
    } catch (e) {
      rethrow;
    }
  }
}

/// 用户服务 Provider
final userServiceProvider = Provider<UserService>((ref) {
  final apiService = ref.watch(apiServiceProvider);
  return UserService(apiService);
});

/// 用户服务
class UserService {
  final ApiService _api;

  UserService(this._api);

  /// 获取当前用户和伴侣信息
  Future<UserProfileWithCompanion> getProfile() async {
    try {
      final response = await _api.get('/profile/me');
      return UserProfileWithCompanion.fromJson(response.data);
    } catch (e) {
      rethrow;
    }
  }

  /// 更新用户资料
  Future<UserProfile> updateProfile({String? nickname, String? avatar}) async {
    try {
      final response = await _api.put(
        '/profile/me',
        data: {
          if (nickname != null) 'nickname': nickname,
          if (avatar != null) 'avatar': avatar,
        },
      );
      return UserProfile.fromJson(response.data['user']);
    } catch (e) {
      rethrow;
    }
  }

  /// 更新伴侣外观
  Future<Companion> updateCompanionAppearance({
    int? outfitId,
    int? sceneId,
    int? voiceId,
  }) async {
    try {
      final response = await _api.put(
        '/profile/companion/appearance',
        data: {
          if (outfitId != null) 'outfit_id': outfitId,
          if (sceneId != null) 'scene_id': sceneId,
          if (voiceId != null) 'voice_id': voiceId,
        },
      );
      return Companion.fromJson(response.data['companion']);
    } catch (e) {
      rethrow;
    }
  }
}

/// 发现服务 Provider
final discoverServiceProvider = Provider<DiscoverService>((ref) {
  final apiService = ref.watch(apiServiceProvider);
  return DiscoverService(apiService);
});

/// 发现服务
class DiscoverService {
  final ApiService _api;

  DiscoverService(this._api);

  /// 获取每日任务
  Future<List<Map<String, dynamic>>> getTasks() async {
    try {
      final response = await _api.get('/discover/tasks');
      final List<dynamic> data = response.data['tasks'] ?? [];
      return data.cast<Map<String, dynamic>>();
    } catch (e) {
      rethrow;
    }
  }

  /// 完成任务
  Future<Map<String, dynamic>> completeTask(int taskId) async {
    try {
      final response = await _api.post('/discover/tasks/$taskId/complete');
      return response.data;
    } catch (e) {
      rethrow;
    }
  }

  /// 许愿
  Future<void> makeWish(String content) async {
    try {
      await _api.post(
        '/discover/wish',
        data: {'content': content},
      );
    } catch (e) {
      rethrow;
    }
  }
}
