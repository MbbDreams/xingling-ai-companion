import 'dart:ui' as ui;
import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'chat/chat_screen.dart';
import 'memory/memory_screen.dart';
import 'diary/diary_screen.dart';
import 'growth/growth_screen.dart';
import 'discover/discover_screen.dart';
import 'profile/profile_screen.dart';
import '../utils/theme.dart';

/// 主页面 — 底部 6 Tab 导航（匹配原型 .bottom-nav）
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with TickerProviderStateMixin {
  int _currentIndex = 0;
  late AnimationController _navController;
  late List<AnimationController> _tabControllers;

  final List<Widget> _screens = const [
    ChatScreen(),
    MemoryScreen(),
    DiaryScreen(),
    GrowthScreen(),
    DiscoverScreen(),
    ProfileScreen(),
  ];

  /// 底部导航栏高度（含 SafeArea）
  static const double _bottomNavHeight = 80;

  @override
  void initState() {
    super.initState();
    _navController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );
    _tabControllers = List.generate(
      6,
      (index) => AnimationController(
        duration: const Duration(milliseconds: 400),
        vsync: this,
      ),
    );
    _tabControllers[0].forward();
  }

  @override
  void dispose() {
    _navController.dispose();
    for (var c in _tabControllers) {
      c.dispose();
    }
    super.dispose();
  }

  void _onTabChanged(int index) {
    if (_currentIndex == index) return;
    
    // 退出动画
    _tabControllers[_currentIndex].reverse();
    
    setState(() {
      _currentIndex = index;
    });
    
    // 进入动画
    _tabControllers[index].forward();
    
    // 导航栏动画
    _navController.forward(from: 0);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment(-0.4, -1.2),
            end: Alignment(0.8, 1.0),
            colors: [
              Color(0xFF030817),
              Color(0xFF091329),
              Color(0xFF0D1026),
            ],
          ),
        ),
        child: Stack(
          children: [
            // 动态星空背景
            const Positioned.fill(
              child: AnimatedStarField(),
            ),
            // 页面内容 - 使用 FadeTransition 实现平滑切换
            AnimatedBuilder(
              animation: _tabControllers[_currentIndex],
              builder: (context, child) {
                return FadeTransition(
                  opacity: CurvedAnimation(
                    parent: _tabControllers[_currentIndex],
                    curve: Curves.easeInOut,
                  ),
                  child: SlideTransition(
                    position: Tween<Offset>(
                      begin: const Offset(0.05, 0),
                      end: Offset.zero,
                    ).animate(CurvedAnimation(
                      parent: _tabControllers[_currentIndex],
                      curve: Curves.easeOutCubic,
                    )),
                    child: Padding(
                      // 为所有子页面预留底部导航栏空间
                      padding: const EdgeInsets.only(bottom: _bottomNavHeight),
                      child: _screens[_currentIndex],
                    ),
                  ),
                );
              },
            ),
          ],
        ),
      ),
      // 使用 extendBody: false，自定义导航栏
      extendBody: false,
      bottomNavigationBar: _buildBottomNav(),
    );
  }

  Widget _buildBottomNav() {
    return Container(
      margin: const EdgeInsets.fromLTRB(12, 0, 12, 20),
      decoration: BoxDecoration(
        color: const Color(0xE6060C1F),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: AppTheme.line),
        boxShadow: [
          BoxShadow(
            color: AppTheme.primary.withOpacity(0.1),
            blurRadius: 20,
            spreadRadius: 2,
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(24),
        child: BackdropFilter(
          filter: ui.ImageFilter.blur(sigmaX: 16, sigmaY: 16),
          child: SafeArea(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 6),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  _buildNavItem(Icons.chat_bubble_outline, Icons.chat_bubble, '聊天', 0),
                  _buildNavItem(Icons.auto_awesome_outlined, Icons.auto_awesome, '记忆', 1),
                  _buildNavItem(Icons.book_outlined, Icons.book, '日记', 2),
                  _buildNavItem(Icons.trending_up_outlined, Icons.trending_up, '成长', 3),
                  _buildNavItem(Icons.explore_outlined, Icons.explore, '发现', 4),
                  _buildNavItem(Icons.person_outline, Icons.person, '我的', 5),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildNavItem(IconData icon, IconData activeIcon, String label, int index) {
    final isSelected = _currentIndex == index;
    
    return GestureDetector(
      onTap: () => _onTabChanged(index),
      behavior: HitTestBehavior.opaque,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 250),
        curve: Curves.easeOutCubic,
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        decoration: BoxDecoration(
          color: isSelected 
              ? AppTheme.primary.withOpacity(0.15) 
              : Colors.transparent,
          borderRadius: BorderRadius.circular(16),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            AnimatedSwitcher(
              duration: const Duration(milliseconds: 200),
              transitionBuilder: (child, animation) {
                return ScaleTransition(
                  scale: animation,
                  child: child,
                );
              },
              child: Icon(
                isSelected ? activeIcon : icon,
                key: ValueKey(isSelected),
                color: isSelected ? AppTheme.activeNav : AppTheme.soft,
                size: isSelected ? 22 : 20,
              ),
            ),
            const SizedBox(height: 3),
            AnimatedDefaultTextStyle(
              duration: const Duration(milliseconds: 200),
              style: TextStyle(
                color: isSelected ? AppTheme.activeNav : AppTheme.soft,
                fontSize: 10,
                fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
              ),
              child: Text(label),
            ),
          ],
        ),
      ),
    );
  }
}

/// 动态星空背景 - 带呼吸效果
class AnimatedStarField extends StatefulWidget {
  const AnimatedStarField({super.key});

  @override
  State<AnimatedStarField> createState() => _AnimatedStarFieldState();
}

class _AnimatedStarFieldState extends State<AnimatedStarField> 
    with TickerProviderStateMixin {
  late AnimationController _breathController;
  late AnimationController _twinkleController;

  @override
  void initState() {
    super.initState();
    _breathController = AnimationController(
      duration: const Duration(seconds: 4),
      vsync: this,
    )..repeat(reverse: true);
    
    _twinkleController = AnimationController(
      duration: const Duration(seconds: 2),
      vsync: this,
    )..repeat();
  }

  @override
  void dispose() {
    _breathController.dispose();
    _twinkleController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: Listenable.merge([_breathController, _twinkleController]),
      builder: (context, child) {
        return CustomPaint(
          painter: _BreathingStarPainter(
            breathValue: _breathController.value,
            twinkleValue: _twinkleController.value,
          ),
          size: Size.infinite,
        );
      },
    );
  }
}

