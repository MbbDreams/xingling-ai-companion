import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/models.dart';
import '../services/api_services.dart';

/// 成长摘要 Provider
final growthSummaryProvider = FutureProvider<GrowthSummary>((ref) async {
  final service = ref.watch(growthServiceProvider);
  return service.getSummary();
});

/// 记忆列表 Provider
final memoriesProvider = FutureProvider<List<Memory>>((ref) async {
  final service = ref.watch(memoryServiceProvider);
  return service.getMemories();
});

/// 日记列表 Provider
final diariesProvider = FutureProvider<List<DiaryEntry>>((ref) async {
  final service = ref.watch(diaryServiceProvider);
  return service.getDiaries();
});

/// 商店商品 Provider
final shopItemsProvider = FutureProvider<List<ShopItem>>((ref) async {
  final service = ref.watch(shopServiceProvider);
  return service.getItems();
});

/// 用户资料 Provider
final userProfileProvider = FutureProvider<UserProfileWithCompanion>((ref) async {
  final service = ref.watch(userServiceProvider);
  return service.getProfile();
});

/// 聊天消息列表 StateNotifier
class ChatMessagesNotifier extends StateNotifier<List<Message>> {
  final ChatService _chatService;

  ChatMessagesNotifier(this._chatService) : super([]);

  Future<void> sendMessage(String content) async {
    final response = await _chatService.sendMessage(
      ChatRequest(content: content),
    );
    state = [
      ...state,
      Message(
        messageId: DateTime.now().millisecondsSinceEpoch,
        conversationId: response.conversationId ?? 0,
        content: content,
        isFromUser: true,
        createdAt: DateTime.now(),
      ),
      Message(
        messageId: DateTime.now().millisecondsSinceEpoch + 1,
        conversationId: response.conversationId ?? 0,
        content: response.reply,
        isFromUser: false,
        createdAt: DateTime.now(),
        emotion: response.detectedEmotion,
      ),
    ];
  }

  void loadHistory(List<Message> messages) {
    state = messages;
  }
}

final chatMessagesProvider =
    StateNotifierProvider<ChatMessagesNotifier, List<Message>>((ref) {
  final service = ref.watch(chatServiceProvider);
  return ChatMessagesNotifier(service);
});
