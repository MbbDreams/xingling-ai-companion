import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../utils/theme.dart';
import '../../models/growth.dart';
import '../../services/api_services.dart';
import '../../providers/auth_provider.dart';

/// 发现页面 — 匹配原型深色宇宙风格
class DiscoverScreen extends ConsumerStatefulWidget {
  const DiscoverScreen({super.key});

  @override
  ConsumerState<DiscoverScreen> createState() => _DiscoverScreenState();
}

class _DiscoverScreenState extends ConsumerState<DiscoverScreen> {
  bool _isLoading = true;
  String? _error;
  List<DailyTask> _tasks = [];

  @override
  void initState() {
    super.initState();
    _loadTasks();
  }

  Future<void> _loadTasks() async {
    try {
      setState(() {
        _isLoading = true;
        _error = null;
      });

      final discoverService = ref.read(discoverServiceProvider);
      final tasksData = await discoverService.getTasks();

      setState(() {
        _tasks = tasksData.map((json) => DailyTask.fromJson(json)).toList();
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
        _error = '加载任务失败: $e';
      });
      _loadDefaultTasks();
    }
  }

  void _loadDefaultTasks() {
    setState(() {
      _tasks = [
        DailyTask(taskId: 1, title: '冥想放松', description: '和晚星一起做5分钟冥想', icon: '🧘', rewardCoins: 10),
        DailyTask(taskId: 2, title: 'AI绘画', description: '让晚星为你画一幅画', icon: '🎨', rewardCoins: 15),
        DailyTask(taskId: 3, title: '写故事', description: '和晚星共同创作一个故事', icon: '📖', rewardCoins: 20),
        DailyTask(taskId: 4, title: '旅行计划', description: '规划一次虚拟旅行', icon: '✈️', rewardCoins: 15),
        DailyTask(taskId: 5, title: '知识问答', description: '和晚星玩问答游戏', icon: '❓', rewardCoins: 10),
      ];
    });
  }

  Future<void> _completeTask(int taskId) async {
    try {
      final discoverService = ref.read(discoverServiceProvider);
      final responseData = await discoverService.completeTask(taskId);
      final response = TaskCompleteResponse.fromJson(responseData);

      if (mounted) {
        final intimacyText = response.intimacyGained != null 
            ? '，亲密度 +${response.intimacyGained}' 
            : '';
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('任务完成！获得 ${response.coinsEarned} 星币$intimacyText ✨'),
            backgroundColor: AppTheme.primary,
          ),
        );
      }

      // 刷新任务列表
      _loadTasks();
      
      // 刷新用户信息以更新星币显示
      await ref.read(authProvider.notifier).refreshUser();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('完成任务失败: $e'), backgroundColor: AppTheme.danger),
        );
      }
    }
  }

  Future<void> _makeWish(String content) async {
    try {
      final discoverService = ref.read(discoverServiceProvider);
      await discoverService.makeWish(content);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('愿望已许下，晚星会帮你守护 ✨'),
            backgroundColor: AppTheme.primary,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('许愿失败: $e'), backgroundColor: AppTheme.danger),
        );
      }
    }
  }

  void _showWishDialog() {
    final ctrl = TextEditingController();
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF0A0F24),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text('晚星许愿灯', style: TextStyle(color: AppTheme.text)),
        content: TextField(
          controller: ctrl,
          maxLines: 3,
          style: const TextStyle(color: AppTheme.text),
          decoration: InputDecoration(
            hintText: '写下你的心愿...',
            hintStyle: const TextStyle(color: AppTheme.soft),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: AppTheme.line),
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('取消', style: TextStyle(color: AppTheme.muted)),
          ),
          Container(
            decoration: AppTheme.primaryButtonDecoration,
            child: TextButton(
              onPressed: () {
                if (ctrl.text.trim().isNotEmpty) {
                  Navigator.pop(ctx);
                  _makeWish(ctrl.text.trim());
                }
              },
              child: const Text('许愿', style: TextStyle(color: Colors.white)),
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: const Text('发现'),
        actions: [
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
        onRefresh: _loadTasks,
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
                        onPressed: _loadTasks,
                        child: const Text('重试', style: TextStyle(fontSize: 12)),
                      ),
                    ],
                  ),
                ),
              // 许愿灯卡片
              _WishCard(onTap: _showWishDialog),
              const SizedBox(height: 20),
              // 每日任务
              const Text('每日任务', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: AppTheme.text)),
              const SizedBox(height: 12),
              ..._tasks.map((t) => _ActivityCard(
                task: t,
                onComplete: () => _completeTask(t.taskId),
              )),
            ],
          ),
        ),
      ),
    );
  }
}

class _WishCard extends StatelessWidget {
  final VoidCallback onTap;
  
  const _WishCard({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            begin: Alignment(-1, -0.3),
            end: Alignment(1, 0.8),
            colors: [Color(0x994B3A91), Color(0xB3111934)],
          ),
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: AppTheme.line),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text('晚星许愿灯', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: AppTheme.text)),
                  const SizedBox(height: 6),
                  Text('写下你的心愿，让晚星帮你守护', style: TextStyle(fontSize: 13, color: AppTheme.muted)),
                  const SizedBox(height: 14),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    decoration: AppTheme.primaryButtonDecoration,
                    child: const Text('去许愿', style: TextStyle(color: Colors.white, fontSize: 13)),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 16),
            const Text('🏮', style: TextStyle(fontSize: 56)),
          ],
        ),
      ),
    );
  }
}

class _ActivityCard extends StatelessWidget {
  final DailyTask task;
  final VoidCallback onComplete;
  
  const _ActivityCard({required this.task, required this.onComplete});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: const Color(0x12FFFFFF),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.line),
      ),
      child: Row(
        children: [
          Container(
            width: 42,
            height: 42,
            decoration: BoxDecoration(
              color: AppTheme.primary.withOpacity(0.15),
              borderRadius: BorderRadius.circular(12),
            ),
            alignment: Alignment.center,
            child: Text(task.icon, style: const TextStyle(fontSize: 22)),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(task.title, style: const TextStyle(color: AppTheme.text, fontSize: 14, fontWeight: FontWeight.w500)),
                const SizedBox(height: 3),
                Text(task.description, style: const TextStyle(color: AppTheme.muted, fontSize: 12)),
              ],
            ),
          ),
          const SizedBox(width: 8),
          if (task.isCompleted)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: AppTheme.online.withOpacity(0.3),
                borderRadius: BorderRadius.circular(17),
              ),
              child: const Icon(Icons.check, color: AppTheme.online, size: 16),
            )
          else
            GestureDetector(
              onTap: onComplete,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: AppTheme.primary.withOpacity(0.55),
                  borderRadius: BorderRadius.circular(17),
                ),
                child: Text('+${task.rewardCoins}', style: const TextStyle(color: Colors.white, fontSize: 12)),
              ),
            ),
        ],
      ),
    );
  }
}
