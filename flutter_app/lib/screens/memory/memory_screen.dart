import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../utils/theme.dart';
import '../../models/memory.dart';
import '../../services/api_services.dart';
import '../../providers/cache_providers.dart';

/// 记忆页面 — 匹配原型深色宇宙风格
class MemoryScreen extends ConsumerStatefulWidget {
  const MemoryScreen({super.key});

  @override
  ConsumerState<MemoryScreen> createState() => _MemoryScreenState();
}

class _MemoryScreenState extends ConsumerState<MemoryScreen> {
  MemoryCategory? _selectedCategory; // null 表示全部
  bool _isLoading = true;
  String? _error;
  List<Memory> _allMemories = [];

  @override
  void initState() {
    super.initState();
    _loadMemories();
  }

  Future<void> _loadMemories({bool forceRefresh = false}) async {
    try {
      // 检查缓存
      final cache = ref.read(memoryCacheProvider);
      final category = _selectedCategory?.name;
      
      if (!forceRefresh && cache != null && cache.isValid(category)) {
        print('[DEBUG] Using cached memories');
        setState(() {
          _allMemories = cache.memories;
          _isLoading = false;
        });
        return;
      }

      setState(() {
        _isLoading = true;
        _error = null;
      });

      final memoryService = ref.read(memoryServiceProvider);
      final memories = await memoryService.getMemories(
        category: category,
        page: 1,
        pageSize: 50,
      );

      // 更新缓存
      ref.read(memoryCacheProvider.notifier).state = MemoryCache(
        memories: memories,
        cachedAt: DateTime.now(),
        category: category,
      );

      setState(() {
        _allMemories = memories;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
        _error = '加载记忆失败: $e';
      });
      _loadDefaultMemories();
    }
  }

  void _loadDefaultMemories() {
    setState(() {
      _allMemories = [
        Memory(memoryId: 1, content: '你最喜欢在雨天听爵士乐', category: MemoryCategory.preference, createdAt: DateTime.now().subtract(const Duration(days: 3)), recallCount: 5),
        Memory(memoryId: 2, content: '你的生日是 3 月 15 日', category: MemoryCategory.personal, createdAt: DateTime.now().subtract(const Duration(days: 7)), recallCount: 12),
        Memory(memoryId: 3, content: '你最近在准备面试，有点紧张', category: MemoryCategory.event, createdAt: DateTime.now().subtract(const Duration(days: 1)), recallCount: 3),
        Memory(memoryId: 4, content: '你养了一只叫「团子」的猫', category: MemoryCategory.personal, createdAt: DateTime.now().subtract(const Duration(days: 10)), recallCount: 8),
        Memory(memoryId: 5, content: '你梦想去冰岛看极光', category: MemoryCategory.milestone, createdAt: DateTime.now().subtract(const Duration(days: 14)), recallCount: 2),
      ];
    });
  }

