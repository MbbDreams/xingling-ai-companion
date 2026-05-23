import 'package:flutter/material.dart';

import '../../../utils/theme.dart';

/// 关于星灵页面
class AboutPage extends StatelessWidget {
  const AboutPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF030817),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: const Text('关于星灵', style: TextStyle(color: AppTheme.text, fontSize: 18)),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios, color: AppTheme.muted, size: 20),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            const SizedBox(height: 20),
            // Logo
            Container(
              width: 100,
              height: 100,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: const LinearGradient(colors: [Color(0xFF8F73FF), Color(0xFF5E6AD3)]),
                boxShadow: [
                  BoxShadow(color: const Color(0xFF8F73FF).withOpacity(0.4), blurRadius: 40),
                ],
              ),
              alignment: Alignment.center,
              child: const Text('🌙', style: TextStyle(fontSize: 50)),
            ),
            const SizedBox(height: 20),
            const Text('星灵 AI 伴侣', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w800, color: AppTheme.text)),
            const SizedBox(height: 4),
            const Text('Version 1.0.0', style: TextStyle(fontSize: 14, color: AppTheme.muted)),
            const SizedBox(height: 8),
            const Text('你的 AI 灵魂伴侣', style: TextStyle(fontSize: 16, color: AppTheme.primary)),
            const SizedBox(height: 40),
            // 功能介绍
            _InfoCard(
              icon: '💬',
              title: '智能对话',
              description: '基于大语言模型的自然对话，理解你的情感和需求',
            ),
            const SizedBox(height: 12),
            _InfoCard(
              icon: '🧠',
              title: '记忆系统',
              description: '记住你们之间的每一个重要时刻',
            ),
            const SizedBox(height: 12),
            _InfoCard(
              icon: '📖',
              title: '成长日记',
              description: '记录你的心情变化，AI 陪伴你成长',
            ),
            const SizedBox(height: 12),
            _InfoCard(
              icon: '🎨',
              title: '个性定制',
              description: '自定义伴侣外观、场景和语音',
            ),
            const SizedBox(height: 40),
            const Divider(color: AppTheme.line),
            const SizedBox(height: 16),
            _LinkItem(title: '用户协议', onTap: () {}),
            _LinkItem(title: '隐私政策', onTap: () {}),
            _LinkItem(title: '开源许可', onTap: () {}),
            const SizedBox(height: 24),
            const Text(
              '© 2024 星灵 AI 团队',
              style: TextStyle(color: AppTheme.soft, fontSize: 12),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}

class _InfoCard extends StatelessWidget {
  final String icon;
  final String title;
  final String description;

  const _InfoCard({required this.icon, required this.title, required this.description});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: AppTheme.panelDecoration,
      child: Row(
        children: [
          Text(icon, style: const TextStyle(fontSize: 28)),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: AppTheme.text)),
                const SizedBox(height: 4),
                Text(description, style: const TextStyle(fontSize: 13, color: AppTheme.muted)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _LinkItem extends StatelessWidget {
  final String title;
  final VoidCallback onTap;

  const _LinkItem({required this.title, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 14),
        decoration: const BoxDecoration(
          border: Border(bottom: BorderSide(color: AppTheme.line, width: 0.5)),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(title, style: const TextStyle(color: AppTheme.text, fontSize: 15)),
            const Icon(Icons.chevron_right, color: AppTheme.soft, size: 18),
          ],
        ),
      ),
    );
  }
}
