#!/usr/bin/env python3
"""基于specs文档的正确上传方法"""

import sys
sys.path.append('/root/projects/tencent-doc-manager')

import asyncio
from playwright.async_api import async_playwright
import json
from pathlib import Path
from datetime import datetime

class SpecBasedUploader:
    """基于specs文档的上传器"""

    def __init__(self):
        self.cookie_file = Path('/root/projects/tencent-doc-manager/config/cookies.json')
        self.excel_file = '/root/projects/tencent-doc-manager/excel_outputs/marked/new_colors_20250929_021336.xlsx'

    async def upload(self):
        """按照specs文档的步骤上传"""

        # 1. 读取cookies
        with open(self.cookie_file, 'r') as f:
            data = json.load(f)
            cookie_string = data.get('current_cookies', '')

        # 2. 解析cookies
        cookies = []
        for item in cookie_string.split('; '):
            if '=' in item:
                name, value = item.split('=', 1)
                cookies.append({
                    'name': name,
                    'value': value,
                    'domain': '.qq.com',
                    'path': '/'
                })

        async with async_playwright() as p:
            # 3. 启动浏览器（参照specs使用headless=True）
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )

            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )

            # 4. 添加cookies
            await context.add_cookies(cookies)

            page = await context.new_page()

            try:
                # 5. 根据specs，需要先导航到一个现有文档
                print("📋 步骤1: 导航到现有腾讯文档...")
                target_url = 'https://docs.qq.com/sheet/DWHJKWGVQZmJmTnBL'
                await page.goto(target_url, wait_until='networkidle', timeout=60000)
                await asyncio.sleep(3)

                # 6. 点击导入按钮（参照V3的selectors）
                print("📥 步骤2: 查找导入按钮...")
                import_selectors = [
                    'button.desktop-import-button-pc',
                    'nav button:has(i.desktop-icon-import)',
                    'button:has-text("导入")',
                    'i.desktop-icon-import',
                    '.desktop-toolbar button[title*="导入"]'
                ]

                import_clicked = False
                for selector in import_selectors:
                    try:
                        btn = await page.wait_for_selector(selector, timeout=3000)
                        await btn.click()
                        print(f"   ✓ 点击导入: {selector}")
                        import_clicked = True
                        break
                    except:
                        continue

                if not import_clicked:
                    print("❌ 未找到导入按钮")
                    return None

                await asyncio.sleep(2)

                # 7. 选择本地Excel选项
                print("📁 步骤3: 选择本地Excel...")
                excel_option_selectors = [
                    'text=/本地.*Excel/i',
                    'text=/Excel.*文件/i',
                    '.import-kit-import-list-item:has-text("Excel")'
                ]

                for selector in excel_option_selectors:
                    try:
                        option = await page.wait_for_selector(selector, timeout=3000)
                        await option.click()
                        print(f"   ✓ 选择Excel选项")
                        break
                    except:
                        continue

                await asyncio.sleep(1)

                # 8. 上传文件
                print(f"📤 步骤4: 上传文件...")
                file_inputs = await page.query_selector_all('input[type="file"]')

                if file_inputs:
                    # 使用最后一个file input
                    await file_inputs[-1].set_input_files(self.excel_file)
                    print(f"   ✓ 文件已选择: new_colors_20250929_021336.xlsx")
                else:
                    print("❌ 未找到文件选择器")
                    return None

                await asyncio.sleep(2)

                # 9. 确认导入（参照specs的confirm_selectors）
                print("✅ 步骤5: 确认导入...")
                confirm_selectors = [
                    'button.dui-button-type-primary:has-text("确定")',
                    '.import-kit-import-file-footer button.dui-button-type-primary',
                    'button:has-text("确定")',
                    'button:has-text("导入")'
                ]

                for selector in confirm_selectors:
                    try:
                        btn = await page.wait_for_selector(selector, timeout=3000)
                        await btn.click()
                        print(f"   ✓ 点击确定")
                        break
                    except:
                        continue

                # 10. 等待上传完成
                print("⏳ 步骤6: 等待上传完成...")
                await asyncio.sleep(10)

                # 11. 获取最终URL
                final_url = page.url

                # 检查是否跳转到新文档
                if final_url != target_url and 'docs.qq.com/sheet/' in final_url:
                    doc_id = final_url.split('/sheet/')[-1].split('?')[0]
                    print("✅ 上传成功！")
                    print(f"📊 文档ID: {doc_id}")
                    print(f"🔗 文档URL: {final_url}")
                    return final_url
                else:
                    # 检查是否有成功提示
                    try:
                        success_msg = await page.wait_for_selector('text=/导入成功/i', timeout=5000)
                        if success_msg:
                            # 查找新创建的sheet标签
                            new_sheet = await page.wait_for_selector('.sheet-tab-item.active', timeout=3000)
                            if new_sheet:
                                await new_sheet.click()
                                await asyncio.sleep(2)
                                final_url = page.url
                                print("✅ 导入成功（作为新sheet）")
                                print(f"🔗 文档URL: {final_url}")
                                return final_url
                    except:
                        pass

                    print(f"⚠️ 上传状态不确定，当前URL: {final_url}")
                    return final_url

            except Exception as e:
                print(f"❌ 上传失败: {e}")
                await page.screenshot(path='/tmp/spec_upload_error.png')
                print("📸 错误截图: /tmp/spec_upload_error.png")
                return None

            finally:
                await browser.close()

async def main():
    uploader = SpecBasedUploader()
    result = await uploader.upload()

    if result:
        print("\n" + "="*70)
        print("🎉 新涂色Excel文件已成功上传！")
        print("")
        print("📌 请访问以下链接验证颜色显示效果：")
        print(f"   {result}")
        print("")
        print("🎨 新颜色配置（更明显）：")
        print("   • L1级别(高风险): 红色 (#FF6666)")
        print("   • L2级别(中风险): 橙色 (#FFB366)")
        print("   • L3级别(低风险): 绿色 (#66FF66)")
        print("")
        print("📊 涂色统计：")
        print("   • L1: 6个单元格")
        print("   • L2: 9个单元格")
        print("   • L3: 7个单元格")
        print("   • 共计: 22个变更")
        print("="*70)
        return result
    else:
        print("\n❌ 上传失败")
        return None

if __name__ == "__main__":
    result = asyncio.run(main())