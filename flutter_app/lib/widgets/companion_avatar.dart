import 'dart:math' as math;
import 'package:flutter/material.dart';

import '../../utils/theme.dart';

/// Live2D 风格的伴侣形象组件
/// 欧美风格，支持多种情绪表情和呼吸动画
class CompanionAvatar extends StatefulWidget {
  final double size;
  final String? emotion;
  final bool showGlow;
  final bool animate;

  const CompanionAvatar({
    super.key,
    this.size = 120,
    this.emotion,
    this.showGlow = true,
    this.animate = true,
  });

  @override
  State<CompanionAvatar> createState() => _CompanionAvatarState();
}

class _CompanionAvatarState extends State<CompanionAvatar>
    with TickerProviderStateMixin {
  late AnimationController _breathController;
  late AnimationController _blinkController;
  late AnimationController _swayController;

  @override
  void initState() {
    super.initState();
    _breathController = AnimationController(
      duration: const Duration(milliseconds: 3000),
      vsync: this,
    )..repeat(reverse: true);

    _blinkController = AnimationController(
      duration: const Duration(milliseconds: 150),
      vsync: this,
    );

    _swayController = AnimationController(
      duration: const Duration(milliseconds: 4000),
      vsync: this,
    )..repeat(reverse: true);

    // 随机眨眼
    _startBlinking();
  }

  void _startBlinking() async {
    while (mounted) {
      await Future.delayed(
        Duration(seconds: 2 + math.Random().nextInt(4)),
      );
      if (mounted) {
        await _blinkController.forward();
        await Future.delayed(const Duration(milliseconds: 100));
        if (mounted) {
          await _blinkController.reverse();
        }
      }
    }
  }

  @override
  void dispose() {
    _breathController.dispose();
    _blinkController.dispose();
    _swayController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: Listenable.merge([
        if (widget.animate) _breathController,
        if (widget.animate) _swayController,
        _blinkController,
      ]),
      builder: (context, child) {
        final breathScale = widget.animate
            ? 1.0 + _breathController.value * 0.015
            : 1.0;
        final swayAngle = widget.animate
            ? math.sin(_swayController.value * math.pi * 2) * 0.02
            : 0.0;
        final blinkValue = _blinkController.value;

        Widget content = Stack(
          alignment: Alignment.center,
          children: [
            // 外发光
            if (widget.showGlow)
              Positioned.fill(
                child: Container(
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: RadialGradient(
                      colors: [
                        AppTheme.primary.withOpacity(0.15),
                        AppTheme.primary.withOpacity(0.05),
                        Colors.transparent,
                      ],
                      stops: const [0.5, 0.75, 1.0],
                    ),
                  ),
                ),
              ),
            // 头部主体
            _buildHead(blinkValue),
            // 头发
            _buildHair(),
            // 眼睛
            _buildEyes(blinkValue),
            // 嘴巴（根据情绪变化）
            _buildMouth(),
            // 腮红
            _buildBlush(),
          ],
        );

        // 只在需要动画时应用 Transform
        if (widget.animate) {
          content = Transform(
            alignment: Alignment.center,
            transform: Matrix4.identity()
              ..scale(breathScale)
              ..rotateZ(swayAngle),
            child: content,
          );
        }

        return SizedBox(
          width: widget.size,
          height: widget.size,
          child: ClipOval(
            child: content,
          ),
        );
      },
    );
  }

  /// 头部
  Widget _buildHead(double blinkValue) {
    return Container(
      width: widget.size * 0.72,
      height: widget.size * 0.78,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: const LinearGradient(
          begin: Alignment(-0.3, -0.5),
          end: Alignment(0.5, 0.8),
          colors: [
            Color(0xFFFDE8D0), // 欧美肤色
            Color(0xFFF5D5B8),
            Color(0xFFEDCAA8),
          ],
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.15),
            blurRadius: 8,
            offset: const Offset(0, 3),
          ),
        ],
      ),
    );
  }

  /// 头发
  Widget _buildHair() {
    final s = widget.size;
    return Positioned(
      top: s * 0.02,
      left: s * 0.08,
      right: s * 0.08,
      height: s * 0.55,
      child: CustomPaint(
        size: Size(s * 0.84, s * 0.55),
        painter: _HairPainter(),
      ),
    );
  }

  /// 眼睛
  Widget _buildEyes(double blinkValue) {
    final s = widget.size;
    final eyeHeight = 6.0 * (1 - blinkValue);
    final eyeWidth = 8.0 + blinkValue * 2;

    return Positioned(
      top: s * 0.35,
      left: s * 0.18,
      right: s * 0.18,
      height: s * 0.15,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          _buildSingleEye(eyeWidth, eyeHeight, s),
          _buildSingleEye(eyeWidth, eyeHeight, s),
        ],
      ),
    );
  }

  Widget _buildSingleEye(double w, double h, double s) {
    return Container(
      width: w * 2.2,
      height: h * 3,
      alignment: Alignment.center,
      child: Container(
        width: w * 1.6,
        height: math.max(h * 0.5, 1),
        decoration: BoxDecoration(
          color: const Color(0xFF2C1810),
          borderRadius: BorderRadius.circular(h),
          boxShadow: [
            BoxShadow(
              color: const Color(0xFF6B4423).withOpacity(0.3),
              blurRadius: 3,
              spreadRadius: 0.5,
            ),
          ],
        ),
      ),
    );
  }

  /// 嘴巴
  Widget _buildMouth() {
    final s = widget.size;
    final emotion = widget.emotion ?? 'happy';

    return Positioned(
      top: s * 0.52,
      left: s * 0.32,
      right: s * 0.32,
      height: s * 0.12,
      child: CustomPaint(
        size: Size(s * 0.36, s * 0.12),
        painter: _MouthPainter(emotion: emotion),
      ),
    );
  }

  /// 腮红
  Widget _buildBlush() {
    final s = widget.size;
    return Positioned(
      top: s * 0.46,
      left: s * 0.12,
      right: s * 0.12,
      height: s * 0.04,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Container(
            width: s * 0.12,
            height: s * 0.04,
            decoration: BoxDecoration(
              color: const Color(0xFFFFB5B5).withOpacity(0.4),
              borderRadius: BorderRadius.circular(s * 0.02),
            ),
          ),
          Container(
            width: s * 0.12,
            height: s * 0.04,
            decoration: BoxDecoration(
              color: const Color(0xFFFFB5B5).withOpacity(0.4),
              borderRadius: BorderRadius.circular(s * 0.02),
            ),
          ),
        ],
      ),
    );
  }
}

