import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../utils/theme.dart';
import '../../models/diary.dart';
import '../../services/api_services.dart';
import '../../providers/cache_providers.dart';

/// 日记页面 — 匹配原型深色宇宙风格
class DiaryScreen extends ConsumerStatefulWidget {
  const DiaryScreen({super.key});

  @override
  ConsumerState<DiaryScreen> createState() => _DiaryScreenState();
}

class _DiaryScreenState extends ConsumerState<DiaryScreen> {
  DateTime _selectedDate = DateTime.now();
  MoodType _selectedMood = MoodType.happy;
  bool _isLoading = true;
  String? _error;
  List<DiaryEntry> _allDiaries = [];
  List<DiaryCalendarDay> _calendarDays = [];
  bool _showAllDiaries = false; // false: 默认只显示选中日期, true: 显示所有日记

  @override
  void initState() {
    super.initState();
    _loadDiaries();
    _loadCalendar();
  }

  Future<void> _loadDiaries({bool forceRefresh = false}) async {
    try {
      // 检查缓存
      final cache = ref.read(diaryCacheProvider);
      final now = DateTime.now();
      
      if (!forceRefresh && cache != null && cache.isValid(now.year, now.month)) {
        print('[DEBUG] Using cached diaries');
        setState(() {
          _allDiaries = cache.diaries;
          _isLoading = false;
        });
        return;
      }

      setState(() {
        _isLoading = true;
        _error = null;
      });

      final diaryService = ref.read(diaryServiceProvider);
      // 加载最近3个月的日记
      final diaries = await diaryService.getDiaries(
        startDate: DateTime(now.year, now.month - 2, 1),
        endDate: DateTime(now.year, now.month + 1, 0),
        page: 1,
        pageSize: 100,
      );

      // 更新缓存
      ref.read(diaryCacheProvider.notifier).state = DiaryCache(
        diaries: diaries,
        cachedAt: DateTime.now(),
        year: now.year,
        month: now.month,
      );

      setState(() {
        _allDiaries = diaries;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
        _error = '加载日记失败: $e';
      });
      _loadDefaultDiaries();
    }
  }

  Future<void> _loadCalendar() async {
    try {
      final diaryService = ref.read(diaryServiceProvider);
      final response = await diaryService.getCalendar(_selectedDate.year, _selectedDate.month);
      print('[DEBUG] Calendar loaded: ${response.days.map((d) => '${d.day}:${d.hasDiary}').toList()}');
      setState(() {
        _calendarDays = response.days;
      });
    } catch (e) {
      print('[DEBUG] Calendar load error: $e');
      final daysInMonth = DateTime(_selectedDate.year, _selectedDate.month + 1, 0).day;
      setState(() {
        _calendarDays = List.generate(daysInMonth, (i) => 
          DiaryCalendarDay(day: i + 1, hasDiary: false));
      });
    }
  }

  void _loadDefaultDiaries() {
    setState(() {
      _allDiaries = [
        DiaryEntry(
          diaryId: 1,
          date: DateTime.now(),
          content: '今天工作压力有点大，但和晚星聊了一会儿之后感觉好多了。她真的很会安慰人呢~',
          mood: MoodType.neutral,
          tags: ['工作', '加班', '音乐'],
          createdAt: DateTime.now().subtract(const Duration(hours: 2)),
        ),
        DiaryEntry(
          diaryId: 2,
          date: DateTime.now().subtract(const Duration(days: 1)),
          content: '周末和朋友去爬山了！天气特别好，心情也很棒。拍了好多照片想分享给晚星看。',
          mood: MoodType.veryHappy,
          tags: ['周末', '爬山', '朋友'],
          createdAt: DateTime.now().subtract(const Duration(days: 1, hours: 5)),
        ),
      ];
    });
  }

