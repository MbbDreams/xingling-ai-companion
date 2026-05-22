import 'package:flutter/material.dart';

class AppTheme {
  // ── 原型 CSS 变量映射 ──
  static const Color bg = Color(0xFF050B1A);
  static const Color background = Color(0xFF050B1A);
  static const Color panel = Color(0xFF151E3A);
  static const Color panelStrong = Color(0xDD222B4E);
  static const Color line = Color(0x29AEBEFF); // rgba(174,190,255,0.16)
  static const Color text = Color(0xFFF7F4FF);
  static const Color muted = Color(0xFFAEB5D2);
  static const Color soft = Color(0xFF727AA0);
  static const Color primary = Color(0xFF8F73FF);
  static const Color primary2 = Color(0xFFD984CA);
  static const Color accent = Color(0xFFFFCF7A);
  static const Color danger = Color(0xFFEE4C58);
  static const Color online = Color(0xFF67E6A1);
  static const Color activeNav = Color(0xFFBFAEFF);
  static const Color userBubbleStart = Color(0xFF6F63D6);
  static const Color userBubbleEnd = Color(0xFF8975FF);
  static const Color aiBubble = Color(0xE6FFFFFF);
  static const Color aiBubbleText = Color(0xFF1E2030);

  static ThemeData get darkTheme {
    return ThemeData(
      brightness: Brightness.dark,
      useMaterial3: false,
      scaffoldBackgroundColor: bg,
      colorScheme: const ColorScheme.dark(
        primary: primary,
        secondary: primary2,
        surface: panel,
        onPrimary: text,
        onSecondary: text,
        onSurface: text,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: false,
        iconTheme: IconThemeData(color: muted),
        titleTextStyle: TextStyle(
          color: text,
          fontSize: 23,
          fontWeight: FontWeight.w700,
          letterSpacing: 0,
        ),
      ),
      cardTheme: CardThemeData(
        color: const Color(0x4D1F2A4F), // rgba(31,42,79,0.30)
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(18),
          side: BorderSide(color: line),
        ),
        margin: EdgeInsets.zero,
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: Color(0xE6060C1F), // rgba(6,12,31,0.90)
        selectedItemColor: activeNav,
        unselectedItemColor: soft,
        type: BottomNavigationBarType.fixed,
        elevation: 0,
        selectedLabelStyle: TextStyle(fontSize: 11),
        unselectedLabelStyle: TextStyle(fontSize: 11),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: const Color(0x1AFFFFFF), // rgba(255,255,255,0.10)
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(24),
          borderSide: BorderSide(color: line),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(24),
          borderSide: BorderSide(color: line),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(24),
          borderSide: BorderSide(color: primary),
        ),
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
        hintStyle: const TextStyle(color: soft, fontSize: 14),
      ),
      textTheme: const TextTheme(
        bodyMedium: TextStyle(color: text, fontSize: 13),
        bodySmall: TextStyle(color: muted, fontSize: 12),
        titleMedium: TextStyle(color: text, fontSize: 16, fontWeight: FontWeight.w600),
        titleLarge: TextStyle(color: text, fontSize: 23, fontWeight: FontWeight.w700),
      ),
      iconTheme: const IconThemeData(color: muted, size: 20),
      dividerColor: line,
    );
  }

  // ── 通用装饰 ──

  /// 面板卡片 BoxDecoration（匹配 .panel）
  static BoxDecoration get panelDecoration => BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment(0, 0),
          end: Alignment(0, 1),
          colors: [
            Color(0xC71F2A4F), // rgba(31,42,79,0.78)
            Color(0xC7111934), // rgba(17,25,52,0.78)
          ],
        ),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: line),
        boxShadow: const [
          BoxShadow(
            color: Color(0x0DFFFFFF), // inset 0 1px 0 rgba(255,255,255,0.05)
            offset: Offset(0, -1),
            blurRadius: 0,
          ),
        ],
      );

  /// 主按钮渐变
  static BoxDecoration get primaryButtonDecoration => BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment(-1, -1),
          end: Alignment(1, 1),
          colors: [primary, Color(0xFF6E5BD5)],
        ),
        borderRadius: BorderRadius.circular(24),
      );

  /// 次要按钮
  static BoxDecoration get secondaryButtonDecoration => BoxDecoration(
        color: const Color(0x1AFFFFFF),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: line),
      );

  /// 图标按钮（匹配 .icon-button）
  static BoxDecoration get iconButtonDecoration => BoxDecoration(
        color: const Color(0x14FFFFFF),
        shape: BoxShape.circle,
        border: Border.all(color: line),
      );

  /// 用户消息气泡
  static BoxDecoration get userBubbleDecoration => BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment(-1, -1),
          end: Alignment(1, 1),
          colors: [userBubbleStart, userBubbleEnd],
        ),
        borderRadius: const BorderRadius.only(
          topLeft: Radius.circular(16),
          topRight: Radius.circular(16),
          bottomLeft: Radius.circular(16),
          bottomRight: Radius.circular(4),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.16),
            blurRadius: 30,
            offset: const Offset(0, 10),
          ),
        ],
      );

  /// AI 消息气泡
  static BoxDecoration get aiBubbleDecoration => BoxDecoration(
        color: aiBubble,
        borderRadius: const BorderRadius.only(
          topLeft: Radius.circular(16),
          topRight: Radius.circular(16),
          bottomLeft: Radius.circular(4),
          bottomRight: Radius.circular(16),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.16),
            blurRadius: 30,
            offset: const Offset(0, 10),
          ),
        ],
      );
}
