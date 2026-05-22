import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'api/api_client.dart';
import 'providers/auth_provider.dart';
import 'screens/home_screen.dart';
import 'screens/auth/login_page.dart';
import 'services/secure_storage.dart';
import 'utils/theme.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // 初始化系统 UI
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
    ),
  );
  
  runApp(
    const ProviderScope(
      child: XinglingApp(),
    ),
  );
}

class XinglingApp extends ConsumerStatefulWidget {
  const XinglingApp({super.key});

  @override
  ConsumerState<XinglingApp> createState() => _XinglingAppState();
}

class _XinglingAppState extends ConsumerState<XinglingApp> {
  bool _isInitialized = false;

  @override
  void initState() {
    super.initState();
    // 使用 addPostFrameCallback 确保在构建完成后初始化
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _initializeAuth();
    });
  }

  Future<void> _initializeAuth() async {
    // 尝试恢复登录状态
    await ref.read(authProvider.notifier).tryRestoreSession();
    if (mounted) {
      setState(() {
        _isInitialized = true;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authProvider);
    
    // 等待初始化完成
    if (!_isInitialized) {
      return MaterialApp(
        title: '星灵AI伴侣',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.darkTheme,
        home: const Scaffold(
          backgroundColor: AppTheme.background,
          body: Center(
            child: CircularProgressIndicator(
              color: AppTheme.primary,
            ),
          ),
        ),
      );
    }
    
    return MaterialApp(
      title: '星灵AI伴侣',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      // 根据认证状态决定显示哪个页面
      home: authState.isAuthenticated
          ? const HomeScreen()
          : const LoginPage(),
      routes: {
        '/login': (context) => const LoginPage(),
        '/home': (context) => const HomeScreen(),
      },
    );
  }
}
