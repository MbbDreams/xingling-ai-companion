"""
认证服务 - 包含JWT、密码加密、验证码等功能
"""
import random
import hashlib
import hmac
import base64
import json
from datetime import datetime, timedelta
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings


# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """认证服务"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ============ 密码相关 ============
    
    @staticmethod
    def hash_password(password: str) -> str:
        """对密码进行哈希加密"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)
    
    # ============ JWT相关 ============
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(hours=24))
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    
    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """创建刷新令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=30)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            if payload.get("type") != token_type:
                return None
            return payload
        except JWTError:
            return None
    
    # ============ 验证码相关 ============
    
    @staticmethod
    def generate_verification_code(length: int = 6) -> str:
        """生成验证码"""
        return ''.join([str(random.randint(0, 9)) for _ in range(length)])
    
    @staticmethod
    def hash_verification_code(phone: str, code: str) -> str:
        """对验证码进行哈希（不存储明文）"""
        message = f"{phone}:{code}:{settings.secret_key}"
        return hashlib.sha256(message.encode()).hexdigest()
    
    # ============ 签名相关 ============
    
    @staticmethod
    def generate_signature(params: dict) -> str:
        """生成请求签名（防篡改）"""
        # 按字典key排序后拼接
        sorted_params = sorted(params.items())
        message = '&'.join([f"{k}={v}" for k, v in sorted_params])
        signature = hmac.new(
            settings.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    @staticmethod
    def verify_signature(params: dict, signature: str) -> bool:
        """验证请求签名"""
        expected = AuthService.generate_signature(params)
        return hmac.compare_digest(expected, signature)
    
    # ============ 敏感数据加密 ============
    
    @staticmethod
    def encrypt_sensitive_data(data: str) -> str:
        """加密敏感数据（如真实姓名、身份证等）"""
        from cryptography.fernet import Fernet
        import os
        
        # 使用固定的key（生产环境应从配置读取）
        key = base64.urlsafe_b64encode(settings.secret_key.encode()[:32].ljust(32, b'0'))
        f = Fernet(key)
        return f.encrypt(data.encode()).decode()
    
    @staticmethod
    def decrypt_sensitive_data(encrypted_data: str) -> str:
        """解密敏感数据"""
        from cryptography.fernet import Fernet
        import os
        
        key = base64.urlsafe_b64encode(settings.secret_key.encode()[:32].ljust(32, b'0'))
        f = Fernet(key)
        return f.decrypt(encrypted_data.encode()).decode()


# 内存中的验证码存储（生产环境应使用Redis）
_verification_codes: dict = {}


class VerificationCodeStore:
    """验证码存储（内存版，生产环境建议用Redis）"""
    
    @staticmethod
    def store(phone: str, code: str, purpose: str = "login"):
        """存储验证码"""
        _verification_codes[phone] = {
            "code": AuthService.hash_verification_code(phone, code),
            "purpose": purpose,
            "created_at": datetime.utcnow(),
            "attempts": 0
        }
    
    @staticmethod
    def verify(phone: str, code: str) -> bool:
        """验证验证码"""
        if phone not in _verification_codes:
            return False
        
        stored = _verification_codes[phone]
        hashed = AuthService.hash_verification_code(phone, code)
        
        # 检查是否过期（5分钟）
        if datetime.utcnow() - stored["created_at"] > timedelta(minutes=5):
            del _verification_codes[phone]
            return False
        
        # 检查尝试次数
        if stored["attempts"] >= 5:
            del _verification_codes[phone]
            return False
        
        # 验证
        if hmac.compare_digest(hashed, stored["code"]):
            del _verification_codes[phone]  # 验证成功后删除
            return True
        
        stored["attempts"] += 1
        return False
    
    @staticmethod
    def get_code(phone: str) -> Optional[str]:
        """获取验证码（调试用）"""
        if phone in _verification_codes:
            stored = _verification_codes[phone]
            if datetime.utcnow() - stored["created_at"] < timedelta(minutes=5):
                # 返回原始验证码（实际应用中不应返回）
                return stored["code"]
        return None


class SMSService:
    """短信服务 - 当前为模拟实现，生产环境接入阿里云/腾讯云"""
    
    @staticmethod
    async def send_verification_code(phone: str, code: str) -> dict:
        """
        发送验证码短信
        返回: {"success": bool, "message": str}
        """
        # TODO: 生产环境接入真实短信服务商
        # 当前仅打印到控制台，方便开发测试
        print(f"\n{'='*50}")
        print(f"[SMS] 发送验证码到 {phone}")
        print(f"[SMS] 验证码: {code}")
        print(f"{'='*50}\n")
        
        # 模拟发送成功
        return {
            "success": True,
            "message": "验证码已发送"
        }
    
    @staticmethod
    async def send_sms(phone: str, template_code: str, params: dict) -> dict:
        """
        发送普通短信
        生产环境接入:
        - 阿里云短信服务
        - 腾讯云短信服务
        - SendGrid (国际)
        """
        print(f"\n[SMS] 发送短信到 {phone}, 模板: {template_code}, 参数: {params}\n")
        return {"success": True, "message": "短信已发送"}
