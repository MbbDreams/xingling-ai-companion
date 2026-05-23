import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../utils/theme.dart';
import '../../providers/auth_provider.dart';
import '../../services/secure_storage.dart';
import '../auth/login_page.dart';
import 'edit_profile_page.dart';
import 'settings/change_password_page.dart';
import 'settings/about_page.dart';

/// 个人中心页面 — 使用 authProvider 统一数据源
class ProfileScreen extends ConsumerStatefulWidget {
  const ProfileScreen({super.key});

  @override
  ConsumerState<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends ConsumerState<ProfileScreen> {
  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authProvider);
    final user = authState.user;

    return Scaffold(
      backgroundColor: Colors.transparent,
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(18, 50, 18, 100),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 用户信息卡片
            _ProfileCard(user: user, onEdit: _navigateToEditProfile),
            const SizedBox(height: 16),
            // 账户统计卡片
            _StatsCard(),
            const SizedBox(height: 16),
            // Pro 卡片
            _ProCard(isVip: user?.isVip ?? false),
            const SizedBox(height: 16),
            // 设置列表
            ..._buildSettings(context),
            const SizedBox(height: 24),
            // 退出按钮
            Center(
              child: GestureDetector(
                onTap: _logout,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 12),
                  decoration: BoxDecoration(
                    color: AppTheme.danger.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(24),
                    border: Border.all(color: AppTheme.danger.withOpacity(0.3)),
                  ),
                  child: const Text('退出登录', style: TextStyle(color: AppTheme.danger, fontSize: 14)),
                ),
              ),
            ),
            const SizedBox(height: 16),
            const Center(
              child: Text('Version 1.0.0', style: TextStyle(color: AppTheme.soft, fontSize: 12)),
            ),
          ],
        ),
      ),
    );
  }

  List<Widget> _buildSettings(BuildContext context) {
    return [
      _SettingRow(
        icon: Icons.shield_outlined,
        title: '账户与安全',
        trailing: '',
        onTap: () => _navigateTo(context, const ChangePasswordPage()),
      ),
      _SettingRow(
        icon: Icons.notifications_outlined,
        title: '通知设置',
        trailing: '',
        onTap: () => _showComingSoon('通知设置'),
      ),
      _SettingRow(
        icon: Icons.lock_outline,
        title: '隐私设置',
        trailing: '',
        onTap: () => _showComingSoon('隐私设置'),
      ),
      _SettingRow(
        icon: Icons.language,
        title: '语言',
        trailing: '中文',
        onTap: () => _showComingSoon('语言切换'),
      ),
      _SettingRow(
        icon: Icons.help_outline,
        title: '帮助与反馈',
        trailing: '',
        onTap: () => _showComingSoon('帮助与反馈'),
      ),
      _SettingRow(
        icon: Icons.info_outline,
        title: '关于星灵',
        trailing: '',
        onTap: () => _navigateTo(context, const AboutPage()),
      ),
    ];
  }

  void _navigateToEditProfile() {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => const EditProfilePage()),
    ).then((_) {
      // 返回后刷新用户信息
      ref.read(authProvider.notifier).refreshUser();
    });
  }

  void _navigateTo(BuildContext context, Widget page) {
    Navigator.push(context, MaterialPageRoute(builder: (context) => page));
  }

  void _showComingSoon(String feature) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('$feature 即将上线 ✨'),
        backgroundColor: AppTheme.primary,
        duration: const Duration(seconds: 2),
      ),
    );
  }

  Future<void> _logout() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF0A0F24),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text('退出登录', style: TextStyle(color: AppTheme.text)),
        content: const Text('确定要退出登录吗？', style: TextStyle(color: AppTheme.muted)),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('取消', style: TextStyle(color: AppTheme.muted)),
          ),
          Container(
            decoration: BoxDecoration(
              color: AppTheme.danger.withOpacity(0.2),
              borderRadius: BorderRadius.circular(12),
            ),
            child: TextButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: const Text('退出', style: TextStyle(color: AppTheme.danger)),
            ),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      await ref.read(authProvider.notifier).logout();
      await SecureStorage.clearAll();
      if (mounted) {
        Navigator.of(context).pushAndRemoveUntil(
          MaterialPageRoute(builder: (context) => const LoginPage()),
          (route) => false,
        );
      }
    }
  }
}

class _ProfileCard extends StatelessWidget {
  final dynamic user;
  final VoidCallback onEdit;

  const _ProfileCard({required this.user, required this.onEdit});

