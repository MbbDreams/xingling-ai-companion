import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../utils/theme.dart';
import '../../models/user.dart';
import '../../models/shop.dart';
import '../../services/api_services.dart';
import '../../providers/auth_provider.dart';
import '../../services/secure_storage.dart';
import '../auth/login_page.dart';
import 'edit_profile_page.dart';

/// 个人中心页面 — 匹配原型深色宇宙风格
class ProfileScreen extends ConsumerStatefulWidget {
  const ProfileScreen({super.key});

  @override
  ConsumerState<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends ConsumerState<ProfileScreen> {
  bool _isLoading = true;
  String? _error;
  UserProfile? _user;
  Companion? _companion;
  int _coins = 0;

  @override
  void initState() {
    super.initState();
    _loadProfile();
    _loadBalance();
  }

  Future<void> _loadProfile() async {
    try {
      setState(() {
        _isLoading = true;
        _error = null;
      });

      final userService = ref.read(userServiceProvider);
      final profile = await userService.getProfile();

      setState(() {
        _user = profile.user;
        _companion = profile.companion;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
        _error = '加载资料失败: $e';
      });
      _loadDefaultProfile();
    }
  }

  Future<void> _loadBalance() async {
    try {
      final shopService = ref.read(shopServiceProvider);
      final balance = await shopService.getBalance();
      setState(() {
        _coins = balance;
      });
    } catch (e) {
      // 使用默认余额
      setState(() {
        _coins = 100;
      });
    }
  }

  void _loadDefaultProfile() {
    setState(() {
      _user = UserProfile(
        userId: 1,
        username: 'Lee',
        isVip: false,
        createdAt: DateTime(2024),
      );
      _companion = Companion(
        companionId: 1,
        name: '晚星',
        intimacyLevel: 6,
        intimacyPoints: 450,
      );
    });
  }

  Future<void> _updateProfile({String? nickname, String? avatar}) async {
    try {
      final userService = ref.read(userServiceProvider);
      final updatedUser = await userService.updateProfile(
        nickname: nickname,
        avatar: avatar,
      );
      setState(() {
        _user = updatedUser;
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('资料已更新'), backgroundColor: AppTheme.primary),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('更新失败: $e'), backgroundColor: AppTheme.danger),
        );
      }
    }
  }

  /// 跳转到编辑资料页面
  void _navigateToEditProfile() {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => const EditProfilePage(),
      ),
    ).then((_) {
      // 返回后刷新资料
      _loadProfile();
    });
  }

  /// 退出登录
  Future<void> _logout() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF0A0F24),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text('退出登录', style: TextStyle(color: AppTheme.text)),
        content: const Text(
          '确定要退出登录吗？',
          style: TextStyle(color: AppTheme.muted),
        ),
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
      // 调用退出登录
      await ref.read(authProvider.notifier).logout();
      
      // 清除本地存储
      await SecureStorage.clearAll();
      
      // 跳转到登录页面
      if (mounted) {
        Navigator.of(context).pushAndRemoveUntil(
          MaterialPageRoute(builder: (context) => const LoginPage()),
          (route) => false,
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: RefreshIndicator(
        onRefresh: () async {
          await _loadProfile();
          await _loadBalance();
        },
        color: AppTheme.primary,
        backgroundColor: const Color(0xFF0A0F24),
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(18, 50, 18, 100),
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
                        onPressed: _loadProfile,
                        child: const Text('重试', style: TextStyle(fontSize: 12)),
                      ),
                    ],
                  ),
                ),
              // 用户信息
              _ProfileCard(
                user: _user,
                companion: _companion,
                coins: _coins,
                isLoading: _isLoading,
                onEdit: _navigateToEditProfile,
              ),
              const SizedBox(height: 16),
              // Pro 卡片
              _ProCard(isVip: _user?.isVip ?? false),
              const SizedBox(height: 16),
              // 设置列表
              ..._settings.map((s) => _SettingRow(icon: s.icon, title: s.title, trailing: s.trailing)),
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
      ),
    );
  }
}

class _ProfileCard extends StatelessWidget {
  final UserProfile? user;
  final Companion? companion;
  final int coins;
  final bool isLoading;
  final VoidCallback onEdit;

  const _ProfileCard({
    this.user,
    this.companion,
    required this.coins,
    required this.isLoading,
    required this.onEdit,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: AppTheme.panelDecoration,
      child: Column(
        children: [
          Row(
            children: [
              // 头像
              Container(
                width: 58,
                height: 58,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(color: AppTheme.primary.withOpacity(0.5), width: 2),
                  boxShadow: [
                    BoxShadow(color: AppTheme.primary.withOpacity(0.3), blurRadius: 20),
                  ],
                ),
                alignment: Alignment.center,
                child: const Text('🌙', style: TextStyle(fontSize: 28)),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (isLoading)
                      const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          valueColor: AlwaysStoppedAnimation<Color>(AppTheme.primary),
                        ),
                      )
                    else ...[
                      Text(
                        user?.username ?? '用户',
                        style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: AppTheme.text),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Lv.${companion?.intimacyLevel ?? 1} · ${companion?.name ?? '晚星'}',
                        style: TextStyle(fontSize: 13, color: AppTheme.muted),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        '加入于 ${user?.createdAt.year ?? 2024}',
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
                  '$coins 星币',
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
                Text(
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
  const _SettingRow({required this.icon, required this.title, required this.trailing});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () {},
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
            Text(trailing, style: const TextStyle(color: AppTheme.soft, fontSize: 13)),
            const SizedBox(width: 8),
            const Icon(Icons.chevron_right, color: AppTheme.soft, size: 18),
          ],
        ),
      ),
    );
  }
}

class _SettingItem {
  final IconData icon;
  final String title;
  final String trailing;
  const _SettingItem(this.icon, this.title, this.trailing);
}

const _settings = [
  _SettingItem(Icons.shield_outlined, '账户与安全', ''),
  _SettingItem(Icons.notifications_outlined, '通知设置', ''),
  _SettingItem(Icons.lock_outline, '隐私设置', ''),
  _SettingItem(Icons.language, '语言', '中文'),
  _SettingItem(Icons.help_outline, '帮助与反馈', ''),
  _SettingItem(Icons.info_outline, '关于星灵', ''),
];
