import 'message.dart';

/// 日记条目模型
class DiaryEntry {
  final int diaryId;
  final DateTime date;
  final String? content;
  final MoodType? mood;
  final List<String>? tags;
  final DateTime createdAt;
  final DateTime? updatedAt;

  DiaryEntry({
    required this.diaryId,
    required this.date,
    this.content,
    this.mood,
    this.tags,
    required this.createdAt,
    this.updatedAt,
  });

  factory DiaryEntry.fromJson(Map<String, dynamic> json) {
    // 后端返回的是 'happened_on'，但前端期望 'date'
    final dateStr = json['date'] ?? json['happened_on'] ?? DateTime.now().toIso8601String();
    return DiaryEntry(
      diaryId: json['diary_id'] ?? json['id'] ?? 0,
      date: DateTime.parse(dateStr),
      content: json['content'],
      mood: json['mood'] != null ? MoodType.fromString(json['mood']) : null,
      tags: json['tags'] != null ? List<String>.from(json['tags']) : null,
      createdAt: DateTime.parse(json['created_at'] ?? DateTime.now().toIso8601String()),
      updatedAt: json['updated_at'] != null ? DateTime.parse(json['updated_at']) : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'diary_id': diaryId,
      'date': date.toIso8601String(),
      'content': content,
      'mood': mood?.name,
      'tags': tags,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt?.toIso8601String(),
    };
  }
}

/// 心情类型
enum MoodType {
  veryHappy,
  happy,
  neutral,
  sad,
  verySad;

  static MoodType fromString(String? value) {
    if (value == null) return MoodType.neutral;
    return MoodType.values.firstWhere(
      (e) => e.name.toLowerCase() == value.toLowerCase(),
      orElse: () => MoodType.neutral,
    );
  }

  String get displayName {
    switch (this) {
      case MoodType.veryHappy:
        return '非常开心';
      case MoodType.happy:
        return '开心';
      case MoodType.neutral:
        return '一般';
      case MoodType.sad:
        return '难过';
      case MoodType.verySad:
        return '非常难过';
    }
  }

  String get emoji {
    switch (this) {
      case MoodType.veryHappy:
        return '😄';
      case MoodType.happy:
        return '😊';
      case MoodType.neutral:
        return '😐';
      case MoodType.sad:
        return '😢';
      case MoodType.verySad:
        return '😭';
    }
  }
}

/// 添加日记请求
class AddDiaryRequest {
  final DateTime date;
  final String content;
  final MoodType mood;
  final List<String>? tags;

  AddDiaryRequest({
    required this.date,
    required this.content,
    required this.mood,
    this.tags,
  });

  Map<String, dynamic> toJson() {
    return {
      'happened_on': date.toIso8601String().split('T')[0], // 后端期望 happened_on，格式为 YYYY-MM-DD
      'content': content,
      'mood': mood.name,
      if (tags != null) 'tags': tags,
    };
  }
}

/// 日记日历响应
class DiaryCalendarResponse {
  final int year;
  final int month;
  final List<DiaryCalendarDay> days;

  DiaryCalendarResponse({
    required this.year,
    required this.month,
    required this.days,
  });

  factory DiaryCalendarResponse.fromJson(Map<String, dynamic> json) {
    // 后端返回的是 'dates'，但前端期望 'days'
    final List<dynamic> daysJson = json['days'] ?? json['dates'] ?? [];
    return DiaryCalendarResponse(
      year: json['year'] ?? DateTime.now().year,
      month: json['month'] ?? DateTime.now().month,
      days: daysJson.map((d) => DiaryCalendarDay.fromJson(d)).toList(),
    );
  }
}

/// 日历中的某一天
class DiaryCalendarDay {
  final int day;
  final bool hasDiary;
  final MoodType? mood;

  DiaryCalendarDay({
    required this.day,
    required this.hasDiary,
    this.mood,
  });

  factory DiaryCalendarDay.fromJson(Map<String, dynamic> json) {
    return DiaryCalendarDay(
      day: json['day'] ?? 1,
      hasDiary: json['has_diary'] ?? false,
      mood: json['mood'] != null ? MoodType.fromString(json['mood']) : null,
    );
  }
}
