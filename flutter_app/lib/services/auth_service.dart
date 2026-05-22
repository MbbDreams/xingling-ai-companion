import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/api_client.dart';
import '../models/auth.dart';
import 'secure_storage.dart';

/// 认证服务 Provider
final authServiceProvider = Provider<AuthService>((ref) {
  final apiService = ref.watch(apiServiceProvider);
  return AuthService(apiService);
});

/// 认证服务
class AuthService {
  final ApiService _api;

  AuthService(this._api);

  /// 发送验证码
  Future<bool> sendVerificationCode(String phone) async {
    try {
      final response = await _api.post(
        '/auth/send-code',
        data: {'phone': phone, 'purpose': 'login'},
      );
      
      if (response.data['success'] == true) {
        // 开发环境打印验证码
        if (kDebugMode && response.data['debug_code'] != null) {
          print('[DEBUG] 验证码: ${response.data['debug_code']}');
        }
        return true;
      }
      return false;
    } catch (e) {
      debugPrint('发送验证码失败: $e');
      return false;
    }
  }

  /// 注册
  Future<TokenInfo?> register({
    required String phone,
    required String code,
    required String password,
    required String nickname,
    String? avatar,
  }) async {
    try {
      final response = await _api.post(
        '/auth/register',
        data: {
          'phone': phone,
          'code': code,
          'password': password,
          'nickname': nickname,
          if (avatar != null) 'avatar': avatar,
        },
      );
      
      final token = TokenInfo.fromJson(response.data);
      await SecureStorage.saveToken(token);
      return token;
    } catch (e) {
      debugPrint('注册失败: $e');
      rethrow;
    }
  }

  /// 登录
  Future<TokenInfo?> login({
    required String phone,
    required String code,
  }) async {
    try {
      final response = await _api.post(
        '/auth/login',
        data: {
          'phone': phone,
          'code': code,
        },
      );
      
      final token = TokenInfo.fromJson(response.data);
      await SecureStorage.saveToken(token);
      return token;
    } catch (e) {
      debugPrint('登录失败: $e');
      rethrow;
    }
  }

  /// 刷新Token
  Future<TokenInfo?> refreshToken() async {
    try {
      final refreshToken = await SecureStorage.getRefreshToken();
      if (refreshToken == null) return null;

      final response = await _api.post(
        '/auth/refresh',
        data: {'refresh_token': refreshToken},
      );
      
      final token = TokenInfo.fromJson(response.data);
      await SecureStorage.saveToken(token);
      return token;
    } catch (e) {
      debugPrint('刷新Token失败: $e');
      await SecureStorage.clearAll();
      return null;
    }
  }

  /// 获取当前用户信息
  Future<UserInfo?> getCurrentUser() async {
    try {
      final response = await _api.get('/auth/me');
      final user = UserInfo.fromJson(response.data);
      await SecureStorage.saveUserInfo(user);
      return user;
    } catch (e) {
      debugPrint('获取用户信息失败: $e');
      return null;
    }
  }

  /// 更新个人资料
  Future<UserInfo?> updateProfile({
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
      final response = await _api.put(
        '/auth/me',
        data: {
          if (nickname != null) 'nickname': nickname,
          if (avatar != null) 'avatar': avatar,
          if (email != null) 'email': email,
          if (gender != null) 'gender': gender,
          if (birthday != null) 'birthday': birthday,
          if (bio != null) 'bio': bio,
          if (location != null) 'location': location,
          if (website != null) 'website': website,
        },
      );
      
      final user = UserInfo.fromJson(response.data);
      await SecureStorage.saveUserInfo(user);
      return user;
    } catch (e) {
      debugPrint('更新资料失败: $e');
      rethrow;
    }
  }

  /// 修改密码
  Future<bool> changePassword({
    required String oldPassword,
    required String newPassword,
  }) async {
    try {
      await _api.post(
        '/auth/change-password',
        data: {
          'old_password': oldPassword,
          'new_password': newPassword,
        },
      );
      return true;
    } catch (e) {
      debugPrint('修改密码失败: $e');
      return false;
    }
  }

  /// 退出登录
  Future<void> logout() async {
    try {
      await _api.post('/auth/logout');
    } catch (e) {
      debugPrint('退出登录请求失败: $e');
    } finally {
      await SecureStorage.clearAll();
    }
  }
}
