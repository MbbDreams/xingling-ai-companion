/// 成长总结
class GrowthSummary {
  final int intimacyLevel;
  final int intimacyPoints;
  final int intimacyForNext;
  final int totalMessages;
  final int milestonesCount;
  final int activeDays;

  GrowthSummary({
    required this.intimacyLevel,
    required this.intimacyPoints,
    required this.intimacyForNext,
    required this.totalMessages,
    required this.milestonesCount,
    required this.activeDays,
  });

  factory GrowthSummary.fromJson(Map<String, dynamic> json) {
    return GrowthSummary(
      intimacyLevel: json['intimacy_level'] ?? 1,
      intimacyPoints: json['intimacy_points'] ?? 0,
      intimacyForNext: json['intimacy_for_next'] ?? 100,
      totalMessages: json['total_messages'] ?? 0,
      milestonesCount: json['milestones_count'] ?? 0,
      activeDays: json['active_days'] ?? 0,
    );
  }
}

/// 成长里程碑
class GrowthMilestone {
  final int id;
  final String title;
  final String? description;
  final DateTime achievedAt;

  GrowthMilestone({
    required this.id,
    required this.title,
    this.description,
    required this.achievedAt,
  });

  factory GrowthMilestone.fromJson(Map<String, dynamic> json) {
    return GrowthMilestone(
      id: json['id'] ?? 0,
      title: json['title'] ?? '',
      description: json['description'],
      achievedAt: DateTime.parse(
        json['achieved_at'] ?? DateTime.now().toIso8601String(),
      ),
    );
  }
}

/// 每日任务
class DailyTask {
  final int taskId;
  final String title;
  final String description;
  final String icon;
  final int rewardCoins;
  final bool isCompleted;

  DailyTask({
    required this.taskId,
    required this.title,
    required this.description,
    required this.icon,
    required this.rewardCoins,
    this.isCompleted = false,
  });

  factory DailyTask.fromJson(Map<String, dynamic> json) {
    return DailyTask(
      taskId: json['task_id'] ?? json['id'] ?? 0,
      title: json['title'] ?? '',
      description: json['description'] ?? '',
      icon: json['icon'] ?? '✨',
      rewardCoins: json['reward_coins'] ?? json['coins'] ?? 0,
      isCompleted: json['is_completed'] ?? json['completed'] ?? false,
    );
  }
}

/// 任务完成响应
class TaskCompleteResponse {
  final bool success;
  final int coinsEarned;
  final String message;

  TaskCompleteResponse({
    required this.success,
    required this.coinsEarned,
    required this.message,
  });

  factory TaskCompleteResponse.fromJson(Map<String, dynamic> json) {
    return TaskCompleteResponse(
      success: json['success'] ?? true,
      coinsEarned: json['coins_earned'] ?? json['coins'] ?? 0,
      message: json['message'] ?? '任务完成',
    );
  }
}
