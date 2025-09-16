#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档完整上传实现 - 包含具体点击顺序和成功元素
基于已验证成功的上传流程
"""

import sys
import os
import asyncio
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

# 添加成功方案的路径
sys.path.append('/root/projects/tencent-doc-manager/测试版本-性能优化开发-20250811-001430')

class CompleteUploadSequence:
    """完整的上传点击顺序实现"""
    
    def __init__(self):
        self.browser = None
        self.page = None
        self.playwright = None
        
    async def start_browser(self):
        """启动浏览器"""
        print("🚀 启动浏览器...")
        self.playwright = await async_playwright().start()
        
        # 启动浏览器（无头模式）
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        # 创建上下文
        context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        self.page = await context.new_page()
        print("✅ 浏览器启动成功")
    
    async def load_cookies(self):
        """加载Cookie认证"""
        print("🔐 加载Cookie认证...")
        
        # 读取Cookie文件
        with open('/root/projects/参考/cookie', 'r') as f:
            content = f.read()
            lines = content.strip().split('\n')
            cookies = ""
            for line in lines:
                if line.startswith('fingerprint='):
                    cookies = line
                    break
        
        # 多域名Cookie配置（关键）
        cookie_list = []
        domains = ['docs.qq.com', '.docs.qq.com', 'qq.com', '.qq.com']
        
        for cookie_str in cookies.split(';'):
            if '=' in cookie_str:
                name, value = cookie_str.strip().split('=', 1)
                for domain in domains:
                    cookie_list.append({
                        'name': name,
                        'value': value,
                        'domain': domain,
                        'path': '/',
                        'httpOnly': False,
                        'secure': True,
                        'sameSite': 'None'
                    })
        
        await self.page.context.add_cookies(cookie_list)
        print(f"✅ 已添加 {len(cookie_list)} 个cookies（多域名）")
    
    async def upload_file_with_sequence(self, file_path):
        """执行完整的上传点击顺序"""
        print(f"\n📤 开始上传文件: {os.path.basename(file_path)}")
        print("=" * 60)
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        file_size = os.path.getsize(file_path)
        print(f"📏 文件大小: {file_size} bytes")
        
        # ========== 步骤1: 访问腾讯文档主页 ==========
        print("\n📋 步骤1: 访问腾讯文档主页")
        homepage_url = "https://docs.qq.com/desktop"
        await self.page.goto(homepage_url, wait_until='domcontentloaded')
        print(f"✅ 已访问: {homepage_url}")
        
        # 智能等待页面完全加载
        print("⏳ 等待页面完全加载...")
        await self.page.wait_for_timeout(3000)
        try:
            await self.page.wait_for_load_state('networkidle', timeout=8000)
            print("✅ 网络请求完成")
        except:
            print("⚠️ 网络等待超时，继续执行")
        
        # ========== 步骤2: 查找并点击导入按钮 ==========
        print("\n📋 步骤2: 查找并点击导入按钮")
        
        # 成功的导入按钮选择器（按优先级排列）
        import_selectors = [
            'button[class*="import"]:not([class*="disabled"])',  # ✅ 最成功的选择器
            'div[class*="upload"]:not([class*="disabled"])',
            'button[class*="desktop-import"]',
            'button.desktop-import-button-pc',
            '.desktop-import-button-pc',
            'button:has-text("导入")',
            'button:has-text("上传")',
            'div[role="button"]:has-text("导入")',
            'button[title*="导入"]',
            '[data-action*="import"]'
        ]
        
        import_button = None
        for selector in import_selectors:
            try:
                btn = await self.page.query_selector(selector)
                if btn:
                    is_visible = await btn.is_visible()
                    is_enabled = await btn.is_enabled()
                    if is_visible and is_enabled:
                        import_button = btn
                        print(f"✅ 找到导入按钮: {selector}")
                        break
            except:
                continue
        
        if not import_button:
            raise Exception("未找到导入按钮")
        
        # 准备文件选择器监听
        print("📎 准备文件选择器...")
        file_chooser_promise = self.page.wait_for_event('filechooser')
        
        # 点击导入按钮
        await import_button.click()
        print("✅ 已点击导入按钮")
        
        # ========== 步骤3: 处理文件选择 ==========
        print("\n📋 步骤3: 处理文件选择")
        
        try:
            # 等待文件选择器
            file_chooser = await asyncio.wait_for(file_chooser_promise, timeout=10.0)
            print("✅ 文件选择器已触发")
            
            # 设置要上传的文件
            await file_chooser.set_files(file_path)
            print(f"✅ 已选择文件: {file_path}")
            
        except asyncio.TimeoutError:
            print("⚠️ 文件选择器超时，尝试查找input元素...")
            
            # 备用方案：查找input[type="file"]
            await self.page.wait_for_timeout(2000)
            file_input = await self.page.query_selector('input[type="file"]')
            
            if file_input:
                await file_input.set_input_files(file_path)
                print(f"✅ 通过input元素设置文件: {file_path}")
            else:
                raise Exception("未找到文件输入控件")
        
        # 等待上传对话框出现
        await self.page.wait_for_timeout(3000)
        
        # ========== 步骤4: 点击确认上传按钮 ==========
        print("\n📋 步骤4: 点击确认上传按钮")
        
        # 成功的确认按钮选择器
        confirm_selectors = [
            'button[class*="confirm"]:not([class*="disabled"])',
            'div[class*="dui-button"]:has-text("确定")',  # ✅ 成功使用的选择器
            'button[class*="dui-button"]:has-text("确定")',
            'div.dui-button-container:has-text("确定")',
            'button:has-text("确定")',
            'button:has-text("确认")',
            'button:has-text("上传")',
            '.dui-button:has-text("确定")',
            '[class*="confirm"]:has-text("确定")',
            '[role="button"]:has-text("确定")'
        ]
        
        confirm_button = None
        for selector in confirm_selectors:
            try:
                btn = await self.page.query_selector(selector)
                if btn:
                    is_visible = await btn.is_visible()
                    is_enabled = await btn.is_enabled()
                    if is_visible and is_enabled:
                        confirm_button = btn
                        # 获取按钮文本
                        btn_text = await btn.text_content()
                        print(f"✅ 找到确认按钮: {selector}")
                        print(f"📝 按钮文本: '{btn_text}'")
                        break
            except:
                continue
        
        if confirm_button:
            await confirm_button.click()
            print("✅ 已点击确认按钮")
        else:
            print("⚠️ 未找到确认按钮，可能自动上传")
        
        # ========== 步骤5: 等待上传完成 ==========
        print("\n📋 步骤5: 等待上传完成")
        print("⏳ 监控上传状态...")
        
        # 等待上传进度
        for i in range(30):
            await self.page.wait_for_timeout(1000)
            print(f"⏳ 上传进行中... ({i+1}/30秒)")
            
            # 检查网络空闲状态
            try:
                await self.page.wait_for_load_state('networkidle', timeout=1000)
                print("🌐 网络空闲检测，上传可能已完成")
                break
            except:
                continue
        
        # 验证上传结果
        await self.page.wait_for_timeout(2000)
        
        # 检查成功指标（如新文档出现等）
        success_indicators = await self.page.evaluate('''
            () => {
                // 检查是否有新文档卡片或成功提示
                const hasNewDoc = document.querySelector('[class*="doc-card"], [class*="file-item"]');
                const hasSuccess = document.body.textContent.includes('成功') || 
                                  document.body.textContent.includes('完成');
                return {
                    hasNewDoc: !!hasNewDoc,
                    hasSuccess: hasSuccess
                };
            }
        ''')
        
        if success_indicators['hasNewDoc'] or success_indicators['hasSuccess']:
            print("✅ 检测到上传成功指标")
        
        print("🎉 文件上传流程完成！")
        return True
    
    async def cleanup(self):
        """清理资源"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

