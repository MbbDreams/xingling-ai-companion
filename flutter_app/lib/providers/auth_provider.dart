import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/auth.dart';
import '../services/auth_service.dart';
import '../services/secure_storage.dart';

/// 认证状态
class AuthState {
  final AuthStatus status;
  final UserInfo? user;
  final String? error;

  AuthState({
    this.status = AuthStatus.initial,
    this.user,
    this.error,
  });

  AuthState copyWith({
    AuthStatus? status,
    UserInfo? user,
    String? error,
  }) {
    return AuthState(
      status: status ?? this.status,
      user: user ?? this.user,
      error: error,
    );
  }

  /// 是否已认证
  bool get isAuthenticated => status == AuthStatus.authenticated;
}

/// 认证状态管理
class AuthNotifier extends StateNotifier<AuthState> {
  final AuthService _authService;
  bool _initialized = false;

  AuthNotifier(this._authService) : super(AuthState());

  /// 尝试恢复会话 - 供首次启动时调用
  Future<void> tryRestoreSession() async {
    if (_initialized) return;
    _initialized = true;
    
    state = state.copyWith(status: AuthStatus.loading);
    
    try {
      final isLoggedIn = await SecureStorage.isLoggedIn();
      if (isLoggedIn) {
        final user = await _authService.getCurrentUser();
        if (user != null) {
          state = state.copyWith(
            status: AuthStatus.authenticated,
            user: user,
          );
          return;
        }
      }
      
      // 尝试刷新Token
      final token = await _authService.refreshToken();
      if (token != null) {
        final user = await _authService.getCurrentUser();
        state = state.copyWith(
          status: AuthStatus.authenticated,
          user: user,
        );
        return;
      }
      
      state = state.copyWith(status: AuthStatus.unauthenticated);
    } catch (e) {
      state = state.copyWith(
        status: AuthStatus.unauthenticated,
        error: e.toString(),
      );
    }
  }

  /// 发送验证码
  Future<bool> sendCode(String phone) async {
    return await _authService.sendVerificationCode(phone);
  }

  /// 注册
  Future<bool> register({
    required String phone,
    required String code,
    required String password,
    required String nickname,
  }) async {
    state = state.copyWith(status: AuthStatus.loading, error: null);
    
    try {
      final token = await _authService.register(
        phone: phone,
        code: code,
        password: password,
        nickname: nickname,
      );
      
      if (token != null) {
        final user = await _authService.getCurrentUser();
        state = state.copyWith(
          status: AuthStatus.authenticated,
          user: user,
        );
        return true;
      }
      
      state = state.copyWith(
        status: AuthStatus.error,
        error: '注册失败',
      );
      return false;
    } catch (e) {
      state = state.copyWith(
        status: AuthStatus.error,
        error: e.toString(),
      );
      return false;
    }
  }

  /// 登录
  Future<bool> login({
    required String phone,
    required String code,
  }) async {
    state = state.copyWith(status: AuthStatus.loading, error: null);
    
    try {
      final token = await _authService.login(
        phone: phone,
        code: code,
      );
      
      if (token != null) {
        final user = await _authService.getCurrentUser();
        state = state.copyWith(
          status: AuthStatus.authenticated,
          user: user,
        );
        return true;
      }
      
      state = state.copyWith(
        status: AuthStatus.error,
        error: '登录失败',
      );
      return false;
    } catch (e) {
      state = state.copyWith(
        status: AuthStatus.error,
        error: e.toString(),
      );
      return false;
    }
  }

  /// 更新用户信息
  Future<bool> updateProfile({
    String? nickname,
    String? avatar,
    String? email,
    String? gender,
    String? birthday,
    String? bio,
    String? location,
    String? website,
  }) async {
    try {
      final user = await _authService.updateProfile(
        nickname: nickname,
        avatar: avatar,
        email: email,
        gender: gender,
        birthday: birthday,
        bio: bio,
        location: location,
        website: website,
      );
      
      if (user != null) {
        state = state.copyWith(user: user);
        return true;
      }
      return false;
    } catch (e) {
      state = state.copyWith(error: e.toString());
      return false;
    }
  }

  /// 退出登录
  Future<void> logout() async {
    await _authService.logout();
    state = AuthState(status: AuthStatus.unauthenticated);
  }

  /// 刷新用户信息
  Future<void> refreshUser() async {
    final user = await _authService.getCurrentUser();
    if (user != null) {
      state = state.copyWith(user: user);
    }
  }
}

/// 认证状态Provider
final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  final authService = ref.watch(authServiceProvider);
  return AuthNotifier(authService);
});