/// 头发绘制器
class _HairPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = const Color(0xFF1A0A2E)
      ..style = PaintingStyle.fill;

    final path = Path();
    // 主头发轮廓 - 限制在边界内
    path.moveTo(0, size.height * 0.6);
    path.quadraticBezierTo(
      size.width * 0.1, size.height * 0.1,
      size.width * 0.5, 0,
    );
    path.quadraticBezierTo(
      size.width * 0.9, size.height * 0.1,
      size.width, size.height * 0.6,
    );
    // 右侧发丝 - 限制在边界内
    path.quadraticBezierTo(
      size.width * 0.98, size.height * 0.8,
      size.width * 0.92, size.height,
    );
    // 底部
    path.lineTo(size.width * 0.08, size.height);
    path.quadraticBezierTo(
      size.width * 0.02, size.height * 0.8,
      0, size.height * 0.6,
    );
    path.close();

    canvas.drawPath(path, paint);

    // 刘海
    final bangsPaint = Paint()
      ..color = const Color(0xFF231040)
      ..style = PaintingStyle.fill;

    final bangsPath = Path();
    bangsPath.moveTo(size.width * 0.1, size.height * 0.45);
    bangsPath.quadraticBezierTo(
      size.width * 0.3, size.height * 0.2,
      size.width * 0.5, size.height * 0.25,
    );
    bangsPath.quadraticBezierTo(
      size.width * 0.7, size.height * 0.2,
      size.width * 0.9, size.height * 0.45,
    );
    bangsPath.lineTo(size.width * 0.85, size.height * 0.5);
    bangsPath.quadraticBezierTo(
      size.width * 0.5, size.height * 0.35,
      size.width * 0.15, size.height * 0.5,
    );
    bangsPath.close();
    canvas.drawPath(bangsPath, bangsPaint);

    // 高光
    final highlightPaint = Paint()
      ..color = const Color(0xFF3D1F6D).withOpacity(0.3)
      ..style = PaintingStyle.fill;

    final highlightPath = Path();
    highlightPath.moveTo(size.width * 0.3, size.height * 0.15);
    highlightPath.quadraticBezierTo(
      size.width * 0.5, size.height * 0.05,
      size.width * 0.65, size.height * 0.2,
    );
    highlightPath.lineTo(size.width * 0.6, size.height * 0.25);
    highlightPath.quadraticBezierTo(
      size.width * 0.45, size.height * 0.15,
      size.width * 0.3, size.height * 0.2,
    );
    highlightPath.close();
    canvas.drawPath(highlightPath, highlightPaint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

/// 嘴巴绘制器
class _MouthPainter extends CustomPainter {
  final String emotion;

  _MouthPainter({required this.emotion});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = const Color(0xFFD4736A)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5
      ..strokeCap = StrokeCap.round;

    final center = Offset(size.width / 2, size.height * 0.3);
    final w = size.width * 0.35;

    final path = Path();

    switch (emotion) {
      case 'happy':
        path.moveTo(center.dx - w, center.dy);
        path.quadraticBezierTo(
          center.dx, center.dy + size.height * 0.6,
          center.dx + w, center.dy,
        );
        break;
      case 'sad':
        path.moveTo(center.dx - w, center.dy + size.height * 0.2);
        path.quadraticBezierTo(
          center.dx, center.dy - size.height * 0.3,
          center.dx + w, center.dy + size.height * 0.2,
        );
        break;
      case 'surprised':
        canvas.drawOval(
          Rect.fromCenter(
            center: center,
            width: w * 0.6,
            height: size.height * 0.5,
          ),
          paint..style = PaintingStyle.stroke,
        );
        return;
      case 'thinking':
        path.moveTo(center.dx - w * 0.5, center.dy);
        path.lineTo(center.dx + w * 0.3, center.dy - size.height * 0.1);
        break;
      case 'excited':
        path.moveTo(center.dx - w, center.dy);
        path.quadraticBezierTo(
          center.dx, center.dy + size.height * 0.8,
          center.dx + w, center.dy,
        );
        // 张嘴效果
        final fillPaint = Paint()
          ..color = const Color(0xFFD4736A).withOpacity(0.3)
          ..style = PaintingStyle.fill;
        canvas.drawPath(path, fillPaint);
        path.close();
        break;
      default: // calm / neutral
        path.moveTo(center.dx - w * 0.7, center.dy);
        path.quadraticBezierTo(
          center.dx, center.dy + size.height * 0.2,
          center.dx + w * 0.7, center.dy,
        );
    }

    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(covariant _MouthPainter oldDelegate) =>
      oldDelegate.emotion != emotion;
}

/// 聊天界面中的伴侣形象卡片（含情绪标签）
class CompanionCard extends StatelessWidget {
  final String? emotion;
  final String name;
  final double size;

  const CompanionCard({
    super.key,
    this.emotion,
    this.name = '晚星',
    this.size = 200,
  });

  @override
  Widget build(BuildContext context) {
    final emotionLabel = _getEmotionLabel(emotion);

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        CompanionAvatar(
          size: size,
          emotion: emotion,
          showGlow: true,
        ),
        const SizedBox(height: 8),
        Text(
          name,
          style: const TextStyle(
            color: AppTheme.text,
            fontSize: 14,
            fontWeight: FontWeight.w600,
          ),
        ),
        if (emotionLabel.isNotEmpty) ...[
          const SizedBox(height: 2),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
            decoration: BoxDecoration(
              color: AppTheme.primary.withOpacity(0.15),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Text(
              emotionLabel,
              style: const TextStyle(
                color: AppTheme.primary,
                fontSize: 11,
              ),
            ),
          ),
        ],
      ],
    );
  }

  String _getEmotionLabel(String? emotion) {
    switch (emotion) {
      case 'happy': return '😊 开心';
      case 'sad': return '😢 难过';
      case 'surprised': return '😮 惊讶';
      case 'thinking': return '🤔 思考中';
      case 'excited': return '🤩 兴奋';
      case 'calm': return '😌 平静';
      default: return '';
    }
  }
}

/// 小型伴侣头像（用于消息气泡旁）
class CompanionMiniAvatar extends StatelessWidget {
  final String? emotion;
  final double size;

  const CompanionMiniAvatar({
    super.key,
    this.emotion,
    this.size = 36,
  });

  @override
  Widget build(BuildContext context) {
    return CompanionAvatar(
      size: size,
      emotion: emotion,
      showGlow: false,
      animate: false,
    );
  }
}
