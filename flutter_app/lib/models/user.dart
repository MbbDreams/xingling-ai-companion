/// 用户模型
class UserProfile {
  final int userId;
  final String username;
  final String? avatarUrl;
  final bool isVip;
  final DateTime createdAt;

  UserProfile({
    required this.userId,
    required this.username,
    this.avatarUrl,
    this.isVip = false,
    required this.createdAt,
  });

  factory UserProfile.fromJson(Map<String, dynamic> json) {
    return UserProfile(
      userId: json['user_id'] ?? 0,
      username: json['username'] ?? '',
      avatarUrl: json['avatar_url'],
      isVip: json['is_vip'] ?? false,
      createdAt: DateTime.parse(json['created_at'] ?? DateTime.now().toIso8601String()),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'user_id': userId,
      'username': username,
      'avatar_url': avatarUrl,
      'is_vip': isVip,
      'created_at': createdAt.toIso8601String(),
    };
  }
}

/// AI 伴侣模型
class Companion {
  final int companionId;
  final String name;
  final String? avatarUrl;
  final int intimacyLevel;
  final int intimacyPoints;
  final String? voiceUrl;
  final String? personality;

  Companion({
    required this.companionId,
    required this.name,
    this.avatarUrl,
    this.intimacyLevel = 1,
    this.intimacyPoints = 0,
    this.voiceUrl,
    this.personality,
  });

  factory Companion.fromJson(Map<String, dynamic> json) {
    return Companion(
      companionId: json['companion_id'] ?? 0,
      name: json['name'] ?? '',
      avatarUrl: json['avatar_url'],
      intimacyLevel: json['intimacy_level'] ?? 1,
      intimacyPoints: json['intimacy_points'] ?? 0,
      voiceUrl: json['voice_url'],
      personality: json['personality'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'companion_id': companionId,
      'name': name,
      'avatar_url': avatarUrl,
      'intimacy_level': intimacyLevel,
      'intimacy_points': intimacyPoints,
      'voice_url': voiceUrl,
      'personality': personality,
    };
  }
}

/// 用户资料（包含用户和伴侣）
class UserProfileWithCompanion {
  final UserProfile user;
  final Companion companion;

  UserProfileWithCompanion({
    required this.user,
    required this.companion,
  });

  factory UserProfileWithCompanion.fromJson(Map<String, dynamic> json) {
    return UserProfileWithCompanion(
      user: UserProfile.fromJson(json['user'] ?? {}),
      companion: Companion.fromJson(json['companion'] ?? {}),
    );
  }
}