class _BreathingStarPainter extends CustomPainter {
  final double breathValue;
  final double twinkleValue;

  _BreathingStarPainter({required this.breathValue, required this.twinkleValue});

  @override
  void paint(Canvas canvas, Size size) {
    final breathOpacity = 0.3 + (breathValue * 0.2);
    
    // 主光晕 - 左上
    final r1 = Paint()
      ..shader = RadialGradient(
        center: const Alignment(0.2, 0.12),
        radius: 0.45 + (breathValue * 0.05),
        colors: [
          Color(0x5C5D48AA).withOpacity(breathOpacity),
          Colors.transparent,
        ],
      ).createShader(Rect.fromLTWH(0, 0, size.width, size.height));
    canvas.drawRect(Rect.fromLTWH(0, 0, size.width, size.height), r1);

    // 次光晕 - 右上
    final r2 = Paint()
      ..shader = RadialGradient(
        center: const Alignment(0.82, 0.22),
        radius: 0.42 + ((1 - breathValue) * 0.05),
        colors: [
          Color(0x381F5B98).withOpacity(breathOpacity * 0.7),
          Colors.transparent,
        ],
      ).createShader(Rect.fromLTWH(0, 0, size.width, size.height));
    canvas.drawRect(Rect.fromLTWH(0, 0, size.width, size.height), r2);

    // 闪烁的星星
    final rng = DateTime.now().millisecond;
    for (int i = 0; i < 80; i++) {
      final x = ((i * 137 + rng) % 1000) / 1000 * size.width;
      final y = ((i * 251 + rng * 2) % 1000) / 1000 * size.height;
      final baseR = ((i * 73) % 3).toDouble() + 0.5;
      
      final twinkle = math.sin((twinkleValue * math.pi * 2) + (i * 0.5)) * 0.5 + 0.5;
      final r = baseR * (0.7 + twinkle * 0.6);
      final opacity = 0.15 + twinkle * 0.25;
      
      final dotPaint = Paint()
        ..color = Colors.white.withOpacity(opacity)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 0.5);
      
      canvas.drawCircle(Offset(x, y), r, dotPaint);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
