import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/message.dart';
import '../services/api_services.dart';

/// 聊天会话状态
class ChatSessionState {
  final int? conversationId;
  final List<Message> messages;
  final bool isLoading;
  final bool isSending;
  final bool showTyping;
  final String? error;
  final List<String> suggestions;

  ChatSessionState({
    this.conversationId,
    this.messages = const [],
    this.isLoading = false,
    this.isSending = false,
    this.showTyping = false,
    this.error,
    this.suggestions = const [],
  });

  ChatSessionState copyWith({
    int? conversationId,
    List<Message>? messages,
    bool? isLoading,
    bool? isSending,
    bool? showTyping,
    String? error,
    List<String>? suggestions,
    bool clearError = false,
  }) {
    return ChatSessionState(
      conversationId: conversationId ?? this.conversationId,
      messages: messages ?? this.messages,
      isLoading: isLoading ?? this.isLoading,
      isSending: isSending ?? this.isSending,
      showTyping: showTyping ?? this.showTyping,
      error: clearError ? null : (error ?? this.error),
      suggestions: suggestions ?? this.suggestions,
    );
  }

  /// 获取最后一条消息
  Message? get lastMessage => messages.isNotEmpty ? messages.last : null;

  /// 是否有活跃会话
  bool get hasActiveSession => conversationId != null;
}

/// 聊天会话管理器
class ChatSessionNotifier extends StateNotifier<ChatSessionState> {
  final ChatService _chatService;

  ChatSessionNotifier(this._chatService) : super(ChatSessionState());

  /// 初始化或恢复会话
  /// 
  /// 如果有传入 conversationId，则加载该会话
  /// 否则尝试获取用户的默认会话，如果没有则创建新会话
  Future<void> initializeSession({int? conversationId}) async {
    if (conversationId != null) {
      await loadConversation(conversationId);
      return;
    }

    // 如果已经有会话ID，直接加载
    if (state.conversationId != null) {
      await loadConversation(state.conversationId!);
      return;
    }

    // 否则创建新会话
    await createNewSession();
  }

  /// 加载指定会话的历史记录
  Future<void> loadConversation(int conversationId) async {
    try {
      state = state.copyWith(isLoading: true, clearError: true);

      final response = await _chatService.getChatHistory(
        conversationId: conversationId,
        page: 1,
        pageSize: 50,
      );

      state = state.copyWith(
        conversationId: conversationId,
        messages: response.messages,
        isLoading: false,
      );
    } catch (e) {
      debugPrint('加载聊天记录失败: $e');
      state = state.copyWith(
        isLoading: false,
        error: '加载聊天记录失败: $e',
      );
    }
  }

  /// 创建新会话
  Future<void> createNewSession() async {
    try {
      state = state.copyWith(isLoading: true, clearError: true);

      // 调用后端创建新会话
      final response = await _chatService.createConversation();
      
      state = ChatSessionState(
        conversationId: response.conversationId,
        messages: [],
        isLoading: false,
        suggestions: state.suggestions,
      );
    } catch (e) {
      debugPrint('创建会话失败: $e');
      // 创建失败时使用默认会话ID 1
      state = ChatSessionState(
        conversationId: 1,
        messages: [],
        isLoading: false,
        error: '创建新会话失败，使用默认会话',
      );
    }
  }

  /// 加载快捷建议
  Future<void> loadSuggestions() async {
    try {
      final suggestions = await _chatService.getSuggestions();
      state = state.copyWith(
        suggestions: suggestions.map((s) => s.text).toList(),
      );
    } catch (e) {
      debugPrint('加载建议失败: $e');
      state = state.copyWith(
        suggestions: [
          '今天心情怎么样',
          '陪我聊聊天',
          '我想听故事',
          '帮我放松一下',
        ],
      );
    }
  }

  /// 发送消息
  Future<void> sendMessage(String content) async {
    if (content.trim().isEmpty || state.isSending) return;

    final text = content.trim();
    
    // 确保有会话ID
    if (state.conversationId == null) {
      await createNewSession();
    }

    // 创建用户消息
    final userMsg = Message(
      messageId: DateTime.now().millisecondsSinceEpoch,
      conversationId: state.conversationId!,
      content: text,
      isFromUser: true,
      createdAt: DateTime.now(),
    );

    // 添加到消息列表
    state = state.copyWith(
      messages: [...state.messages, userMsg],
      isSending: true,
      showTyping: true,
      clearError: true,
    );

    try {
      // 调用后端 API
      final request = ChatRequest(
        content: text,
        conversationId: state.conversationId,
      );
      final response = await _chatService.sendMessage(request);

      // 创建 AI 消息
      final aiMsg = Message(
        messageId: DateTime.now().millisecondsSinceEpoch + 1,
        conversationId: response.conversationId ?? state.conversationId!,
        content: response.reply,
        isFromUser: false,
        createdAt: DateTime.now(),
        emotion: response.detectedEmotion,
      );

      state = state.copyWith(
        messages: [...state.messages, aiMsg],
        isSending: false,
        showTyping: false,
        conversationId: response.conversationId ?? state.conversationId,
      );
    } catch (e) {
      debugPrint('发送消息失败: $e');
      state = state.copyWith(
        isSending: false,
        showTyping: false,
        error: '发送失败: $e',
      );
    }
  }

  /// 清除错误
  void clearError() {
    state = state.copyWith(clearError: true);
  }

  /// 重置会话（用于退出登录等场景）
  void reset() {
    state = ChatSessionState();
  }
}

/// 聊天会话 Provider
final chatSessionProvider = StateNotifierProvider<ChatSessionNotifier, ChatSessionState>((ref) {
  final chatService = ref.watch(chatServiceProvider);
  return ChatSessionNotifier(chatService);
});

/// 当前会话ID Provider（用于外部访问）
final currentConversationIdProvider = Provider<int?>((ref) {
  return ref.watch(chatSessionProvider).conversationId;
});

/// 消息列表 Provider（用于外部访问）
final chatMessagesProvider = Provider<List<Message>>((ref) {
  return ref.watch(chatSessionProvider).messages;
});
