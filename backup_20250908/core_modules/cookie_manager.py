#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生产级Cookie管理器
实现Cookie自动刷新、加密存储、多域名支持、失败恢复机制
解决系统最大单点故障问题
"""

import os
import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
from playwright.async_api import async_playwright

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CookieManager:
    """生产级Cookie管理器"""
    
    def __init__(self, config_dir: str = None):
        """初始化Cookie管理器"""
        self.config_dir = config_dir or "/root/projects/tencent-doc-manager/config"
        self.cookie_file = os.path.join(self.config_dir, "cookies_encrypted.json")
        self.backup_file = os.path.join(self.config_dir, "cookies_backup.json") 
        
        # 确保目录存在
        os.makedirs(self.config_dir, exist_ok=True)
        
        # 初始化加密
        self._init_encryption()
        
        # Cookie配置
        self.domains = ['docs.qq.com', '.docs.qq.com', 'qq.com', '.qq.com']
        self.refresh_threshold = 30 * 60  # 30分钟阈值
        self.max_retries = 3
        self.retry_delay = 5  # 5秒重试间隔
        
        # Cookie池
        self.primary_cookies = None
        self.backup_cookies = []
        self.last_validation = None
        self.validation_interval = 5 * 60  # 5分钟验证间隔
        
    def _init_encryption(self):
        """初始化加密系统"""
        try:
            # 生成密钥（基于系统特征）
            system_info = f"{os.path.expanduser('~')}-tencent-cookie-manager"
            password = system_info.encode()
            
            salt = b"tencent_doc_cookie_salt_2025"
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password))
            self.cipher_suite = Fernet(key)
            logger.info("✅ Cookie加密系统初始化成功")
        except Exception as e:
            logger.error(f"❌ Cookie加密系统初始化失败: {e}")
            raise
    
    def _encrypt_data(self, data: str) -> str:
        """加密数据"""
        try:
            return self.cipher_suite.encrypt(data.encode()).decode()
        except Exception as e:
            logger.error(f"数据加密失败: {e}")
            raise
    
    def _decrypt_data(self, encrypted_data: str) -> str:
        """解密数据"""
        try:
            return self.cipher_suite.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            logger.error(f"数据解密失败: {e}")
            raise
    
    async def load_cookies(self) -> Dict[str, any]:
        """加载Cookie配置"""
        try:
            if os.path.exists(self.cookie_file):
                with open(self.cookie_file, 'r', encoding='utf-8') as f:
                    encrypted_config = json.load(f)
                
                # 解密Cookie数据
                if 'encrypted_cookies' in encrypted_config:
                    cookie_data = self._decrypt_data(encrypted_config['encrypted_cookies'])
                    config = json.loads(cookie_data)
                    
                    self.primary_cookies = config.get('primary_cookies')
                    self.backup_cookies = config.get('backup_cookies', [])
                    self.last_validation = config.get('last_validation')
                    
                    logger.info(f"✅ 成功加载加密Cookie配置，备用Cookie数量: {len(self.backup_cookies)}")
                    return config
                else:
                    # 兼容旧格式
                    logger.warning("⚠️ 检测到未加密Cookie文件，将自动升级加密")
                    await self._migrate_old_cookies()
                    return await self.load_cookies()
            else:
                # 尝试迁移旧Cookie文件
                old_file = os.path.join(self.config_dir, "cookies.json")
                if os.path.exists(old_file):
                    logger.info("🔄 检测到旧Cookie文件，开始迁移...")
                    await self._migrate_old_cookies()
                    return await self.load_cookies()
                else:
                    logger.warning("⚠️ 未找到Cookie配置文件，需要初始化")
                    return {}
        except Exception as e:
            logger.error(f"❌ 加载Cookie配置失败: {e}")
            return {}
    
    async def _migrate_old_cookies(self):
        """迁移旧Cookie文件到加密格式"""
        try:
            old_file = os.path.join(self.config_dir, "cookies.json")
            if os.path.exists(old_file):
                with open(old_file, 'r', encoding='utf-8') as f:
                    old_config = json.load(f)
                
                # 转换为新格式
                new_config = {
                    'primary_cookies': old_config.get('current_cookies'),
                    'backup_cookies': [],
                    'last_validation': old_config.get('last_test_time'),
                    'is_valid': old_config.get('is_valid', False),
                    'migration_time': datetime.now().isoformat()
                }
                
                # 保存加密文件
                await self.save_cookies(new_config)
                
                # 备份旧文件
                backup_old = old_file + ".backup_" + str(int(time.time()))
                os.rename(old_file, backup_old)
                
                logger.info(f"✅ Cookie文件迁移完成，旧文件备份为: {backup_old}")
            else:
                logger.warning("⚠️ 未找到旧Cookie文件")
        except Exception as e:
            logger.error(f"❌ Cookie文件迁移失败: {e}")
    
    async def save_cookies(self, config: Dict[str, any]):
        """保存Cookie配置（加密）"""
        try:
            # 更新内存状态
            self.primary_cookies = config.get('primary_cookies')
            self.backup_cookies = config.get('backup_cookies', [])
            self.last_validation = datetime.now().isoformat()
            
            # 准备加密数据
            config['last_validation'] = self.last_validation
            cookie_data = json.dumps(config, ensure_ascii=False, indent=2)
            encrypted_cookies = self._encrypt_data(cookie_data)
            
            # 保存加密文件
            encrypted_config = {
                'encrypted_cookies': encrypted_cookies,
                'last_update': datetime.now().isoformat(),
                'encryption_version': '1.0'
            }
            
            with open(self.cookie_file, 'w', encoding='utf-8') as f:
                json.dump(encrypted_config, f, ensure_ascii=False, indent=2)
            
            # 创建备份
            with open(self.backup_file, 'w', encoding='utf-8') as f:
                json.dump(encrypted_config, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Cookie配置保存成功，加密存储到: {self.cookie_file}")
        except Exception as e:
            logger.error(f"❌ Cookie配置保存失败: {e}")
            raise
    
    async def validate_cookies(self, cookies_string: str) -> Tuple[bool, str]:
        """验证Cookie有效性"""
        try:
            logger.info("🔍 开始验证Cookie有效性...")
            
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # 设置Cookie
            cookie_list = await self._parse_cookies_to_list(cookies_string)
            await context.add_cookies(cookie_list)
            
            # 测试访问腾讯文档
            try:
                response = await page.goto('https://docs.qq.com/desktop', timeout=15000)
                await page.wait_for_timeout(3000)
                
                # 检查登录状态
                is_logged_in = await page.evaluate('''() => {
                    const text = document.body.textContent.toLowerCase();
                    return !text.includes('登录') || text.includes('已登录') || 
                           document.querySelector('.user-info, [class*="user"][class*="name"], [class*="avatar"]');
                }''')
                
                await browser.close()
                await playwright.stop()
                
                if is_logged_in:
                    logger.info("✅ Cookie验证成功，用户已登录")
                    return True, "Cookie有效，用户已登录"
                else:
                    logger.warning("⚠️ Cookie可能已失效，检测到登录页面")
                    return False, "Cookie已失效，需要重新登录"
                    
            except Exception as page_error:
                await browser.close()
                await playwright.stop()
                logger.error(f"页面访问失败: {page_error}")
                return False, f"页面访问失败: {str(page_error)}"
                
        except Exception as e:
            logger.error(f"❌ Cookie验证过程失败: {e}")
            return False, f"Cookie验证失败: {str(e)}"
    
    async def _parse_cookies_to_list(self, cookies_string: str) -> List[Dict]:
        """将Cookie字符串解析为列表格式"""
        cookie_list = []
        
        if not cookies_string:
            return cookie_list
        
        for cookie_str in cookies_string.split(';'):
            if '=' in cookie_str:
                name, value = cookie_str.strip().split('=', 1)
                
                # 为每个域添加Cookie
                for domain in self.domains:
                    cookie_list.append({
                        'name': name,
                        'value': value,
                        'domain': domain,
                        'path': '/',
                        'httpOnly': False,
                        'secure': True,
                        'sameSite': 'None'
                    })
        
        return cookie_list
    
    async def get_valid_cookies(self) -> Optional[str]:
        """获取有效的Cookie"""
        try:
            # 加载当前配置
            await self.load_cookies()
            
            # 检查是否需要验证
            if self._should_validate():
                logger.info("🔄 开始Cookie有效性检查...")
                
                # 验证主Cookie
                if self.primary_cookies:
                    is_valid, message = await self.validate_cookies(self.primary_cookies)
                    if is_valid:
                        logger.info("✅ 主Cookie验证通过")
                        return self.primary_cookies
                    else:
                        logger.warning(f"⚠️ 主Cookie验证失败: {message}")
                
                # 尝试备用Cookie
                for i, backup_cookie in enumerate(self.backup_cookies):
                    logger.info(f"🔄 尝试备用Cookie {i+1}/{len(self.backup_cookies)}")
                    is_valid, message = await self.validate_cookies(backup_cookie)
                    if is_valid:
                        logger.info(f"✅ 备用Cookie {i+1} 验证通过，提升为主Cookie")
                        
                        # 将有效的备用Cookie提升为主Cookie
                        old_primary = self.primary_cookies
                        self.primary_cookies = backup_cookie
                        
                        # 重组备用Cookie列表
                        new_backup = [old_primary] if old_primary else []
                        new_backup.extend([c for j, c in enumerate(self.backup_cookies) if j != i])
                        self.backup_cookies = new_backup[:5]  # 最多保留5个备用
                        
                        # 保存更新后的配置
                        await self.save_cookies({
                            'primary_cookies': self.primary_cookies,
                            'backup_cookies': self.backup_cookies,
                            'is_valid': True
                        })
                        
                        return self.primary_cookies
                    else:
                        logger.warning(f"⚠️ 备用Cookie {i+1} 验证失败: {message}")
                
                # 所有Cookie都无效
                logger.error("❌ 所有Cookie都已失效，需要手动更新")
                return None
            else:
                # 不需要验证，返回主Cookie
                return self.primary_cookies
                
        except Exception as e:
            logger.error(f"❌ 获取有效Cookie失败: {e}")
            return None
    
    def _should_validate(self) -> bool:
        """判断是否需要验证Cookie"""
        if not self.last_validation:
            return True
        
        try:
            last_time = datetime.fromisoformat(self.last_validation.replace('Z', '+00:00'))
            now = datetime.now()
            
            # 如果超过验证间隔，需要验证
            if (now - last_time).total_seconds() > self.validation_interval:
                return True
        except Exception:
            return True
        
        return False
    
    async def add_backup_cookie(self, cookie_string: str) -> bool:
        """添加备用Cookie"""
        try:
            # 验证新Cookie
            is_valid, message = await self.validate_cookies(cookie_string)
            if not is_valid:
                logger.warning(f"⚠️ 备用Cookie无效，不添加: {message}")
                return False
            
            # 加载当前配置
            await self.load_cookies()
            
            # 添加到备用列表
            if cookie_string not in self.backup_cookies:
                self.backup_cookies.append(cookie_string)
                # 限制备用Cookie数量
                self.backup_cookies = self.backup_cookies[-5:]
                
                # 保存配置
                await self.save_cookies({
                    'primary_cookies': self.primary_cookies,
                    'backup_cookies': self.backup_cookies,
                    'is_valid': True
                })
                
                logger.info(f"✅ 备用Cookie添加成功，当前备用数量: {len(self.backup_cookies)}")
                return True
            else:
                logger.info("ℹ️ Cookie已存在于备用列表中")
                return True
                
        except Exception as e:
            logger.error(f"❌ 添加备用Cookie失败: {e}")
            return False
    
    async def update_primary_cookie(self, cookie_string: str) -> bool:
        """更新主Cookie"""
        try:
            # 验证新Cookie
            is_valid, message = await self.validate_cookies(cookie_string)
            if not is_valid:
                logger.error(f"❌ 新Cookie无效: {message}")
                return False
            
            # 加载当前配置
            await self.load_cookies()
            
            # 将旧主Cookie添加到备用列表
            if self.primary_cookies and self.primary_cookies != cookie_string:
                if self.primary_cookies not in self.backup_cookies:
                    self.backup_cookies.insert(0, self.primary_cookies)
                    self.backup_cookies = self.backup_cookies[:5]  # 限制数量
            
            # 更新主Cookie
            self.primary_cookies = cookie_string
            
            # 保存配置
            await self.save_cookies({
                'primary_cookies': self.primary_cookies,
                'backup_cookies': self.backup_cookies,
                'is_valid': True
            })
            
            logger.info("✅ 主Cookie更新成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 更新主Cookie失败: {e}")
            return False
    
    async def get_health_status(self) -> Dict[str, any]:
        """获取Cookie管理器健康状态"""
        try:
            status = {
                'healthy': False,
                'primary_cookie_valid': False,
                'backup_cookies_count': len(self.backup_cookies),
                'last_validation': self.last_validation,
                'encryption_enabled': True,
                'errors': []
            }
            
            # 检查主Cookie
            if self.primary_cookies:
                is_valid, message = await self.validate_cookies(self.primary_cookies)
                status['primary_cookie_valid'] = is_valid
                if not is_valid:
                    status['errors'].append(f"主Cookie无效: {message}")
            else:
                status['errors'].append("未设置主Cookie")
            
            # 整体健康状态
            status['healthy'] = status['primary_cookie_valid'] or status['backup_cookies_count'] > 0
            
            return status
            
        except Exception as e:
            logger.error(f"❌ 获取健康状态失败: {e}")
            return {
                'healthy': False,
                'error': str(e),
                'encryption_enabled': True
            }


# 单例模式
_cookie_manager_instance = None

def get_cookie_manager(config_dir: str = None) -> CookieManager:
    """获取Cookie管理器单例"""
    global _cookie_manager_instance
    if _cookie_manager_instance is None:
        _cookie_manager_instance = CookieManager(config_dir)
    return _cookie_manager_instance


# 测试代码
async def test_cookie_manager():
    """测试Cookie管理器功能"""
    try:
        print("=== Cookie管理器功能测试 ===")
        
        manager = get_cookie_manager()
        
        # 测试健康状态
        print("\n1. 健康状态检查:")
        health = await manager.get_health_status()
        print(f"健康状态: {health}")
        
        # 测试获取Cookie
        print("\n2. 获取有效Cookie:")
        valid_cookie = await manager.get_valid_cookies()
        if valid_cookie:
            print(f"✅ 获取到有效Cookie: {valid_cookie[:50]}...")
        else:
            print("❌ 未获取到有效Cookie")
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(test_cookie_manager())