  @override
  Widget build(BuildContext context) {
    final nickname = user?.nickname ?? '用户';
    final avatar = user?.avatar;
    final phone = user?.phone ?? '';
    final bio = user?.bio ?? '';

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: AppTheme.panelDecoration,
      child: Column(
        children: [
          Row(
            children: [
              // 头像
              GestureDetector(
                onTap: onEdit,
                child: Container(
                  width: 58,
                  height: 58,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(color: AppTheme.primary.withOpacity(0.5), width: 2),
                    boxShadow: [
                      BoxShadow(color: AppTheme.primary.withOpacity(0.3), blurRadius: 20),
                    ],
                    image: avatar != null && avatar.isNotEmpty
                        ? DecorationImage(image: NetworkImage(avatar), fit: BoxFit.cover)
                        : null,
                  ),
                  alignment: Alignment.center,
                  child: avatar == null || avatar.isEmpty
                      ? const Text('🌙', style: TextStyle(fontSize: 28))
                      : null,
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      nickname,
                      style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: AppTheme.text),
                    ),
                    if (phone.isNotEmpty) ...[
                      const SizedBox(height: 4),
                      Text(
                        phone,
                        style: TextStyle(fontSize: 13, color: AppTheme.muted),
                      ),
                    ],
                    if (bio.isNotEmpty) ...[
                      const SizedBox(height: 2),
                      Text(
                        bio.length > 30 ? '${bio.substring(0, 30)}...' : bio,
                        style: TextStyle(fontSize: 12, color: AppTheme.soft),
                      ),
                    ],
                  ],
                ),
              ),
              GestureDetector(
                onTap: onEdit,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                  decoration: BoxDecoration(
                    color: const Color(0x14FFFFFF),
                    borderRadius: BorderRadius.circular(17),
                    border: Border.all(color: AppTheme.line),
                  ),
                  child: const Text('编辑', style: TextStyle(color: AppTheme.muted, fontSize: 13)),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          // 星币显示
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            decoration: BoxDecoration(
              color: const Color(0x14FFFFFF),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppTheme.line),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text('⭐', style: TextStyle(fontSize: 16)),
                const SizedBox(width: 6),
                Text(
                  '${user?.coins ?? 0} 星币',
                  style: const TextStyle(color: AppTheme.text, fontSize: 14, fontWeight: FontWeight.w500),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _StatsCard extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: AppTheme.panelDecoration,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _StatItem(label: '亲密度', value: 'Lv.6', icon: '💜'),
          _StatItem(label: '记忆', value: '12', icon: '🧠'),
          _StatItem(label: '日记', value: '5', icon: '📖'),
        ],
      ),
    );
  }
}

class _StatItem extends StatelessWidget {
  final String label;
  final String value;
  final String icon;

  const _StatItem({required this.label, required this.value, required this.icon});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(icon, style: const TextStyle(fontSize: 20)),
        const SizedBox(height: 4),
        Text(value, style: const TextStyle(color: AppTheme.text, fontSize: 16, fontWeight: FontWeight.w700)),
        const SizedBox(height: 2),
        Text(label, style: const TextStyle(color: AppTheme.muted, fontSize: 12)),
      ],
    );
  }
}

class _ProCard extends StatelessWidget {
  final bool isVip;

  const _ProCard({required this.isVip});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment(-1, -0.5),
          end: Alignment(1, 0.5),
          colors: [Color(0xB87552D6), Color(0xCC232952)],
        ),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppTheme.line),
      ),
      child: Row(
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              color: AppTheme.accent.withOpacity(0.12),
              borderRadius: BorderRadius.circular(14),
            ),
            alignment: Alignment.center,
            child: const Icon(Icons.auto_awesome, color: AppTheme.accent, size: 28),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  isVip ? '星灵 Pro (已开通)' : '星灵 Pro',
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: AppTheme.text),
                ),
                const SizedBox(height: 3),
                const Text(
                  '解锁全部服装、场景和语音包',
                  style: TextStyle(fontSize: 12, color: AppTheme.muted),
                ),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
            decoration: AppTheme.primaryButtonDecoration,
            child: Text(
              isVip ? '管理' : '开通',
              style: const TextStyle(color: Colors.white, fontSize: 13),
            ),
          ),
        ],
      ),
    );
  }
}

class _SettingRow extends StatelessWidget {
  final IconData icon;
  final String title;
  final String trailing;
  final VoidCallback onTap;

  const _SettingRow({
    required this.icon,
    required this.title,
    required this.trailing,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 2),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
        height: 52,
        decoration: BoxDecoration(
          color: const Color(0x14FFFFFF),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AppTheme.line),
        ),
        child: Row(
          children: [
            Icon(icon, color: AppTheme.muted, size: 22),
            const SizedBox(width: 12),
            Expanded(child: Text(title, style: const TextStyle(color: AppTheme.text, fontSize: 14))),
            if (trailing.isNotEmpty)
              Text(trailing, style: const TextStyle(color: AppTheme.soft, fontSize: 13)),
            const SizedBox(width: 8),
            const Icon(Icons.chevron_right, color: AppTheme.soft, size: 18),
          ],
        ),
      ),
    );
  }
}
