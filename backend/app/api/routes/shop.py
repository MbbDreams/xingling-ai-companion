from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.models import ShopItem, UserItem
from app.schemas.shop import ShopItemRead, PurchaseResponse, EquipResponse
from app.services.bootstrap import get_or_create_companion, get_or_create_user

router = APIRouter()


@router.get("/items", response_model=list[ShopItemRead])
async def list_shop_items(
    category: str | None = None,
    user_id: int | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> list[ShopItemRead]:
    """获取商店商品列表"""
    user = await get_or_create_user(session, user_id)
    
    query = select(ShopItem).where(ShopItem.is_active == True)
    
    if category:
        query = query.where(ShopItem.category == category)
    
    query = query.order_by(ShopItem.category, ShopItem.price)
    result = await session.scalars(query)
    items = result.all()
    
    # 获取用户已拥有的商品
    user_items_result = await session.scalars(
        select(UserItem).where(UserItem.user_id == user.id)
    )
    user_items = {ui.item_id: ui for ui in user_items_result.all()}
    
    return [
        ShopItemRead(
            id=item.id,
            name=item.name,
            category=item.category,
            price=item.price,
            description=item.description,
            asset_url=item.asset_url,
            is_active=item.is_active,
            is_owned=item.id in user_items,
            is_equipped=user_items.get(item.id, None).is_equipped if item.id in user_items else False,
            created_at=item.created_at,
        )
        for item in items
    ]


@router.get("/balance")
async def get_user_balance(
    user_id: int | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """获取用户星币余额"""
    user = await get_or_create_user(session, user_id)
    return {"coins": user.coins}


@router.post("/items/{item_id}/purchase", response_model=PurchaseResponse)
async def purchase_item(
    item_id: int,
    user_id: int | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> PurchaseResponse:
    """购买商品"""
    user = await get_or_create_user(session, user_id)
    
    # 获取商品
    item = await session.get(ShopItem, item_id)
    if not item or not item.is_active:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    # 检查是否已拥有
    existing = await session.scalar(
        select(UserItem).where(
            UserItem.user_id == user.id,
            UserItem.item_id == item_id,
        )
    )
    if existing:
        raise HTTPException(status_code=400, detail="已拥有该商品")
    
    # 检查余额
    if user.coins < item.price:
        raise HTTPException(status_code=400, detail="星币不足")
    
    # 扣除星币
    user.coins -= item.price
    
    # 创建用户物品记录
    user_item = UserItem(
        user_id=user.id,
        item_id=item_id,
        is_equipped=False,
    )
    session.add(user_item)
    
    await session.flush()
    await session.commit()
    
    return PurchaseResponse(
        success=True,
        remaining_coins=user.coins,
        item=ShopItemRead(
            id=item.id,
            name=item.name,
            category=item.category,
            price=item.price,
            description=item.description,
            asset_url=item.asset_url,
            is_active=item.is_active,
            is_owned=True,
            is_equipped=False,
            created_at=item.created_at,
        ),
    )


@router.post("/items/{item_id}/equip", response_model=EquipResponse)
async def equip_item(
    item_id: int,
    user_id: int | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> EquipResponse:
    """装备商品"""
    user = await get_or_create_user(session, user_id)
    companion = await get_or_create_companion(session, user)
    
    # 获取商品
    item = await session.get(ShopItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    # 检查是否已拥有
    user_item = await session.scalar(
        select(UserItem).where(
            UserItem.user_id == user.id,
            UserItem.item_id == item_id,
        )
    )
    if not user_item:
        raise HTTPException(status_code=400, detail="未拥有该商品")
    
    # 同类型商品取消装备
    await session.execute(
        select(UserItem)
        .where(
            UserItem.user_id == user.id,
            UserItem.is_equipped == True,
        )
    )
    
    # 更新装备状态
    user_item.is_equipped = True
    
    # 更新伴侣外观
    if item.category == "outfit":
        companion.current_outfit_id = item_id
    elif item.category == "scene":
        companion.current_scene_id = item_id
    elif item.category == "voice":
        companion.voice_style = item.name
    
    await session.flush()
    await session.commit()
    
    return EquipResponse(
        success=True,
        item=ShopItemRead(
            id=item.id,
            name=item.name,
            category=item.category,
            price=item.price,
            description=item.description,
            asset_url=item.asset_url,
            is_active=item.is_active,
            is_owned=True,
            is_equipped=True,
            created_at=item.created_at,
        ),
    )
