import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../utils/theme.dart';
import '../../models/growth.dart';
import '../../services/api_services.dart';

/// 成长页面 — 显示亲密度和里程碑
class GrowthScreen extends ConsumerStatefulWidget {
  const GrowthScreen({super.key});

  @override
  ConsumerState<GrowthScreen> createState() => _GrowthScreenState();
}

class _GrowthScreenState extends ConsumerState<GrowthScreen> {
  bool _isLoading = true;
  String? _error;
  GrowthSummary? _summary;
  List<GrowthMilestone> _milestones = [];

  @override
  void initState() {
    super.initState();
    _loadGrowthData();
  }

  Future<void> _loadGrowthData() async {
    try {
      setState(() {
        _isLoading = true;
        _error = null;
      });

      final growthService = ref.read(growthServiceProvider);
      final summary = await growthService.getGrowthSummary();
      final milestones = await growthService.getMilestones();

      setState(() {
        _summary = summary;
        _milestones = milestones;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
        _error = '加载失败: $e';
      });
      _loadDefaultData();
    }
  }

  void _loadDefaultData() {
    setState(() {
      _summary = GrowthSummary(
        intimacyLevel: 6,
        intimacyPoints: 450,
        intimacyForNext: 50,
        totalMessages: 128,
        milestonesCount: 3,
        activeDays: 15,
      );
      _milestones = [
        GrowthMilestone(
          id: 1,
          title: '初次相遇',
          description: '与晚星完成了第一次对话',
          achievedAt: DateTime.now().subtract(const Duration(days: 14)),
        ),
        GrowthMilestone(
          id: 2,
          title: '深夜倾听者',
          description: '在深夜与晚星分享心事',
          achievedAt: DateTime.now().subtract(const Duration(days: 7)),
        ),
        GrowthMilestone(
          id: 3,
          title: '心有灵犀',
          description: '连续聊天超过10天',
          achievedAt: DateTime.now().subtract(const Duration(days: 3)),
        ),
      ];
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: const Text('我们的成长'),
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
        onRefresh: _loadGrowthData,
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
                        child: Text(_error!, style: TextStyle(color: AppTheme.danger, fontSize: 12)),
                      ),
                      TextButton(
                        onPressed: _loadGrowthData,
                        child: const Text('重试', style: TextStyle(fontSize: 12)),
                      ),
                    ],
                  ),
                ),
              // 亲密度卡片
              _IntimacyCard(summary: _summary),
              const SizedBox(height: 20),
              // 统计概览
              _StatsOverview(summary: _summary),
              const SizedBox(height: 20),
              // 里程碑
              const Text('里程碑', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: AppTheme.text)),
              const SizedBox(height: 12),
              if (_milestones.isEmpty)
                Center(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(vertical: 32),
                    child: Column(
                      children: [
                        Icon(Icons.emoji_events_outlined, size: 48, color: AppTheme.soft.withOpacity(0.5)),
                        const SizedBox(height: 16),
                        Text('还没有里程碑', style: TextStyle(color: AppTheme.muted, fontSize: 14)),
                        const SizedBox(height: 8),
                        Text('继续与晚星互动，解锁更多成就', style: TextStyle(color: AppTheme.soft, fontSize: 12)),
                      ],
                    ),
                  ),
                )
              else
                ..._milestones.map((m) => _MilestoneCard(milestone: m)),
            ],
          ),
        ),
      ),
    );
  }
}

class _IntimacyCard extends StatelessWidget {
  final GrowthSummary? summary;
  const _IntimacyCard({this.summary});

  @override
  Widget build(BuildContext context) {
    final level = summary?.intimacyLevel ?? 1;
    final points = summary?.intimacyPoints ?? 0;
    final forNext = summary?.intimacyForNext ?? 100;
    final progress = 1 - (forNext / 100);

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment(-1, -0.5),
          end: Alignment(1, 0.5),
          colors: [Color(0x995E6AD3), Color(0xCC2A2254)],
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppTheme.line),
      ),
      child: Column(
        children: [
          Row(
            children: [
              // 伴侣头像
              Container(
                width: 64,
                height: 64,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(color: AppTheme.primary.withOpacity(0.5), width: 2),
                  boxShadow: [
                    BoxShadow(color: AppTheme.primary.withOpacity(0.3), blurRadius: 20),
                  ],
                ),
                alignment: Alignment.center,
                child: const Text('🌙', style: TextStyle(fontSize: 32)),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Lv.$level',
                      style: const TextStyle(
                        fontSize: 28,
                        fontWeight: FontWeight.w800,
                        color: AppTheme.text,
                      ),
                    ),
                    Text(
                      '$points 亲密度',
                      style: TextStyle(fontSize: 14, color: AppTheme.muted),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          // 进度条
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('距离 Lv.${level + 1}', style: TextStyle(color: AppTheme.muted, fontSize: 12)),
                  Text('$forNext 点', style: TextStyle(color: AppTheme.primary, fontSize: 12)),
                ],
              ),
              const SizedBox(height: 6),
              ClipRRect(
                borderRadius: BorderRadius.circular(4),
                child: LinearProgressIndicator(
                  value: progress,
                  backgroundColor: AppTheme.line,
                  valueColor: const AlwaysStoppedAnimation<Color>(AppTheme.primary),
                  minHeight: 8,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _StatsOverview extends StatelessWidget {
  final GrowthSummary? summary;
  const _StatsOverview({this.summary});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: _StatCard(
            icon: '💬',
            value: '${summary?.totalMessages ?? 0}',
            label: '对话',
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _StatCard(
            icon: '🏆',
            value: '${summary?.milestonesCount ?? 0}',
            label: '成就',
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _StatCard(
            icon: '📅',
            value: '${summary?.activeDays ?? 0}',
            label: '活跃天',
          ),
        ),
      ],
    );
  }
}

class _StatCard extends StatelessWidget {
  final String icon;
  final String value;
  final String label;
  const _StatCard({required this.icon, required this.value, required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 12),
      decoration: BoxDecoration(
        color: const Color(0x14FFFFFF),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.line),
      ),
      child: Column(
        children: [
          Text(icon, style: const TextStyle(fontSize: 24)),
          const SizedBox(height: 6),
          Text(
            value,
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: AppTheme.text),
          ),
          const SizedBox(height: 2),
          Text(label, style: TextStyle(fontSize: 12, color: AppTheme.muted)),
        ],
      ),
    );
  }
}

class _MilestoneCard extends StatelessWidget {
  final GrowthMilestone milestone;
  const _MilestoneCard({required this.milestone});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0x14FFFFFF),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.line),
      ),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: AppTheme.accent.withOpacity(0.15),
              borderRadius: BorderRadius.circular(12),
            ),
            alignment: Alignment.center,
            child: const Icon(Icons.emoji_events, color: AppTheme.accent, size: 24),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  milestone.title,
                  style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: AppTheme.text),
                ),
                if (milestone.description != null)
                  Text(
                    milestone.description!,
                    style: TextStyle(fontSize: 12, color: AppTheme.muted),
                  ),
              ],
            ),
          ),
          Text(
            _fmtDate(milestone.achievedAt),
            style: TextStyle(fontSize: 11, color: AppTheme.soft),
          ),
        ],
      ),
    );
  }

  String _fmtDate(DateTime t) {
    return '${t.month}/${t.day}';
  }
}
