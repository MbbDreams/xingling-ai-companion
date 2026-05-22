from fastapi import APIRouter

from app.api.routes import auth, chat, diary, discover, growth, memories, profile, shop

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(memories.router, prefix="/memory", tags=["memory"])
api_router.include_router(diary.router, prefix="/diary", tags=["diary"])
api_router.include_router(growth.router, prefix="/growth", tags=["growth"])
api_router.include_router(shop.router, prefix="/shop", tags=["shop"])
api_router.include_router(profile.router, prefix="/profile", tags=["profile"])
api_router.include_router(discover.router, prefix="/discover", tags=["discover"])
