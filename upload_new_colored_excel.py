#!/usr/bin/env python3
"""上传新涂色的Excel文件到腾讯文档"""

import sys
sys.path.append('/root/projects/tencent-doc-manager')

from playwright.async_api import async_playwright
import asyncio
import os
import json
import datetime
from pathlib import Path

class SimpleUploader:
    def __init__(self):
        self.cookie_file = Path('/root/projects/tencent-doc-manager/config/cookies.json')
        self.excel_file = '/root/projects/tencent-doc-manager/excel_outputs/marked/new_colors_20250929_021336.xlsx'

    async def upload(self):
        """简单的上传流程"""
        # 读取cookies
        with open(self.cookie_file, 'r', encoding='utf-8') as f:
            cookies_data = json.load(f)
            cookies = cookies_data.get('cookies', [])

        async with async_playwright() as p:
            # 启动浏览器
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )

            # 添加cookies
            await context.add_cookies(cookies)

            # 创建新页面
            page = await context.new_page()

            try:
                # 访问腾讯文档首页
                print("📋 访问腾讯文档...")
                await page.goto('https://docs.qq.com', wait_until='networkidle', timeout=30000)
                await asyncio.sleep(2)

                # 点击新建按钮
                print("🆕 点击新建...")
                # 尝试多种选择器
                try:
                    new_button = await page.wait_for_selector('button:has-text("新建")', timeout=30000)
                    await new_button.click()
                except:
                    # 尝试其他选择器
                    new_button = await page.wait_for_selector('.new-btn, .create-btn, [data-action="create"]', timeout=30000)
                    await new_button.click()
                await asyncio.sleep(2)

                # 选择导入本地文件
                print("📁 选择导入本地文件...")
                import_option = await page.wait_for_selector('text=导入本地文件', timeout=10000)
                await import_option.click()
                await asyncio.sleep(1)

                # 上传文件
                print(f"📤 上传文件: {os.path.basename(self.excel_file)}")
                file_input = await page.wait_for_selector('input[type="file"]', timeout=10000)
                await file_input.set_input_files(self.excel_file)

                # 等待上传完成
                print("⏳ 等待上传完成...")
                await asyncio.sleep(5)

                # 获取新文档URL
                new_url = page.url
                if 'docs.qq.com/sheet/' in new_url:
                    doc_id = new_url.split('/sheet/')[-1].split('?')[0]
                    print(f"✅ 上传成功！")
                    print(f"🔗 文档URL: {new_url}")
                    print(f"📊 文档ID: {doc_id}")
                    return {'success': True, 'url': new_url, 'doc_id': doc_id}
                else:
                    print(f"⚠️ 未能获取文档URL，当前页面: {new_url}")
                    return {'success': False, 'message': '未能获取文档URL'}

            except Exception as e:
                print(f"❌ 上传失败: {e}")
                return {'success': False, 'message': str(e)}
            finally:
                await browser.close()

async def main():
    uploader = SimpleUploader()
    result = await uploader.upload()

    if result['success']:
        print("\n" + "="*60)
        print("🎉 请访问以下URL验证颜色显示效果:")
        print(f"   {result['url']}")
        print("="*60)

    return result

if __name__ == "__main__":
    result = asyncio.run(main())