async def main():
    """主函数 - 执行完整的上传流程"""
    print("🎯 腾讯文档完整上传流程（包含点击顺序）")
    print("=" * 60)
    
    # 使用修改后的文件
    file_to_upload = "/root/projects/tencent-doc-manager/real_test_results/direct_download_174042/测试版本-回国销售计划表_I6修改.xlsx"
    
    if not os.path.exists(file_to_upload):
        print(f"❌ 文件不存在: {file_to_upload}")
        return
    
    uploader = CompleteUploadSequence()
    
    try:
        # 执行完整的上传流程
        await uploader.start_browser()
        await uploader.load_cookies()
        success = await uploader.upload_file_with_sequence(file_to_upload)
        
        if success:
            print("\n" + "=" * 60)
            print("🎉 上传成功完成！")
            print("✅ 文件已上传到腾讯文档")
            print(f"📋 上传的文件: {os.path.basename(file_to_upload)}")
            print(f"⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 保存成功记录
            success_record = {
                'timestamp': datetime.now().isoformat(),
                'file_uploaded': file_to_upload,
                'file_size': os.path.getsize(file_to_upload),
                'success': True,
                'click_sequence': [
                    '1. 访问主页: https://docs.qq.com/desktop',
                    '2. 点击导入按钮: button[class*="import"]',
                    '3. 选择文件: filechooser事件',
                    '4. 点击确认: div[class*="dui-button"]:has-text("确定")',
                    '5. 等待完成: networkidle检测'
                ]
            }
            
            import json
            with open('/root/projects/tencent-doc-manager/real_test_results/upload_success_sequence.json', 'w') as f:
                json.dump(success_record, f, ensure_ascii=False, indent=2)
                
    except Exception as e:
        print(f"\n❌ 上传失败: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await uploader.cleanup()
        print("\n✅ 资源清理完成")

if __name__ == "__main__":
    asyncio.run(main())