  Future<void> _addDiary(DateTime date, String content, MoodType mood, List<String>? tags) async {
    try {
      final request = AddDiaryRequest(
        date: date,
        content: content,
        mood: mood,
        tags: tags,
      );
      print('[DEBUG] Sending diary request: ${request.toJson()}');
      final diaryService = ref.read(diaryServiceProvider);
      await diaryService.addDiary(request);
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('日记已保存 📝'), backgroundColor: AppTheme.primary),
        );
      }
      
      // 清除缓存并强制刷新
      ref.read(diaryCacheProvider.notifier).state = null;
      _loadDiaries(forceRefresh: true);
      _loadCalendar();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('保存失败: $e'), backgroundColor: AppTheme.danger),
        );
      }
    }
  }

  /// 获取要显示的日记列表
  List<DiaryEntry> get _displayDiaries {
    if (_showAllDiaries) {
      return _allDiaries;
    } else {
      return _allDiaries.where((d) {
        return d.date.year == _selectedDate.year &&
               d.date.month == _selectedDate.month &&
               d.date.day == _selectedDate.day;
      }).toList();
    }
  }

  @override
  Widget build(BuildContext context) {
    final now = DateTime.now();
    final daysInMonth = DateTime(_selectedDate.year, _selectedDate.month + 1, 0).day;
    final firstWeekday = DateTime(_selectedDate.year, _selectedDate.month, 1).weekday;

    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: const Text('晚星日记'),
        actions: [
          // 切换显示模式按钮
          TextButton(
            onPressed: () => setState(() => _showAllDiaries = !_showAllDiaries),
            child: Text(
              _showAllDiaries ? '全部日记' : '筛选日期',
              style: const TextStyle(color: AppTheme.primary, fontSize: 13),
            ),
          ),
          if (_isLoading)
            const Padding(
              padding: EdgeInsets.only(right: 16),
              child: SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  valueColor: AlwaysStoppedAnimation<Color>(AppTheme.primary),
                ),
              ),
            ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          await _loadDiaries();
          await _loadCalendar();
        },
        color: AppTheme.primary,
        backgroundColor: const Color(0xFF0A0F24),
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(18, 8, 18, 100),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 错误提示
              if (_error != null)
                Container(
                  padding: const EdgeInsets.all(12),
                  margin: const EdgeInsets.only(bottom: 12),
                  decoration: BoxDecoration(
                    color: AppTheme.danger.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.error_outline, color: AppTheme.danger, size: 18),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          _error!,
                          style: TextStyle(color: AppTheme.danger, fontSize: 12),
                        ),
                      ),
                      TextButton(
                        onPressed: _loadDiaries,
                        child: const Text('重试', style: TextStyle(fontSize: 12)),
                      ),
                    ],
                  ),
                ),
              // 月份标签和切换
              Row(
                children: [
                  Text(
                    '${_selectedDate.year}年${_selectedDate.month}月',
                    style: const TextStyle(color: AppTheme.muted, fontSize: 14),
                  ),
                  const Spacer(),
                  // 选中日期的日记数量
                  if (!_showAllDiaries)
                    Text(
                      '${_displayDiaries.length} 篇日记',
                      style: const TextStyle(color: AppTheme.primary, fontSize: 12),
                    ),
                ],
              ),
              const SizedBox(height: 12),
              // 日历
              _buildCalendar(daysInMonth, firstWeekday, now),
              const SizedBox(height: 20),
              // 心情选择（仅今天显示）
              if (_isToday(_selectedDate)) ...[
                const Text('今天心情如何？', style: TextStyle(color: AppTheme.muted, fontSize: 13)),
                const SizedBox(height: 10),
                _buildMoodGrid(),
                const SizedBox(height: 20),
              ],
              // 日记列表标题
              Row(
                children: [
                  Text(
                    _showAllDiaries ? '所有日记' : '${_selectedDate.month}月${_selectedDate.day}日',
                    style: const TextStyle(color: AppTheme.text, fontSize: 16, fontWeight: FontWeight.w600),
                  ),
                  const Spacer(),
                  if (!_showAllDiaries && _displayDiaries.isEmpty)
                    Text(
                      '暂无日记',
                      style: TextStyle(color: AppTheme.muted, fontSize: 12),
                    ),
                ],
              ),
              const SizedBox(height: 12),
              // 日记列表
              if (_displayDiaries.isEmpty && !_isLoading)
                Center(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(vertical: 32),
                    child: Column(
                      children: [
                        Icon(
                          Icons.book_outlined,
                          size: 48,
                          color: AppTheme.soft.withOpacity(0.5),
                        ),
                        const SizedBox(height: 16),
                        Text(
                          _showAllDiaries ? '还没有日记' : '该日期暂无日记',
                          style: TextStyle(color: AppTheme.muted, fontSize: 14),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          '点击右下角开始写日记',
                          style: TextStyle(color: AppTheme.soft, fontSize: 12),
                        ),
                      ],
                    ),
                  ),
                )
              else
                ..._displayDiaries.map((d) => _DiaryCard(entry: d)),
            ],
          ),
        ),
      ),
      floatingActionButton: Container(
        decoration: AppTheme.primaryButtonDecoration,
        child: FloatingActionButton.extended(
          onPressed: () => _showWriteSheet(context),
          backgroundColor: Colors.transparent,
          elevation: 0,
          icon: const Icon(Icons.edit, color: Colors.white, size: 20),
          label: const Text('写日记', style: TextStyle(color: Colors.white, fontSize: 14)),
        ),
      ),
    );
  }

  bool _isToday(DateTime date) {
    final now = DateTime.now();
    return date.year == now.year && date.month == now.month && date.day == now.day;
  }

  Widget _buildCalendar(int days, int firstWeekday, DateTime now) {
    final weekLabels = ['一', '二', '三', '四', '五', '六', '日'];
    return Column(
      children: [
        // 星期头
        Row(
          children: weekLabels.map((l) {
            return Expanded(
              child: Center(
                child: Text(l, style: const TextStyle(color: AppTheme.soft, fontSize: 12)),
              ),
            );
          }).toList(),
        ),
        const SizedBox(height: 8),
        // 日期网格
        GridView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 7,
            mainAxisSpacing: 8,
            crossAxisSpacing: 8,
          ),
          itemCount: firstWeekday - 1 + days,
          itemBuilder: (_, i) {
            final day = i - (firstWeekday - 1) + 1;
            if (day < 1) return const SizedBox();
            
            final date = DateTime(_selectedDate.year, _selectedDate.month, day);
            final isSelected = day == _selectedDate.day;
            final isToday = _isToday(date);
            final isFuture = date.isAfter(DateTime.now());
            
            // 查找该日期是否有日记
            final matchingDays = _calendarDays.where((d) => d.day == day).toList();
            final hasDiary = matchingDays.isNotEmpty;
            final calendarDay = hasDiary 
                ? matchingDays.first 
                : DiaryCalendarDay(day: day, hasDiary: false);
            
            return GestureDetector(
              onTap: () {
                setState(() {
                  _selectedDate = date;
                  _showAllDiaries = false;
                });
              },
              child: Container(
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    color: isSelected ? AppTheme.primary : const Color(0x0FFFFFFF),
                    borderRadius: BorderRadius.circular(16),
                    border: hasDiary && !isSelected
                        ? Border.all(color: AppTheme.primary.withOpacity(0.5))
                        : isToday && !isSelected
                            ? Border.all(color: AppTheme.muted.withOpacity(0.3))
                            : null,
                  ),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        '$day',
                        style: TextStyle(
                          color: isSelected 
                              ? Colors.white 
                              : isFuture 
                                  ? AppTheme.soft.withOpacity(0.3)
                                  : AppTheme.text,
                          fontSize: 14,
                          fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                        ),
                      ),
                      if (hasDiary && calendarDay.mood != null)
                        Text(
                          calendarDay.mood!.emoji,
                          style: const TextStyle(fontSize: 10),
                        ),
                    ],
                  ),
                ),
            );
          },
        ),
      ],
    );
  }

  Widget _buildMoodGrid() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceAround,
      children: MoodType.values.map((mood) {
        final active = _selectedMood == mood;
        return GestureDetector(
          onTap: () => setState(() => _selectedMood = mood),
          child: Column(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: active ? AppTheme.primary.withOpacity(0.34) : const Color(0x0FFFFFFF),
                  shape: BoxShape.circle,
                  border: active
                      ? Border.all(color: AppTheme.primary.withOpacity(0.72))
                      : null,
                ),
                alignment: Alignment.center,
                child: Text(mood.emoji, style: const TextStyle(fontSize: 24)),
              ),
              const SizedBox(height: 6),
              Text(
                mood.displayName,
                style: TextStyle(
                  color: active ? AppTheme.activeNav : AppTheme.muted,
                  fontSize: 11,
                ),
              ),
            ],
          ),
        );
      }).toList(),
    );
  }

  void _showWriteSheet(BuildContext context) {
    final ctrl = TextEditingController();
    final tagCtrl = TextEditingController();
    List<String> tags = [];
    // 使用当前选中的日期，而不是 DateTime.now()
    DateTime selectedDiaryDate = _selectedDate;
    
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: const Color(0xDD0A0F24),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (ctx) => StatefulBuilder(
        builder: (context, setModalState) => Padding(
          padding: EdgeInsets.only(
            left: 20, right: 20, top: 20,
            bottom: MediaQuery.of(ctx).viewInsets.bottom + 20,
          ),
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('写日记', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w700, color: AppTheme.text)),
                const SizedBox(height: 16),
                // 日期选择
                Row(
                  children: [
                    const Icon(Icons.calendar_today, color: AppTheme.muted, size: 18),
                    const SizedBox(width: 8),
                    GestureDetector(
                      onTap: () async {
                        final date = await showDatePicker(
                          context: context,
                          initialDate: selectedDiaryDate,
                          firstDate: DateTime(2020),
                          lastDate: DateTime.now(), // 只能选择今天及之前的日期
                          builder: (context, child) {
                            return Theme(
                              data: Theme.of(context).copyWith(
                                colorScheme: const ColorScheme.dark(
                                  primary: AppTheme.primary,
                                  surface: Color(0xFF0A0F24),
                                ),
                              ),
                              child: child!,
                            );
                          },
                        );
                        if (date != null) {
                          setModalState(() => selectedDiaryDate = date);
                        }
                      },
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                        decoration: BoxDecoration(
                          color: const Color(0x14FFFFFF),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: AppTheme.line),
                        ),
                        child: Text(
                          '${selectedDiaryDate.year}/${selectedDiaryDate.month}/${selectedDiaryDate.day}',
                          style: const TextStyle(color: AppTheme.text, fontSize: 14),
                        ),
                      ),
                    ),
                    const Spacer(),
                    Text(_selectedMood.emoji, style: const TextStyle(fontSize: 20)),
                    const SizedBox(width: 4),
                    Text(_selectedMood.displayName, style: const TextStyle(color: AppTheme.muted, fontSize: 14)),
                  ],
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: ctrl,
                  maxLines: 6,
                  style: const TextStyle(color: AppTheme.text),
                  decoration: InputDecoration(
                    hintText: '写下今天发生的事...',
                    hintStyle: const TextStyle(color: AppTheme.soft),
                  ),
                ),
                const SizedBox(height: 12),
                // 标签输入
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: tagCtrl,
                        style: const TextStyle(color: AppTheme.text, fontSize: 14),
                        decoration: InputDecoration(
                          hintText: '添加标签...',
                          hintStyle: const TextStyle(color: AppTheme.soft, fontSize: 14),
                        ),
                        onSubmitted: (value) {
                          if (value.trim().isNotEmpty && !tags.contains(value.trim())) {
                            setModalState(() {
                              tags.add(value.trim());
                              tagCtrl.clear();
                            });
                          }
                        },
                      ),
                    ),
                    const SizedBox(width: 8),
                    // 添加标签按钮
                    GestureDetector(
                      onTap: () {
                        if (tagCtrl.text.trim().isNotEmpty && !tags.contains(tagCtrl.text.trim())) {
                          setModalState(() {
                            tags.add(tagCtrl.text.trim());
                            tagCtrl.clear();
                          });
                        }
                      },
                      child: Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: AppTheme.primary.withOpacity(0.3),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: const Icon(Icons.add, color: Colors.white, size: 20),
                      ),
                    ),
                  ],
                ),
                if (tags.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    runSpacing: 4,
                    children: tags.map((tag) => GestureDetector(
                      onTap: () => setModalState(() => tags.remove(tag)),
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                        decoration: BoxDecoration(
                          color: AppTheme.primary.withOpacity(0.2),
                          borderRadius: BorderRadius.circular(16),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text('#$tag', style: const TextStyle(fontSize: 12, color: AppTheme.text)),
                            const SizedBox(width: 4),
                            const Icon(Icons.close, size: 14, color: AppTheme.muted),
                          ],
                        ),
                      ),
                    )).toList(),
                  ),
                ],
                const SizedBox(height: 16),
                SizedBox(
                  width: double.infinity,
                  child: Container(
                    decoration: AppTheme.primaryButtonDecoration,
                    child: ElevatedButton(
                      onPressed: () {
                        if (ctrl.text.trim().isNotEmpty) {
                          Navigator.pop(ctx);
                          _addDiary(selectedDiaryDate, ctrl.text.trim(), _selectedMood, tags.isEmpty ? null : tags);
                        }
                      },
                      style: ElevatedButton.styleFrom(backgroundColor: Colors.transparent, elevation: 0),
                      child: const Text('保存', style: TextStyle(fontSize: 15)),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

/// 日记卡片
class _DiaryCard extends StatelessWidget {
  final DiaryEntry entry;
  const _DiaryCard({required this.entry});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment(-1, -0.5),
          end: Alignment(1, 1),
          colors: [Color(0x9477469C), Color(0xDB1A254B)],
        ),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppTheme.line),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(entry.mood?.emoji ?? '😐', style: const TextStyle(fontSize: 22)),
              const SizedBox(width: 8),
              Text(entry.mood?.displayName ?? '一般', style: const TextStyle(color: AppTheme.text, fontSize: 14, fontWeight: FontWeight.w500)),
              const Spacer(),
              Text(
                '${entry.date.month}/${entry.date.day} ${entry.createdAt.hour.toString().padLeft(2, '0')}:${entry.createdAt.minute.toString().padLeft(2, '0')}',
                style: const TextStyle(color: AppTheme.muted, fontSize: 12),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(entry.content ?? '', style: const TextStyle(color: Color(0xFFE5E2F8), fontSize: 14, height: 1.65)),
          if (entry.tags != null && entry.tags!.isNotEmpty) ...[
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              children: entry.tags!.map((t) {
                return Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                  decoration: BoxDecoration(
                    color: const Color(0x14FFFFFF),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppTheme.line),
                  ),
                  child: Text('#$t', style: const TextStyle(color: AppTheme.muted, fontSize: 12)),
                );
              }).toList(),
            ),
          ],
        ],
      ),
    );
  }
}
