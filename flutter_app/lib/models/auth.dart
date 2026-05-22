import 'package:flutter/foundation.dart';

/// Token信息
class TokenInfo {
  final String accessToken;
  final String refreshToken;
  final DateTime expiresAt;

  TokenInfo({
    required this.accessToken,
    required this.refreshToken,
    required this.expiresAt,
  });

  bool get isExpired => DateTime.now().isAfter(expiresAt);
  bool get isValid => accessToken.isNotEmpty && !isExpired;

  factory TokenInfo.fromJson(Map<String, dynamic> json) {
    return TokenInfo(
      accessToken: json['access_token'] ?? '',
      refreshToken: json['refresh_token'] ?? '',
      expiresAt: DateTime.now().add(Duration(seconds: json['expires_in'] ?? 86400)),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'access_token': accessToken,
      'refresh_token': refreshToken,
      'expires_at': expiresAt.toIso8601String(),
    };
  }
}

/// 用户信息
class UserInfo {
  final int id;
  final String phone;
  final String nickname;
  final String? avatar;
  final String? email;
  final String? gender;
  final String? birthday;
  final String? bio;
  final String? location;
  final String? website;
  final int coins;
  final bool isVip;
  final DateTime? vipExpireAt;
  final DateTime createdAt;

  UserInfo({
    required this.id,
    required this.phone,
    required this.nickname,
    this.avatar,
    this.email,
    this.gender,
    this.birthday,
    this.bio,
    this.location,
    this.website,
    required this.coins,
    required this.isVip,
    this.vipExpireAt,
    required this.createdAt,
  });

  factory UserInfo.fromJson(Map<String, dynamic> json) {
    return UserInfo(
      id: json['id'] ?? 0,
      phone: json['phone'] ?? '',
      nickname: json['nickname'] ?? '用户',
      avatar: json['avatar'],
      email: json['email'],
      gender: json['gender'],
      birthday: json['birthday'],
      bio: json['bio'],
      location: json['location'],
      website: json['website'],
      coins: json['coins'] ?? 0,
      isVip: json['is_vip'] ?? false,
      vipExpireAt: json['vip_expire_at'] != null
          ? DateTime.parse(json['vip_expire_at'])
          : null,
      createdAt: DateTime.parse(json['created_at'] ?? DateTime.now().toIso8601String()),
    );
  }
}

/// 认证状态
enum AuthStatus {
  initial,
  loading,
  authenticated,
  unauthenticated,
  error,
}
