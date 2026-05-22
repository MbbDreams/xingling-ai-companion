"""
短信服务 - 发送验证码（模拟版）
生产环境需要接入真实的短信服务商：阿里云、腾讯云、SendGrid等
"""
import random
import asyncio
from typing import Optional


class SMSService:
    """短信服务"""
    
    # 支持的手机号前缀（模拟）
    SUPPORTED_PREFIXES = ["+86", "86", ""]
    
    @staticmethod
    async def send_verification_code(phone: str, code: str) -> dict:
        """
        发送验证码短信
        返回: {"success": True, "message": "发送成功"}
        
        生产环境应接入真实短信服务：
        - 阿里云: https://help.aliyun.com/document_detail/101414.html
        - 腾讯云: https://cloud.tencent.com/document/product/1014
        - SendGrid: https://sendgrid.com/
        """
        # 清理手机号
        phone = phone.strip()
        for prefix in SMSService.SUPPORTED_PREFIXES:
            if phone.startswith(prefix):
                phone = phone[len(prefix):]
                break
        
        # 手机号格式校验（中国大陆）
        if not phone.isdigit() or len(phone) != 11:
            return {"success": False, "message": "手机号格式不正确"}
        
        # 模拟发送延迟
        await asyncio.sleep(0.5)
        
        # 模拟成功率（90%成功）
        if random.random() < 0.9:
            print(f"[SMS] 发送验证码到 {phone}: {code}")
            return {"success": True, "message": "发送成功"}
        else:
            return {"success": False, "message": "短信发送失败，请稍后重试"}
    
    @staticmethod
    async def send_template_sms(phone: str, template_id: str, params: dict) -> dict:
        """
        发送模板短信
        template_id: 模板ID
        params: 模板参数
        """
        # 清理手机号
        phone = phone.strip()
        for prefix in SMSService.SUPPORTED_PREFIXES:
            if phone.startswith(prefix):
                phone = phone[len(prefix):]
                break
        
        print(f"[SMS] 发送模板短信到 {phone}, 模板: {template_id}, 参数: {params}")
        return {"success": True, "message": "发送成功"}
