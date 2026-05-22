import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/diary.dart';
import '../models/memory.dart';

/// 日记缓存状态
class DiaryCache {
  final List<DiaryEntry> diaries;
  final DateTime cachedAt;
  final int year;
  final int month;

  DiaryCache({
    required this.diaries,
    required this.cachedAt,
    required this.year,
    required this.month,
  });

  bool isValid(int year, int month) {
    // 缓存5分钟内有效，且年月匹配
    return this.year == year &&
           this.month == month &&
           DateTime.now().difference(cachedAt).inMinutes < 5;
  }
}

/// 记忆缓存状态
class MemoryCache {
  final List<Memory> memories;
  final DateTime cachedAt;
  final String? category;

  MemoryCache({
    required this.memories,
    required this.cachedAt,
    this.category,
  });

  bool isValid(String? category) {
    // 缓存3分钟内有效，且分类匹配
    return this.category == category &&
           DateTime.now().difference(cachedAt).inMinutes < 3;
  }
}

/// 日记缓存 Provider
final diaryCacheProvider = StateProvider<DiaryCache?>((ref) => null);

/// 记忆缓存 Provider
final memoryCacheProvider = StateProvider<MemoryCache?>((ref) => null);

/// 清除所有缓存
void clearAllCache(WidgetRef ref) {
  ref.read(diaryCacheProvider.notifier).state = null;
  ref.read(memoryCacheProvider.notifier).state = null;
}
