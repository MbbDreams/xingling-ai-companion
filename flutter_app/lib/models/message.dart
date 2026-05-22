/// 消息模型
class Message {
  final int messageId;
  final int conversationId;
  final String content;
  final bool isFromUser;
  final DateTime createdAt;
  final EmotionType? emotion;
  final String? aiReply;

  Message({
    required this.messageId,
    required this.conversationId,
    required this.content,
    required this.isFromUser,
    required this.createdAt,
    this.emotion,
    this.aiReply,
  });

  factory Message.fromJson(Map<String, dynamic> json) {
    return Message(
      messageId: json['message_id'] ?? 0,
      conversationId: json['conversation_id'] ?? 0,
      content: json['content'] ?? '',
      isFromUser: json['is_from_user'] ?? true,
      createdAt: DateTime.parse(json['created_at'] ?? DateTime.now().toIso8601String()),
      emotion: json['emotion'] != null ? EmotionType.fromString(json['emotion']) : null,
      aiReply: json['ai_reply'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'message_id': messageId,
      'conversation_id': conversationId,
      'content': content,
      'is_from_user': isFromUser,
      'created_at': createdAt.toIso8601String(),
      'emotion': emotion?.name,
      'ai_reply': aiReply,
    };
  }
}

/// 情绪类型
enum EmotionType {
  happy,
  sad,
  angry,
  anxious,
  calm,
  excited,
  neutral;

  static EmotionType fromString(String? value) {
    if (value == null) return EmotionType.neutral;
    return EmotionType.values.firstWhere(
      (e) => e.name.toLowerCase() == value.toLowerCase(),
      orElse: () => EmotionType.neutral,
    );
  }

  String get displayName {
    switch (this) {
      case EmotionType.happy:
        return '开心';
      case EmotionType.sad:
        return '难过';
      case EmotionType.angry:
        return '生气';
      case EmotionType.anxious:
        return '焦虑';
      case EmotionType.calm:
        return '平静';
      case EmotionType.excited:
        return '兴奋';
      case EmotionType.neutral:
        return '中性';
    }
  }
}

/// 聊天请求
class ChatRequest {
  final String content;
  final int? conversationId;
  final Map<String, dynamic>? context;

  ChatRequest({
    required this.content,
    this.conversationId,
    this.context,
  });

  Map<String, dynamic> toJson() {
    return {
      'content': content,
      if (conversationId != null) 'conversation_id': conversationId,
      if (context != null) 'context': context,
    };
  }
}

/// 聊天响应
class ChatResponse {
  final String reply;
  final EmotionType detectedEmotion;
  final int? conversationId;
  final int? intimacyGained;

  ChatResponse({
    required this.reply,
    required this.detectedEmotion,
    this.conversationId,
    this.intimacyGained,
  });

  factory ChatResponse.fromJson(Map<String, dynamic> json) {
    return ChatResponse(
      reply: json['reply'] ?? '',
      detectedEmotion: EmotionType.fromString(json['detected_emotion']),
      conversationId: json['conversation_id'],
      intimacyGained: json['intimacy_gained'],
    );
  }
}

/// 聊天历史响应
class ChatHistoryResponse {
  final List<Message> messages;
  final int total;
  final int page;
  final int pageSize;

  ChatHistoryResponse({
    required this.messages,
    required this.total,
    required this.page,
    required this.pageSize,
  });

  factory ChatHistoryResponse.fromJson(Map<String, dynamic> json) {
    final List<dynamic> messagesJson = json['messages'] ?? [];
    return ChatHistoryResponse(
      messages: messagesJson.map((m) => Message.fromJson(m)).toList(),
      total: json['total'] ?? 0,
      page: json['page'] ?? 1,
      pageSize: json['page_size'] ?? 20,
    );
  }
}

/// 聊天建议
class ChatSuggestion {
  final String text;
  final String? icon;

  ChatSuggestion({
    required this.text,
    this.icon,
  });

  factory ChatSuggestion.fromJson(Map<String, dynamic> json) {
    return ChatSuggestion(
      text: json['text'] ?? '',
      icon: json['icon'],
    );
  }
}
