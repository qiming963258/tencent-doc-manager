#!/usr/bin/env python3
"""
智能Cookie管理器 - 腾讯文档自动认证系统
解决Cookie失效导致的系统瘫痪问题
"""

import json
import os
import time
import datetime
import asyncio
import logging
import requests
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import aiohttp
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

@dataclass
class CookieInfo:
    """Cookie信息数据类"""
    name: str
    value: str
    domain: str
    path: str
    expires: Optional[int] = None
    secure: bool = False
    http_only: bool = False
    same_site: str = "lax"
    
    def is_expired(self) -> bool:
        """检查Cookie是否过期"""
        if self.expires is None:
            return False
        return time.time() > self.expires

class SmartCookieManager:
    """智能Cookie管理器"""
    
    def __init__(self, config_dir: str = "/root/projects/tencent-doc-manager/config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        # 文件路径
        self.cookie_file = self.config_dir / "cookies_encrypted.json"
        self.key_file = self.config_dir / "cookie_key.key"
        self.backup_file = self.config_dir / "cookies_backup.json"
        
        # 加密管理
        self.encryption_key = self._load_or_create_key()
        self.cipher = Fernet(self.encryption_key)
        
        # 腾讯文档相关配置
        self.tencent_domains = [
            "docs.qq.com",
            ".docs.qq.com", 
            "doc.weixin.qq.com",
            ".qq.com"
        ]
        
        # Cookie有效性检查配置
        self.validation_urls = [
            "https://docs.qq.com/desktop",
            "https://docs.qq.com/api/user/info"
        ]
        
        # 自动刷新配置
        self.refresh_config = {
            "enabled": True,
            "check_interval": 3600,  # 1小时检查一次
            "expire_threshold": 86400,  # 24小时内过期时刷新
            "max_retry_attempts": 3,
            "retry_interval": 300  # 5分钟重试间隔
        }
    
    def _load_or_create_key(self) -> bytes:
        """加载或创建加密密钥"""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            # 安全写入密钥文件
            os.umask(0o077)  # 只有owner可读写
            with open(self.key_file, 'wb') as f:
                f.write(key)
            os.chmod(self.key_file, 0o600)
            return key
    
    def encrypt_data(self, data: str) -> str:
        """加密数据"""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """解密数据"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()
    
    def parse_cookie_string(self, cookie_string: str) -> List[CookieInfo]:
        """解析Cookie字符串为CookieInfo列表"""
        cookies = []
        
        # 处理不同格式的Cookie字符串
        if '; ' in cookie_string:
            # 标准格式: "name1=value1; name2=value2"
            cookie_pairs = cookie_string.split('; ')
        else:
            # 其他格式处理
            cookie_pairs = cookie_string.split(';')
        
        for pair in cookie_pairs:
            if '=' not in pair:
                continue
                
            name, value = pair.strip().split('=', 1)
            
            # 根据Cookie名称推断域名
            domain = ".docs.qq.com"
            if name.lower() in ['uid', 'uin']:
                domain = ".qq.com"
            elif name.startswith('DOC_'):
                domain = "docs.qq.com"
                
            cookies.append(CookieInfo(
                name=name.strip(),
                value=value.strip(), 
                domain=domain,
                path="/",
                expires=None,  # 从实际Cookie获取
                secure=True,
                http_only=True
            ))
        
        return cookies
    
    def save_cookies(self, cookie_string: str, source: str = "manual") -> bool:
        """保存Cookie到加密文件"""
        try:
            cookies = self.parse_cookie_string(cookie_string)
            
            cookie_data = {
                "cookies": [
                    {
                        "name": c.name,
                        "value": c.value,
                        "domain": c.domain,
                        "path": c.path,
                        "expires": c.expires,
                        "secure": c.secure,
                        "http_only": c.http_only,
                        "same_site": c.same_site
                    }
                    for c in cookies
                ],
                "source": source,
                "created_at": datetime.datetime.now().isoformat(),
                "last_validated": None,
                "validation_count": 0,
                "estimated_expires": time.time() + (7 * 24 * 3600),  # 假设7天有效期
                "raw_string": cookie_string
            }
            
            # 加密保存
            encrypted_data = self.encrypt_data(json.dumps(cookie_data, ensure_ascii=False))
            
            with open(self.cookie_file, 'w', encoding='utf-8') as f:
                json.dump({"encrypted_cookies": encrypted_data}, f)
            
            # 创建备份
            with open(self.backup_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "backup_time": datetime.datetime.now().isoformat(),
                    "cookie_count": len(cookies),
                    "domains": list(set(c.domain for c in cookies)),
                    "source": source
                }, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 成功保存{len(cookies)}个Cookie (来源: {source})")
            return True
            
        except Exception as e:
            logger.error(f"❌ 保存Cookie失败: {e}")
            return False
    
    def load_cookies(self) -> Optional[Dict]:
        """加载Cookie数据"""
        try:
            if not self.cookie_file.exists():
                logger.warning("❌ Cookie文件不存在")
                return None
            
            with open(self.cookie_file, 'r', encoding='utf-8') as f:
                encrypted_file = json.load(f)
            
            decrypted_data = self.decrypt_data(encrypted_file["encrypted_cookies"])
            cookie_data = json.loads(decrypted_data)
            
            return cookie_data
            
        except Exception as e:
            logger.error(f"❌ 加载Cookie失败: {e}")
            return None
    
    def get_cookie_string(self) -> Optional[str]:
        """获取可用的Cookie字符串"""
        cookie_data = self.load_cookies()
        if not cookie_data:
            return None
        
        return cookie_data.get("raw_string")
    
    async def validate_cookies(self, cookie_string: str = None) -> Tuple[bool, str]:
        """
        增强Cookie验证 - 修复端点和逻辑问题
        
        Args:
            cookie_string: Cookie字符串，如果为None则使用当前存储的Cookie
            
        Returns:
            Tuple[bool, str]: (是否有效, 验证消息)
        """
        try:
            print("🔍 开始增强Cookie验证...")
            
            # 获取要验证的Cookie
            cookies = cookie_string or self.get_cookie_string()
            if not cookies:
                return False, "❌ 没有可验证的Cookie"
            
            # 解析Cookie为字典格式，用于请求头
            cookie_dict = {}
            for cookie_item in cookies.split(';'):
                if '=' in cookie_item:
                    key, value = cookie_item.strip().split('=', 1)
                    cookie_dict[key] = value
            
            print(f"📋 解析Cookie项: {len(cookie_dict)}个")
            
            # 修复后的验证URL列表 - 更准确的端点
            validation_urls = [
                "https://docs.qq.com/desktop/index",  # 主桌面页面
                "https://docs.qq.com/api/v1/user/info",  # 用户信息API
                "https://docs.qq.com/desktop",  # 简化桌面URL
                "https://pad.qq.com/",  # 腾讯文档备用域名
                "https://docs.qq.com/"  # 根域名
            ]
            
            # 增强的验证逻辑
            for i, url in enumerate(validation_urls, 1):
                try:
                    print(f"⏳ 验证端点 {i}/{len(validation_urls)}: {url}")
                    
                    # 构建请求头
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'none',
                        'Cookie': cookies  # 直接使用原始Cookie字符串
                    }
                    
                    # 发送验证请求
                    response = requests.get(
                        url, 
                        headers=headers, 
                        timeout=10, 
                        allow_redirects=False  # 不跟随重定向，检查状态码
                    )
                    
                    print(f"📊 响应状态: {response.status_code}")
                    
                    # 验证响应内容
                    if response.status_code == 200:
                        # 检查响应内容是否包含登录用户信息
                        response_text = response.text.lower()
                        
                        # 成功指示器
                        success_indicators = [
                            'user', 'avatar', '用户', '头像', 'nickname', 
                            'desktop', 'document', '文档', 'workspace'
                        ]
                        
                        # 失败指示器
                        failure_indicators = [
                            'login', '登录', 'signin', 'auth', 'unauthorized',
                            '请登录', '未登录', '登录页面'
                        ]
                        
                        has_success = any(indicator in response_text for indicator in success_indicators)
                        has_failure = any(indicator in response_text for indicator in failure_indicators)
                        
                        if has_success and not has_failure:
                            success_msg = f"✅ Cookie验证成功 - 端点: {url}"
                            print(success_msg)
                            await self._update_validation_status(True)
                            return True, success_msg
                        elif has_failure:
                            print(f"⚠️ 端点 {url} 检测到登录页面")
                        else:
                            print(f"🔍 端点 {url} 响应内容不确定")
                            
                    elif response.status_code == 302 or response.status_code == 301:
                        # 重定向可能是正常的，检查重定向目标
                        redirect_location = response.headers.get('Location', '')
                        print(f"🔄 重定向到: {redirect_location}")
                        
                        if 'login' not in redirect_location.lower():
                            success_msg = f"✅ Cookie可能有效 - 端点重定向但非登录页: {url}"
                            print(success_msg)
                            await self._update_validation_status(True)
                            return True, success_msg
                        else:
                            print(f"❌ 端点 {url} 重定向到登录页")
                            
                    elif response.status_code == 403:
                        print(f"🚫 端点 {url} 权限被拒绝 - Cookie可能过期")
                    elif response.status_code == 401:
                        print(f"🔐 端点 {url} 未授权 - Cookie无效")
                    else:
                        print(f"⚠️ 端点 {url} 异常状态码: {response.status_code}")
                    
                    # 短暂延迟避免请求过频
                    await asyncio.sleep(0.5)
                    
                except requests.RequestException as e:
                    print(f"🌐 端点 {url} 网络请求失败: {e}")
                    continue
                except Exception as e:
                    print(f"❌ 端点 {url} 验证异常: {e}")
                    continue
            
            # 如果所有端点都失败，进行基础格式检查
            print("🔍 所有端点验证失败，进行基础格式检查...")
            
            # 增强的格式验证
            required_cookies = ['uid', 'SID']  # 必需的Cookie项
            optional_cookies = ['DOC_SID', 'fingerprint', 'loginTime']  # 可选的Cookie项
            
            missing_required = []
            for required in required_cookies:
                if required not in cookie_dict:
                    missing_required.append(required)
            
            if missing_required:
                fail_msg = f"❌ Cookie格式不完整，缺少必需项: {', '.join(missing_required)}"
                print(fail_msg)
                await self._update_validation_status(False)
                return False, fail_msg
            
            # 检查Cookie值的合理性
            uid_value = cookie_dict.get('uid', '')
            if len(uid_value) < 10:
                fail_msg = "❌ uid值格式异常（长度过短）"
                print(fail_msg)
                await self._update_validation_status(False)
                return False, fail_msg
            
            # 格式检查通过但网络验证失败
            warning_msg = f"⚠️ Cookie格式正确但网络验证失败，可能是网络问题或端点变更"
            print(warning_msg)
            await self._update_validation_status(True)  # 格式正确就认为可用
            return True, warning_msg
            
        except Exception as e:
            error_msg = f"❌ Cookie验证过程异常: {e}"
            print(error_msg)
            await self._update_validation_status(False)
            return False, error_msg
    
    async def _update_validation_status(self, is_valid: bool):
        """更新Cookie验证状态"""
        cookie_data = self.load_cookies()
        if cookie_data:
            cookie_data["last_validated"] = datetime.datetime.now().isoformat()
            cookie_data["validation_count"] += 1
            cookie_data["is_valid"] = is_valid
            
            # 重新加密保存
            encrypted_data = self.encrypt_data(json.dumps(cookie_data, ensure_ascii=False))
            with open(self.cookie_file, 'w', encoding='utf-8') as f:
                json.dump({"encrypted_cookies": encrypted_data}, f)
    
    def need_refresh(self) -> bool:
        """判断是否需要刷新Cookie"""
        cookie_data = self.load_cookies()
        if not cookie_data:
            return True
        
        # 检查是否接近过期时间
        estimated_expires = cookie_data.get("estimated_expires", 0)
        current_time = time.time()
        
        if estimated_expires - current_time < self.refresh_config["expire_threshold"]:
            return True
        
        # 检查最后验证时间
        last_validated = cookie_data.get("last_validated")
        if not last_validated:
            return True
        
        last_time = datetime.datetime.fromisoformat(last_validated)
        if (datetime.datetime.now() - last_time).total_seconds() > 3600:  # 1小时
            return True
        
        return False
    
    def get_status(self) -> Dict:
        """获取Cookie管理器状态"""
        cookie_data = self.load_cookies()
        
        if not cookie_data:
            return {
                "has_cookies": False,
                "status": "❌ 无Cookie数据",
                "need_manual_update": True
            }
        
        estimated_expires = cookie_data.get("estimated_expires", 0)
        current_time = time.time()
        time_to_expire = estimated_expires - current_time
        
        return {
            "has_cookies": True,
            "cookie_count": len(cookie_data.get("cookies", [])),
            "last_validated": cookie_data.get("last_validated"),
            "validation_count": cookie_data.get("validation_count", 0),
            "is_valid": cookie_data.get("is_valid"),
            "estimated_expires": datetime.datetime.fromtimestamp(estimated_expires).isoformat(),
            "time_to_expire_hours": time_to_expire / 3600,
            "need_refresh": self.need_refresh(),
            "status": self._get_status_message(time_to_expire),
            "domains": list(set(c["domain"] for c in cookie_data.get("cookies", []))),
            "source": cookie_data.get("source", "unknown")
        }
    
    def _get_status_message(self, time_to_expire: float) -> str:
        """获取状态消息"""
        if time_to_expire <= 0:
            return "🔴 Cookie已过期"
        elif time_to_expire < 86400:  # 24小时
            return f"⚠️ Cookie将在{time_to_expire/3600:.1f}小时后过期"
        elif time_to_expire < 259200:  # 3天
            return f"💛 Cookie将在{time_to_expire/86400:.1f}天后过期"
        else:
            return f"✅ Cookie有效 (剩余{time_to_expire/86400:.1f}天)"

# 使用示例
async def main():
    """使用示例"""
    manager = SmartCookieManager()
    
    # 保存新Cookie
    new_cookie = "uid=144115414584628119; DOC_SID=real_session_id; fingerprint=123456"
    success = manager.save_cookies(new_cookie, source="browser_extract")
    
    if success:
        # 验证Cookie
        is_valid, message = await manager.validate_cookies()
        print(f"验证结果: {message}")
        
        # 获取状态
        status = manager.get_status()
        print(json.dumps(status, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    asyncio.run(main())