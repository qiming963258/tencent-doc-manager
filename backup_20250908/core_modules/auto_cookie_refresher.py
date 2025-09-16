#!/usr/bin/env python3
"""
自动Cookie获取服务 - 用于定期刷新腾讯文档认证
"""

import asyncio
import json
import logging
from pathlib import Path
from playwright.async_api import async_playwright
from smart_cookie_manager import SmartCookieManager

logger = logging.getLogger(__name__)

class AutoCookieRefresher:
    """自动Cookie刷新服务"""
    
    def __init__(self, config_dir: str = "/root/projects/tencent-doc-manager/config"):
        self.config_dir = Path(config_dir)
        self.cookie_manager = SmartCookieManager(config_dir)
        
        # 刷新配置
        self.refresh_config = {
            "enabled": True,
            "check_interval": 14400,  # 4小时检查
            "login_timeout": 60,  # 登录超时60秒
            "max_attempts": 3,
            "success_cooldown": 86400,  # 成功后24小时内不再尝试
        }
        
        # 腾讯账号配置 (需要用户配置)
        self.account_config_file = self.config_dir / "account_config.json"
        
    def load_account_config(self) -> dict:
        """加载账号配置"""
        try:
            if self.account_config_file.exists():
                with open(self.account_config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # 创建示例配置
                example_config = {
                    "accounts": [
                        {
                            "username": "your_qq_number",
                            "password": "your_password", 
                            "enabled": False,
                            "note": "主账号 - 请填写真实信息后启用"
                        }
                    ],
                    "login_method": "qr_code",  # qr_code, password
                    "security_note": "密码将被加密存储，但建议使用二维码登录"
                }
                
                with open(self.account_config_file, 'w', encoding='utf-8') as f:
                    json.dump(example_config, f, ensure_ascii=False, indent=2)
                
                logger.info(f"已创建示例配置文件: {self.account_config_file}")
                return example_config
                
        except Exception as e:
            logger.error(f"加载账号配置失败: {e}")
            return {"accounts": []}
    
    async def refresh_cookies_via_browser(self) -> bool:
        """通过浏览器自动登录获取新Cookie"""
        try:
            async with async_playwright() as p:
                # 启动浏览器
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
                
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                
                page = await context.new_page()
                
                # 访问腾讯文档登录页面
                await page.goto('https://docs.qq.com/desktop', timeout=30000)
                await page.wait_for_timeout(3000)
                
                # 检查是否已经登录
                if await self._check_login_status(page):
                    logger.info("✅ 页面已登录状态")
                    cookies = await self._extract_cookies(context)
                    success = self._save_extracted_cookies(cookies)
                    await browser.close()
                    return success
                
                # 尝试自动登录流程
                account_config = self.load_account_config()
                login_method = account_config.get("login_method", "qr_code")
                
                if login_method == "qr_code":
                    success = await self._login_via_qr_code(page)
                else:
                    success = await self._login_via_password(page, account_config)
                
                if success:
                    # 等待登录完成
                    await page.wait_for_url("**/desktop**", timeout=30000)
                    await page.wait_for_timeout(5000)
                    
                    # 提取Cookie
                    cookies = await self._extract_cookies(context)
                    success = self._save_extracted_cookies(cookies)
                    
                await browser.close()
                return success
                
        except Exception as e:
            logger.error(f"❌ 浏览器刷新Cookie失败: {e}")
            return False
    
    async def _check_login_status(self, page) -> bool:
        """检查登录状态"""
        try:
            # 检查是否存在用户头像或用户信息
            user_selectors = [
                '.user-avatar',
                '.user-info', 
                '[data-testid="user"]',
                '.header-user'
            ]
            
            for selector in user_selectors:
                if await page.query_selector(selector):
                    return True
            
            # 检查URL是否包含登录后的特征
            url = page.url
            if 'desktop' in url and 'login' not in url:
                return True
                
            return False
            
        except Exception:
            return False
    
    async def _extract_cookies(self, context) -> list:
        """提取浏览器Cookie"""
        try:
            cookies = await context.cookies()
            
            # 过滤腾讯文档相关Cookie
            tencent_cookies = []
            important_names = ['uid', 'DOC_SID', 'SID', 'fingerprint', 'loginTime', 'uin']
            
            for cookie in cookies:
                if (cookie['domain'].endswith('.qq.com') or 
                    cookie['domain'].endswith('docs.qq.com') or
                    cookie['name'] in important_names):
                    tencent_cookies.append(cookie)
            
            logger.info(f"✅ 提取到{len(tencent_cookies)}个腾讯相关Cookie")
            return tencent_cookies
            
        except Exception as e:
            logger.error(f"❌ 提取Cookie失败: {e}")
            return []
    
    def _save_extracted_cookies(self, cookies: list) -> bool:
        """保存提取的Cookie"""
        try:
            if not cookies:
                return False
            
            # 转换为Cookie字符串格式
            cookie_pairs = []
            for cookie in cookies:
                cookie_pairs.append(f"{cookie['name']}={cookie['value']}")
            
            cookie_string = "; ".join(cookie_pairs)
            
            # 使用Cookie管理器保存
            success = self.cookie_manager.save_cookies(
                cookie_string, 
                source="auto_browser_refresh"
            )
            
            if success:
                logger.info(f"✅ 自动刷新Cookie成功，共{len(cookies)}个")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ 保存提取Cookie失败: {e}")
            return False
    
    async def _login_via_qr_code(self, page) -> bool:
        """二维码登录方式"""
        try:
            logger.info("🔍 尝试二维码登录...")
            
            # 查找二维码登录按钮或二维码
            qr_selectors = [
                '.qr-code',
                '[data-testid="qr-login"]',
                'img[alt*="二维码"]',
                '.login-qr'
            ]
            
            for selector in qr_selectors:
                qr_element = await page.query_selector(selector)
                if qr_element:
                    logger.info(f"找到二维码元素: {selector}")
                    
                    # 等待用户扫码 (这里需要人工干预)
                    logger.info("⏳ 等待用户扫码登录 (60秒超时)...")
                    
                    try:
                        # 等待登录成功的信号
                        await page.wait_for_url("**/desktop**", timeout=60000)
                        logger.info("✅ 二维码登录成功")
                        return True
                    except:
                        logger.warning("⏰ 二维码登录超时")
                        return False
            
            logger.warning("❌ 未找到二维码登录选项")
            return False
            
        except Exception as e:
            logger.error(f"❌ 二维码登录失败: {e}")
            return False
    
    async def _login_via_password(self, page, account_config: dict) -> bool:
        """密码登录方式"""
        try:
            accounts = account_config.get("accounts", [])
            enabled_accounts = [acc for acc in accounts if acc.get("enabled", False)]
            
            if not enabled_accounts:
                logger.warning("❌ 无可用账号配置")
                return False
            
            account = enabled_accounts[0]  # 使用第一个启用的账号
            
            # 查找用户名和密码输入框
            username_input = await page.query_selector('input[type="text"], input[name*="user"], input[placeholder*="账号"]')
            password_input = await page.query_selector('input[type="password"]')
            
            if not username_input or not password_input:
                logger.warning("❌ 未找到登录输入框")
                return False
            
            # 输入账号密码
            await username_input.fill(account["username"])
            await password_input.fill(account["password"])
            
            # 查找登录按钮
            login_button = await page.query_selector('button[type="submit"], button:has-text("登录"), .login-btn')
            if login_button:
                await login_button.click()
                
                # 等待登录结果
                try:
                    await page.wait_for_url("**/desktop**", timeout=30000)
                    logger.info("✅ 密码登录成功")
                    return True
                except:
                    logger.warning("❌ 密码登录失败或超时")
                    return False
            else:
                logger.warning("❌ 未找到登录按钮")
                return False
                
        except Exception as e:
            logger.error(f"❌ 密码登录异常: {e}")
            return False
    
    async def run_refresh_service(self):
        """运行Cookie刷新服务"""
        logger.info("🚀 启动Cookie自动刷新服务...")
        
        while self.refresh_config["enabled"]:
            try:
                # 检查是否需要刷新
                if self.cookie_manager.need_refresh():
                    logger.info("🔄 检测到Cookie需要刷新...")
                    
                    # 验证当前Cookie
                    current_cookie = self.cookie_manager.get_cookie_string()
                    if current_cookie:
                        is_valid, message = await self.cookie_manager.validate_cookies()
                        logger.info(f"当前Cookie验证: {message}")
                        
                        if is_valid:
                            logger.info("✅ 当前Cookie仍然有效，跳过刷新")
                        else:
                            # 执行刷新
                            success = await self.refresh_cookies_via_browser()
                            if success:
                                logger.info("✅ Cookie刷新成功")
                            else:
                                logger.error("❌ Cookie刷新失败，将在下次循环重试")
                    else:
                        logger.warning("⚠️ 无当前Cookie，尝试获取新的")
                        await self.refresh_cookies_via_browser()
                else:
                    logger.info("✅ Cookie状态良好，无需刷新")
                
                # 等待下次检查
                await asyncio.sleep(self.refresh_config["check_interval"])
                
            except KeyboardInterrupt:
                logger.info("👋 接收到中断信号，停止Cookie刷新服务")
                break
            except Exception as e:
                logger.error(f"❌ Cookie刷新服务异常: {e}")
                await asyncio.sleep(300)  # 异常后等待5分钟再重试

# CLI接口
async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="腾讯文档Cookie自动管理")
    parser.add_argument("--daemon", action="store_true", help="后台服务模式")
    parser.add_argument("--refresh", action="store_true", help="立即刷新Cookie")
    parser.add_argument("--status", action="store_true", help="查看Cookie状态")
    
    args = parser.parse_args()
    
    refresher = AutoCookieRefresher()
    
    if args.status:
        status = refresher.cookie_manager.get_status()
        print(json.dumps(status, ensure_ascii=False, indent=2))
    
    elif args.refresh:
        success = await refresher.refresh_cookies_via_browser()
        print(f"刷新结果: {'✅ 成功' if success else '❌ 失败'}")
    
    elif args.daemon:
        await refresher.run_refresh_service()
    
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())