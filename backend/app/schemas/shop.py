from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ShopItemRead(BaseModel):
    id: int
    name: str
    category: str
    price: int
    description: str | None = None
    asset_url: str | None = None
    is_active: bool
    is_owned: bool = False
    is_equipped: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PurchaseResponse(BaseModel):
    success: bool
    remaining_coins: int
    item: ShopItemRead


class EquipResponse(BaseModel):
    success: bool
    item: ShopItemRead
