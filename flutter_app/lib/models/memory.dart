/// 记忆模型
class Memory {
  final int memoryId;
  final String content;
  final MemoryCategory category;
  final DateTime createdAt;
  final DateTime? lastRecalledAt;
  final int recallCount;

  Memory({
    required this.memoryId,
    required this.content,
    required this.category,
    required this.createdAt,
    this.lastRecalledAt,
    this.recallCount = 0,
  });

  factory Memory.fromJson(Map<String, dynamic> json) {
    return Memory(
      memoryId: json['id'] ?? json['memory_id'] ?? 0,
      content: json['memory'] ?? json['content'] ?? '',
      category: MemoryCategory.fromString(json['category']),
      createdAt: DateTime.parse(json['created_at'] ?? DateTime.now().toIso8601String()),
      lastRecalledAt: json['last_recalled_at'] != null
          ? DateTime.parse(json['last_recalled_at'])
          : null,
      recallCount: json['recall_count'] ?? 0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': memoryId,
      'memory': content,
      'category': category.name,
      'created_at': createdAt.toIso8601String(),
      'last_recalled_at': lastRecalledAt?.toIso8601String(),
      'recall_count': recallCount,
    };
  }
}

/// 记忆分类
enum MemoryCategory {
  personal,
  event,
  preference,
  conversation,
  milestone;

  static MemoryCategory fromString(String? value) {
    if (value == null) return MemoryCategory.personal;
    return MemoryCategory.values.firstWhere(
      (e) => e.name.toLowerCase() == value.toLowerCase(),
      orElse: () => MemoryCategory.personal,
    );
  }

  String get displayName {
    switch (this) {
      case MemoryCategory.personal:
        return '个人信息';
      case MemoryCategory.event:
        return '重要事件';
      case MemoryCategory.preference:
        return '喜好习惯';
      case MemoryCategory.conversation:
        return '对话记忆';
      case MemoryCategory.milestone:
        return '里程碑';
    }
  }

  String get icon {
    switch (this) {
      case MemoryCategory.personal:
        return '👤';
      case MemoryCategory.event:
        return '🎉';
      case MemoryCategory.preference:
        return '❤️';
      case MemoryCategory.conversation:
        return '💬';
      case MemoryCategory.milestone:
        return '⭐';
    }
  }
}

/// 添加记忆请求
class AddMemoryRequest {
  final String content;
  final MemoryCategory category;

  AddMemoryRequest({
    required this.content,
    required this.category,
  });

  Map<String, dynamic> toJson() {
    return {
      'memory': content,
      'category': category.name,
    };
  }
}
