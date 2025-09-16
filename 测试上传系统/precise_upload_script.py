#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档精确上传脚本 - 基于提供的按钮位置信息
"""

import asyncio
import json
import os
from pathlib import Path
from playwright.async_api import async_playwright

class TencentDocPreciseUpload:
    """腾讯文档精确上传实现"""
    
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        print("[初始化] 腾讯文档精确上传系统")
        
    async def start_browser(self, headless=False):
        """启动浏览器"""
        try:
            self.playwright = await async_playwright().start()
            
            self.browser = await self.playwright.chromium.launch(
                headless=headless,
                args=['--start-maximized', '--no-sandbox']
            )
            
            self.context = await self.browser.new_context(
                accept_downloads=True,
                viewport={'width': 1920, 'height': 1080}
            )
            
            self.page = await self.context.new_page()
            
            # 设置文件选择器监听
            self.page.on('filechooser', self.handle_file_chooser)
            
            print("[成功] 浏览器启动完成")
            return True
            
        except Exception as e:
            print(f"[错误] 浏览器启动失败: {e}")
            return False
    
    def parse_cookies(self, cookie_string):
        """解析Cookie字符串"""
        cookies = []
        for cookie_pair in cookie_string.split('; '):
            if '=' in cookie_pair:
                name, value = cookie_pair.strip().split('=', 1)
                cookies.append({
                    'name': name.strip(),
                    'value': value.strip(),
                    'domain': '.docs.qq.com',
                    'path': '/'
                })
        return cookies
    
    async def login_with_cookies(self, cookie_string):
        """使用Cookie登录"""
        try:
            print("\n[步骤1] 使用Cookie打开账户首页")
            
            # 添加Cookie
            cookies = self.parse_cookies(cookie_string)
            await self.context.add_cookies(cookies)
            print(f"[信息] 已添加 {len(cookies)} 个Cookies")
            
            # 访问首页
            print("[访问] https://docs.qq.com/")
            await self.page.goto('https://docs.qq.com/', wait_until='domcontentloaded', timeout=30000)
            
            # 等待页面加载
            await self.page.wait_for_timeout(5000)
            
            # 验证登录状态
            title = await self.page.title()
            print(f"[信息] 页面标题: {title}")
            
            # 检查是否有导入按钮
            import_btn = await self.page.query_selector('button.desktop-import-button-pc')
            if import_btn:
                print("[成功] 找到导入按钮 - 登录成功")
                return True
            else:
                print("[警告] 未找到导入按钮")
                return False
                
        except Exception as e:
            print(f"[错误] 登录失败: {e}")
            return False
    
    async def handle_file_chooser(self, file_chooser):
        """处理文件选择器"""
        try:
            # 自动选择文件
            if hasattr(self, 'upload_file_path'):
                await file_chooser.set_files(self.upload_file_path)
                print(f"[文件] 已选择: {self.upload_file_path}")
        except Exception as e:
            print(f"[错误] 文件选择失败: {e}")
    
    async def upload_file(self, file_path):
        """上传文件到腾讯文档"""
        try:
            print(f"\n[步骤2] 点击导入按钮")
            
            # 保存文件路径供文件选择器使用
            self.upload_file_path = str(Path(file_path).resolve())
            
            # 使用多个选择器尝试找到导入按钮
            import_selectors = [
                'button.desktop-import-button-pc',  # 类选择器
                '#root > div.desktop-layout-pc.desktop-dropdown-container.desktop-skin-default > div.desktop-layout-inner-pc > div > nav > button.desktop-import-button-pc',  # 完整CSS选择器
                'button:has-text("导入")',  # 文本选择器
                'nav button:has(i.desktop-icon-import)'  # 包含图标的按钮
            ]
            
            import_btn = None
            for selector in import_selectors:
                try:
                    import_btn = await self.page.wait_for_selector(selector, timeout=5000)
                    if import_btn:
                        print(f"[成功] 使用选择器找到导入按钮: {selector}")
                        break
                except:
                    continue
            
            if not import_btn:
                print("[错误] 未找到导入按钮")
                return False
            
            # 点击导入按钮
            await import_btn.click()
            print("[步骤3] 文件选择器应该已打开")
            
            # 等待文件选择
            await self.page.wait_for_timeout(2000)
            
            print("[步骤4] 等待导入弹窗出现")
            
            # 等待弹窗出现
            modal_appeared = False
            try:
                # 等待弹窗标题出现
                await self.page.wait_for_selector('.import-kit-import-modal-title:has-text("导入本地文件")', timeout=10000)
                modal_appeared = True
                print("[成功] 导入弹窗已出现")
            except:
                print("[警告] 未检测到导入弹窗")
            
            if modal_appeared:
                # 默认选择第一个选项（转为在线文档多人编辑）
                print("[信息] 默认选择: 转为在线文档多人编辑")
                
                # 等待一下让弹窗完全加载
                await self.page.wait_for_timeout(1000)
                
                # 点击确定按钮 - 使用多个选择器
                confirm_selectors = [
                    'button.dui-button.dui-button-type-primary:has-text("确定")',  # 文本选择器
                    '.import-kit-import-file-footer button.dui-button-type-primary',  # 类选择器
                    'body > div.dui-modal-mask.dui-modal-mask-visible.dui-modal-mask-display > div > div.dui-modal-content > div > div.import-kit-import-file-footer > div:nth-child(2) > button.dui-button.dui-button-type-primary.dui-button-size-default',  # 完整选择器
                    'button.dui-button-type-primary .dui-button-container:has-text("确定")'  # 容器选择器
                ]
                
                confirm_clicked = False
                for selector in confirm_selectors:
                    try:
                        confirm_btn = await self.page.wait_for_selector(selector, timeout=3000)
                        if confirm_btn:
                            await confirm_btn.click()
                            print(f"[成功] 点击确定按钮")
                            confirm_clicked = True
                            break
                    except:
                        continue
                
                if not confirm_clicked:
                    print("[警告] 未能点击确定按钮，尝试键盘确认")
                    await self.page.keyboard.press('Enter')
            
            # 等待上传完成
            print("\n[步骤5] 等待上传完成...")
            await self.page.wait_for_timeout(5000)
            
            # 检查是否上传成功
            # 通常上传成功后会跳转到新文档页面
            current_url = self.page.url
            if '/sheet/' in current_url or '/doc/' in current_url:
                print(f"[成功] 文件上传成功！")
                print(f"[URL] {current_url}")
                return True
            else:
                print("[信息] 等待更长时间确认上传...")
                await self.page.wait_for_timeout(5000)
                current_url = self.page.url
                if '/sheet/' in current_url or '/doc/' in current_url:
                    print(f"[成功] 文件上传成功！")
                    print(f"[URL] {current_url}")
                    return True
                else:
                    print("[警告] 上传可能未完成")
                    return False
                    
        except Exception as e:
            print(f"[错误] 上传失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def cleanup(self):
        """清理资源"""
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
        print("[清理] 浏览器已关闭")

async def main():
    """主函数"""
    
    print("="*60)
    print("腾讯文档精确上传脚本")
    print("="*60)
    
    uploader = TencentDocPreciseUpload()
    
    try:
        # 1. 启动浏览器
        print("\n[开始] 启动浏览器")
        success = await uploader.start_browser(headless=False)
        if not success:
            return
        
        # 2. 读取Cookie配置
        print("\n[配置] 读取Cookie")
        config_file = Path('config/cookies.json')
        
        if not config_file.exists():
            print("[错误] Cookie配置文件不存在")
            return
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            cookie_string = config.get('cookie_string', '')
        
        # 3. 登录
        print("\n[登录] 使用Cookie登录")
        login_success = await uploader.login_with_cookies(cookie_string)
        
        if not login_success:
            print("[错误] 登录失败")
            return
        
        # 4. 选择要上传的文件
        test_files = [
            "副本-副本-测试版本-出国销售计划表.xlsx",
            "test_files/test_upload_20250909.xlsx"
        ]
        
        upload_file = None
        for file in test_files:
            if os.path.exists(file):
                upload_file = file
                break
        
        if not upload_file:
            print("[错误] 未找到测试文件")
            return
        
        print(f"\n[文件] 准备上传: {upload_file}")
        file_size = os.path.getsize(upload_file)
        print(f"[信息] 文件大小: {file_size:,} 字节")
        
        # 5. 执行上传
        upload_success = await uploader.upload_file(upload_file)
        
        if upload_success:
            print("\n" + "="*40)
            print("✅ 上传成功！")
            print("="*40)
        else:
            print("\n" + "="*40)
            print("❌ 上传失败")
            print("="*40)
        
        # 6. 等待观察
        print("\n[等待] 保持浏览器打开30秒供观察...")
        await asyncio.sleep(30)
        
    except Exception as e:
        print(f"\n[异常] {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await uploader.cleanup()
        print("\n[结束] 程序结束")

if __name__ == "__main__":
    asyncio.run(main())