  Future<void> _addMemory(String content, MemoryCategory category) async {
    try {
      final memoryService = ref.read(memoryServiceProvider);
      await memoryService.addMemory(
        AddMemoryRequest(content: content, category: category),
      );

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('记忆已保存 ✨'), backgroundColor: AppTheme.primary),
        );
      }

      // 清除缓存并强制刷新
      ref.read(memoryCacheProvider.notifier).state = null;
      _loadMemories(forceRefresh: true);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('保存失败: $e'), backgroundColor: AppTheme.danger),
        );
      }
    }
  }

  Future<void> _deleteMemory(int memoryId) async {
    try {
      final memoryService = ref.read(memoryServiceProvider);
      await memoryService.deleteMemory(memoryId);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('记忆已删除'), backgroundColor: AppTheme.primary),
        );
      }

      // 清除缓存并强制刷新
      ref.read(memoryCacheProvider.notifier).state = null;
      _loadMemories(forceRefresh: true);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('删除失败: $e'), backgroundColor: AppTheme.danger),
        );
      }
    }
  }

  /// 根据选中分类筛选记忆
  List<Memory> get _filteredMemories {
    if (_selectedCategory == null) {
      return _allMemories;
    }
    return _allMemories.where((m) => m.category == _selectedCategory).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: const Text('我们的记忆'),
        actions: [
          // 显示当前筛选的分类数量
          if (_selectedCategory != null)
            TextButton(
              onPressed: () {
                setState(() => _selectedCategory = null);
                _loadMemories();
              },
              child: const Text('显示全部', style: TextStyle(color: AppTheme.primary, fontSize: 13)),
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
      body: Column(
        children: [
          // 错误提示
          if (_error != null)
            Container(
              padding: const EdgeInsets.all(12),
              color: AppTheme.danger.withOpacity(0.1),
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
                    onPressed: _loadMemories,
                    child: const Text('重试', style: TextStyle(fontSize: 12)),
                  ),
                ],
              ),
            ),
          // 分类筛选标签
          Container(
            height: 48,
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 18),
              itemCount: MemoryCategory.values.length + 1, // +1 for "全部"
              separatorBuilder: (_, __) => const SizedBox(width: 8),
              itemBuilder: (_, i) {
                // 第一个是"全部"
                if (i == 0) {
                  final isActive = _selectedCategory == null;
                  return GestureDetector(
                    onTap: () {
                      setState(() => _selectedCategory = null);
                      _loadMemories();
                    },
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                      decoration: BoxDecoration(
                        color: isActive
                            ? AppTheme.primary.withOpacity(0.34)
                            : const Color(0x14FFFFFF),
                        borderRadius: BorderRadius.circular(17),
                        border: Border.all(
                          color: isActive
                              ? AppTheme.primary.withOpacity(0.72)
                              : AppTheme.line,
                        ),
                      ),
                      alignment: Alignment.center,
                      child: Text(
                        '全部',
                        style: TextStyle(
                          color: isActive ? AppTheme.activeNav : AppTheme.muted,
                          fontSize: 13,
                        ),
                      ),
                    ),
                  );
                }
                
                // 其他是各个分类
                final category = MemoryCategory.values[i - 1];
                final isActive = _selectedCategory == category;
                return GestureDetector(
                  onTap: () {
                    setState(() => _selectedCategory = category);
                    _loadMemories();
                  },
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    decoration: BoxDecoration(
                      color: isActive
                          ? AppTheme.primary.withOpacity(0.34)
                          : const Color(0x14FFFFFF),
                      borderRadius: BorderRadius.circular(17),
                      border: Border.all(
                        color: isActive
                            ? AppTheme.primary.withOpacity(0.72)
                            : AppTheme.line,
                      ),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(category.icon, style: const TextStyle(fontSize: 14)),
                        const SizedBox(width: 4),
                        Text(
                          category.displayName,
                          style: TextStyle(
                            color: isActive ? AppTheme.activeNav : AppTheme.muted,
                            fontSize: 13,
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
          // 记忆数量统计
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 8),
            child: Row(
              children: [
                Text(
                  '共 ${_filteredMemories.length} 条记忆',
                  style: const TextStyle(color: AppTheme.muted, fontSize: 12),
                ),
                if (_selectedCategory != null) ...[
                  const SizedBox(width: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: AppTheme.primary.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(_selectedCategory!.icon, style: const TextStyle(fontSize: 10)),
                        const SizedBox(width: 2),
                        Text(
                          _selectedCategory!.displayName,
                          style: const TextStyle(color: AppTheme.primary, fontSize: 10),
                        ),
                      ],
                    ),
                  ),
                ],
              ],
            ),
          ),
          // 记忆列表
          Expanded(
            child: RefreshIndicator(
              onRefresh: _loadMemories,
              color: AppTheme.primary,
              backgroundColor: const Color(0xFF0A0F24),
              child: _filteredMemories.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(
                            Icons.memory_outlined,
                            size: 48,
                            color: AppTheme.soft.withOpacity(0.5),
                          ),
                          const SizedBox(height: 16),
                          Text(
                            _selectedCategory == null 
                                ? '还没有记忆' 
                                : '该分类下没有记忆',
                            style: TextStyle(
                              color: AppTheme.muted,
                              fontSize: 14,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            '点击右下角添加你的第一条记忆',
                            style: TextStyle(
                              color: AppTheme.soft,
                              fontSize: 12,
                            ),
                          ),
                        ],
                      ),
                    )
                  : ListView.separated(
                      padding: const EdgeInsets.fromLTRB(18, 12, 18, 100),
                      itemCount: _filteredMemories.length,
                      separatorBuilder: (_, __) => Divider(color: AppTheme.line, height: 1),
                      itemBuilder: (_, i) => Dismissible(
                        key: Key(_filteredMemories[i].memoryId.toString()),
                        direction: DismissDirection.endToStart,
                        background: Container(
                          alignment: Alignment.centerRight,
                          padding: const EdgeInsets.only(right: 20),
                          color: AppTheme.danger,
                          child: const Icon(Icons.delete, color: Colors.white),
                        ),
                        onDismissed: (_) => _deleteMemory(_filteredMemories[i].memoryId),
                        child: _MemoryRow(memory: _filteredMemories[i]),
                      ),
                    ),
            ),
          ),
        ],
      ),
      floatingActionButton: Container(
        decoration: AppTheme.primaryButtonDecoration,
        child: FloatingActionButton.extended(
          onPressed: () => _showAddSheet(context),
          backgroundColor: Colors.transparent,
          elevation: 0,
          icon: const Icon(Icons.add, color: Colors.white, size: 20),
          label: const Text('添加记忆', style: TextStyle(color: Colors.white, fontSize: 14)),
        ),
      ),
    );
  }

  void _showAddSheet(BuildContext context) {
    final ctrl = TextEditingController();
    // 默认选择当前筛选的分类，如果没筛选则默认选 personal
    MemoryCategory selectedCategory = _selectedCategory ?? MemoryCategory.personal;
    
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
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('添加记忆', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w700, color: AppTheme.text)),
              const SizedBox(height: 8),
              Text(
                '选择分类后，记忆会自动归类到对应标签下',
                style: TextStyle(color: AppTheme.muted, fontSize: 12),
              ),
              const SizedBox(height: 16),
              // 分类选择
              SizedBox(
                height: 40,
                child: ListView.separated(
                  scrollDirection: Axis.horizontal,
                  itemCount: MemoryCategory.values.length,
                  separatorBuilder: (_, __) => const SizedBox(width: 8),
                  itemBuilder: (_, i) {
                    final category = MemoryCategory.values[i];
                    final isSelected = category == selectedCategory;
                    return GestureDetector(
                      onTap: () => setModalState(() => selectedCategory = category),
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                        decoration: BoxDecoration(
                          color: isSelected ? AppTheme.primary.withOpacity(0.34) : const Color(0x14FFFFFF),
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(
                            color: isSelected ? AppTheme.primary.withOpacity(0.72) : AppTheme.line,
                          ),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text(category.icon, style: const TextStyle(fontSize: 14)),
                            const SizedBox(width: 4),
                            Text(
                              category.displayName,
                              style: TextStyle(
                                color: isSelected ? AppTheme.activeNav : AppTheme.muted,
                                fontSize: 12,
                              ),
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: ctrl,
                maxLines: 4,
                style: const TextStyle(color: AppTheme.text),
                decoration: InputDecoration(
                  hintText: '写下你想记住的事情...',
                  hintStyle: const TextStyle(color: AppTheme.soft),
                ),
              ),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: Container(
                  decoration: AppTheme.primaryButtonDecoration,
                  child: ElevatedButton(
                    onPressed: () {
                      if (ctrl.text.trim().isNotEmpty) {
                        Navigator.pop(ctx);
                        _addMemory(ctrl.text.trim(), selectedCategory);
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
    );
  }
}

class _MemoryRow extends StatelessWidget {
  final Memory memory;
  const _MemoryRow({required this.memory});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 14),
      child: Row(
        children: [
          // 图标
          Container(
            width: 34,
            height: 34,
            decoration: BoxDecoration(
              color: AppTheme.primary.withOpacity(0.2),
              borderRadius: BorderRadius.circular(12),
            ),
            alignment: Alignment.center,
            child: Text(memory.category.icon, style: const TextStyle(fontSize: 16)),
          ),
          const SizedBox(width: 10),
          // 内容
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(memory.content, style: const TextStyle(color: AppTheme.text, fontSize: 14, height: 1.4)),
                const SizedBox(height: 4),
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: AppTheme.primary.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(memory.category.icon, style: const TextStyle(fontSize: 10)),
                          const SizedBox(width: 2),
                          Text(
                            memory.category.displayName,
                            style: const TextStyle(color: AppTheme.muted, fontSize: 10),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      '${memory.recallCount} 次回忆 · ${_fmt(memory.createdAt)}',
                      style: const TextStyle(color: AppTheme.muted, fontSize: 12),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const Icon(Icons.chevron_right, color: AppTheme.soft, size: 18),
        ],
      ),
    );
  }

  String _fmt(DateTime t) => '${t.month}月${t.day}日';
}
