/// 商店商品模型
class ShopItem {
  final int itemId;
  final String name;
  final String? description;
  final ShopCategory category;
  final int price;
  final String? imageUrl;
  final bool isOwned;
  final bool isEquipped;

  ShopItem({
    required this.itemId,
    required this.name,
    this.description,
    required this.category,
    required this.price,
    this.imageUrl,
    this.isOwned = false,
    this.isEquipped = false,
  });

  factory ShopItem.fromJson(Map<String, dynamic> json) {
    return ShopItem(
      itemId: json['item_id'] ?? 0,
      name: json['name'] ?? '',
      description: json['description'],
      category: ShopCategory.fromString(json['category']),
      price: json['price'] ?? 0,
      imageUrl: json['image_url'],
      isOwned: json['is_owned'] ?? false,
      isEquipped: json['is_equipped'] ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'item_id': itemId,
      'name': name,
      'description': description,
      'category': category.name,
      'price': price,
      'image_url': imageUrl,
      'is_owned': isOwned,
      'is_equipped': isEquipped,
    };
  }
}

/// 商店分类
enum ShopCategory {
  vip,
  outfit,
  scene,
  voicepack;

  static ShopCategory fromString(String? value) {
    if (value == null) return ShopCategory.outfit;
    return ShopCategory.values.firstWhere(
      (e) => e.name.toLowerCase() == value.toLowerCase(),
      orElse: () => ShopCategory.outfit,
    );
  }

  String get displayName {
    switch (this) {
      case ShopCategory.vip:
        return '会员';
      case ShopCategory.outfit:
        return '服装';
      case ShopCategory.scene:
        return '场景';
      case ShopCategory.voicepack:
        return '语音包';
    }
  }

  String get icon {
    switch (this) {
      case ShopCategory.vip:
        return '👑';
      case ShopCategory.outfit:
        return '👗';
      case ShopCategory.scene:
        return '🏠';
      case ShopCategory.voicepack:
        return '🎵';
    }
  }
}

/// 购买响应
class PurchaseResponse {
  final bool success;
  final String message;
  final int? remainingCoins;

  PurchaseResponse({
    required this.success,
    required this.message,
    this.remainingCoins,
  });

  factory PurchaseResponse.fromJson(Map<String, dynamic> json) {
    return PurchaseResponse(
      success: json['success'] ?? false,
      message: json['message'] ?? '',
      remainingCoins: json['remaining_coins'],
    );
  }
}

/// 装备响应
class EquipResponse {
  final bool success;
  final String message;

  EquipResponse({
    required this.success,
    required this.message,
  });

  factory EquipResponse.fromJson(Map<String, dynamic> json) {
    return EquipResponse(
      success: json['success'] ?? false,
      message: json['message'] ?? '',
    );
  }
}
