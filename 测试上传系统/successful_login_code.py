#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档成功登录代码 - 完整可运行版本
基于enterprise_download_system项目的成功经验
"""

import asyncio
import json
import os
from pathlib import Path
from playwright.async_api import async_playwright

class TencentDocSuccessfulLogin:
    """腾讯文档成功登录实现"""
    
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        print("[初始化] 腾讯文档登录系统")
        
    async def start_browser(self, headless=False):
        """启动浏览器"""
        try:
            self.playwright = await async_playwright().start()
            
            # 浏览器启动配置
            self.browser = await self.playwright.chromium.launch(
                headless=headless,
                args=['--start-maximized', '--no-sandbox']
            )
            
            # 创建上下文
            self.context = await self.browser.new_context(
                accept_downloads=True,
                viewport={'width': 1920, 'height': 1080}
            )
            
            # 创建页面
            self.page = await self.context.new_page()
            print("[成功] 浏览器启动完成")
            return True
            
        except Exception as e:
            print(f"[错误] 浏览器启动失败: {e}")
            return False
    
    def parse_cookies(self, cookie_string):
        """
        解析Cookie字符串 - 核心方法
        关键改进：使用 '; ' 分割，只设置 .docs.qq.com 域
        """
        cookies = []
        
        # 关键：使用 '; ' 而不是 ';'
        for cookie_pair in cookie_string.split('; '):
            if '=' in cookie_pair:
                name, value = cookie_pair.strip().split('=', 1)
                cookies.append({
                    'name': name.strip(),
                    'value': value.strip(),
                    'domain': '.docs.qq.com',  # 关键：只用这个域
                    'path': '/'
                })
        
        return cookies
    
    async def login_with_cookies(self, cookie_string):
        """使用Cookie登录 - 成功实现"""
        try:
            print("\n[开始] Cookie认证流程...")
            
            # 步骤1：解析并添加Cookie
            cookies = self.parse_cookies(cookie_string)
            await self.context.add_cookies(cookies)
            print(f"[信息] 已添加 {len(cookies)} 个Cookies")
            
            # 步骤2：直接访问桌面页面（关键改进）
            print("[访问] 正在访问腾讯文档桌面...")
            await self.page.goto(
                'https://docs.qq.com/desktop/',
                wait_until='domcontentloaded',
                timeout=30000
            )
            
            # 步骤3：充分等待页面加载
            print("[等待] 等待页面完全加载（5秒）...")
            await self.page.wait_for_timeout(5000)
            
            # 步骤4：验证登录状态
            is_logged_in = await self.verify_login_status()
            
            if is_logged_in:
                print("[成功] Cookie认证成功！已登录")
                return True
            else:
                print("[警告] Cookie可能已失效，需要更新")
                return False
                
        except Exception as e:
            print(f"[错误] Cookie登录失败: {e}")
            return False
    
    async def verify_login_status(self):
        """验证登录状态"""
        try:
            # 获取页面标题
            title = await self.page.title()
            print(f"[信息] 页面标题: {title}")
            
            # 检查登录按钮（不应该存在）
            login_btn = await self.page.query_selector('button:has-text("登录")')
            has_login_btn = login_btn is not None
            
            # 检查导入按钮（应该存在）
            import_btn = await self.page.query_selector('.desktop-import-button-pc')
            has_import_btn = import_btn is not None
            
            # 检查用户信息
            user_info = await self.page.query_selector('[class*="avatar"], [class*="user"]')
            has_user_info = user_info is not None
            
            # 打印状态
            print("\n[状态检查]")
            print(f"  - 登录按钮: {'存在' if has_login_btn else '不存在'} (期望：不存在)")
            print(f"  - 导入按钮: {'存在' if has_import_btn else '不存在'} (期望：存在)")
            print(f"  - 用户信息: {'存在' if has_user_info else '不存在'} (期望：存在)")
            
            # 判断登录状态
            is_logged_in = not has_login_btn and (has_import_btn or has_user_info)
            print(f"\n[结果] 登录状态: {'已登录' if is_logged_in else '未登录'}")
            
            return is_logged_in
            
        except Exception as e:
            print(f"[错误] 状态检查失败: {e}")
            return False
    
    async def get_document_list(self):
        """获取文档列表（验证登录是否真正成功）"""
        try:
            print("\n[测试] 尝试获取文档列表...")
            
            # 查找文档元素
            doc_links = await self.page.query_selector_all('a[href*="/doc/"], a[href*="/sheet/"]')
            
            if doc_links:
                print(f"[成功] 找到 {len(doc_links)} 个文档")
                
                # 显示前5个文档
                for i, link in enumerate(doc_links[:5]):
                    text = await link.text_content()
                    if text:
                        print(f"  文档{i+1}: {text.strip()}")
                
                return True
            else:
                print("[信息] 未找到文档（可能是新账号或没有文档）")
                return False
                
        except Exception as e:
            print(f"[错误] 获取文档列表失败: {e}")
            return False
    
    async def cleanup(self):
        """清理资源"""
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
        print("[清理] 浏览器已关闭")

async def main():
    """主函数 - 演示完整登录流程"""
    
    print("="*60)
    print("腾讯文档自动化登录 - 成功版本")
    print("="*60)
    
    # 创建登录实例
    login = TencentDocSuccessfulLogin()
    
    try:
        # 1. 启动浏览器
        print("\n步骤1: 启动浏览器")
        success = await login.start_browser(headless=False)  # 使用可见模式
        if not success:
            return
        
        # 2. 读取Cookie配置
        print("\n步骤2: 读取Cookie配置")
        config_file = Path('config/cookies.json')
        
        if not config_file.exists():
            print("[错误] Cookie配置文件不存在: config/cookies.json")
            print("[提示] 请先手动登录腾讯文档并提取Cookie")
            return
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            cookie_string = config.get('cookie_string', '')
        
        if not cookie_string:
            print("[错误] Cookie字符串为空")
            return
        
        print("[成功] Cookie配置已加载")
        
        # 3. 执行登录
        print("\n步骤3: 执行Cookie登录")
        login_success = await login.login_with_cookies(cookie_string)
        
        if login_success:
            print("\n" + "="*40)
            print("🎉 登录成功！")
            print("="*40)
            
            # 4. 验证：尝试获取文档列表
            await login.get_document_list()
            
            # 5. 等待观察
            print("\n[等待] 保持浏览器打开30秒供观察...")
            await asyncio.sleep(30)
            
        else:
            print("\n" + "="*40)
            print("❌ 登录失败")
            print("="*40)
            print("\n可能的原因：")
            print("1. Cookie已过期（需要重新获取）")
            print("2. Cookie格式不正确")
            print("3. 网络连接问题")
            
    except Exception as e:
        print(f"\n[异常] 发生错误: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # 清理
        await login.cleanup()
        print("\n程序结束")

# Cookie获取说明
def print_cookie_instructions():
    """打印Cookie获取说明"""
    print("""
    ========================================
    如何获取有效的Cookie：
    ========================================
    
    1. 打开Chrome浏览器
    2. 访问 https://docs.qq.com
    3. 使用QQ或微信登录
    4. 按F12打开开发者工具
    5. 切换到Network（网络）标签
    6. 刷新页面
    7. 找到任意docs.qq.com的请求
    8. 在Headers中找到Cookie
    9. 复制完整的Cookie值
    10. 保存到config/cookies.json
    
    Cookie格式示例：
    {
        "cookie_string": "uid=xxx; DOC_SID=xxx; SID=xxx; ..."
    }
    ========================================
    """)

if __name__ == "__main__":
    # 检查配置文件
    if not os.path.exists('config/cookies.json'):
        print_cookie_instructions()
        print("[提示] 请先配置Cookie再运行程序")
    else:
        # 运行主程序
        asyncio.run(main())