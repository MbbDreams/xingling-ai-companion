import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../models/auth.dart';

/// 安全存储服务 - 存储敏感信息
class SecureStorage {
  static const _storage = FlutterSecureStorage(
    aOptions: AndroidOptions(
      encryptedSharedPreferences: true,
    ),
    iOptions: IOSOptions(
      accessibility: KeychainAccessibility.first_unlock_this_device,
    ),
  );

  // Keys
  static const _keyAccessToken = 'access_token';
  static const _keyRefreshToken = 'refresh_token';
  static const _keyExpiresAt = 'expires_at';
  static const _keyUserInfo = 'user_info';

  /// 保存Token
  static Future<void> saveToken(TokenInfo token) async {
    await _storage.write(key: _keyAccessToken, value: token.accessToken);
    await _storage.write(key: _keyRefreshToken, value: token.refreshToken);
    await _storage.write(key: _keyExpiresAt, value: token.expiresAt.toIso8601String());
  }

  /// 获取Token
  static Future<TokenInfo?> getToken() async {
    final accessToken = await _storage.read(key: _keyAccessToken);
    final refreshToken = await _storage.read(key: _keyRefreshToken);
    final expiresAtStr = await _storage.read(key: _keyExpiresAt);

    if (accessToken == null || refreshToken == null) {
      return null;
    }

    return TokenInfo(
      accessToken: accessToken,
      refreshToken: refreshToken,
      expiresAt: expiresAtStr != null
          ? DateTime.parse(expiresAtStr)
          : DateTime.now().add(const Duration(hours: 24)),
    );
  }

  /// 获取AccessToken
  static Future<String?> getAccessToken() async {
    return await _storage.read(key: _keyAccessToken);
  }

  /// 获取RefreshToken
  static Future<String?> getRefreshToken() async {
    return await _storage.read(key: _keyRefreshToken);
  }

  /// 保存用户信息
  static Future<void> saveUserInfo(UserInfo user) async {
    await _storage.write(key: _keyUserInfo, value: jsonEncode({
      'id': user.id,
      'phone': user.phone,
      'nickname': user.nickname,
      'avatar': user.avatar,
      'email': user.email,
      'gender': user.gender,
      'birthday': user.birthday,
      'bio': user.bio,
      'location': user.location,
      'website': user.website,
      'coins': user.coins,
      'is_vip': user.isVip,
      'vip_expire_at': user.vipExpireAt?.toIso8601String(),
      'created_at': user.createdAt.toIso8601String(),
    }));
  }

  /// 获取用户信息
  static Future<UserInfo?> getUserInfo() async {
    final data = await _storage.read(key: _keyUserInfo);
    if (data == null) return null;

    try {
      return UserInfo.fromJson(jsonDecode(data));
    } catch (e) {
      debugPrint('解析用户信息失败: $e');
      return null;
    }
  }

  /// 清除所有认证信息
  static Future<void> clearAll() async {
    await _storage.delete(key: _keyAccessToken);
    await _storage.delete(key: _keyRefreshToken);
    await _storage.delete(key: _keyExpiresAt);
    await _storage.delete(key: _keyUserInfo);
  }

  /// 检查是否已登录
  static Future<bool> isLoggedIn() async {
    final token = await getToken();
    return token != null && token.isValid;
  }
}
