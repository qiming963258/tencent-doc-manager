#!/usr/bin/env python3
"""最终上传尝试 - 使用最简单可靠的方法"""

import sys
sys.path.append('/root/projects/tencent-doc-manager')

from playwright.sync_api import sync_playwright
import json
import time
from pathlib import Path

def simple_upload():
    """使用同步方法上传"""

    # 读取cookie文件
    cookie_file = Path('/root/projects/tencent-doc-manager/config/cookies.json')
    with open(cookie_file, 'r') as f:
        data = json.load(f)
        cookie_string = data.get('current_cookies', '')

    # 解析cookie字符串
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

    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(
            headless=False,  # 使用有头模式
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )

        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )

        # 添加cookies
        context.add_cookies(cookies)

        # 创建页面
        page = context.new_page()

        try:
            # 访问腾讯文档
            print("📋 步骤1: 访问腾讯文档主页...")
            page.goto('https://docs.qq.com', timeout=60000)
            time.sleep(5)

            # 检查是否已登录
            print("🔐 步骤2: 检查登录状态...")
            if "登录" in page.content():
                print("⚠️ 需要登录，cookies可能已过期")
                return None

            # 尝试点击新建
            print("🆕 步骤3: 查找新建按钮...")

            # 尝试多种选择器
            selectors = [
                'button:has-text("新建")',
                '.new-btn',
                '[data-action="create"]',
                '.header-bar-new-btn',
                'span:has-text("新建")'
            ]

            clicked = False
            for selector in selectors:
                try:
                    element = page.wait_for_selector(selector, timeout=5000)
                    element.click()
                    clicked = True
                    print(f"   ✓ 找到并点击: {selector}")
                    break
                except:
                    continue

            if not clicked:
                print("❌ 无法找到新建按钮")
                # 尝试直接访问导入页面
                print("📂 尝试直接访问导入页面...")
                page.goto('https://docs.qq.com/desktop/import')
                time.sleep(3)
            else:
                time.sleep(2)

                # 查找导入选项
                print("📥 步骤4: 选择导入本地文件...")
                import_selectors = [
                    'text=/导入.*本地/',
                    'text=导入本地文件',
                    '[data-action="import"]'
                ]

                for selector in import_selectors:
                    try:
                        element = page.wait_for_selector(selector, timeout=5000)
                        element.click()
                        print(f"   ✓ 点击导入: {selector}")
                        break
                    except:
                        continue

            time.sleep(2)

            # 上传文件
            print("📤 步骤5: 上传Excel文件...")
            excel_file = '/root/projects/tencent-doc-manager/excel_outputs/marked/new_colors_20250929_021336.xlsx'

            # 查找文件输入
            file_input = page.wait_for_selector('input[type="file"]', timeout=10000)
            file_input.set_input_files(excel_file)
            print(f"   ✓ 文件已选择: new_colors_20250929_021336.xlsx")

            # 等待上传
            print("⏳ 步骤6: 等待上传完成...")
            time.sleep(10)

            # 获取最终URL
            final_url = page.url

            if 'docs.qq.com/sheet/' in final_url:
                doc_id = final_url.split('/sheet/')[-1].split('?')[0]
                print("✅ 上传成功！")
                print(f"📊 文档ID: {doc_id}")
                print(f"🔗 文档URL: {final_url}")
                return final_url
            else:
                print(f"⚠️ 未能获取有效URL: {final_url}")
                # 尝试查找最新创建的文档
                page.goto('https://docs.qq.com')
                time.sleep(3)
                # 查找最新文档
                latest_doc = page.query_selector('.doc-list-item:first-child a')
                if latest_doc:
                    href = latest_doc.get_attribute('href')
                    if href:
                        full_url = f'https://docs.qq.com{href}' if href.startswith('/') else href
                        print(f"📄 找到最新文档: {full_url}")
                        return full_url

                return None

        except Exception as e:
            print(f"❌ 出错: {e}")
            # 保存截图
            page.screenshot(path='/tmp/upload_final_error.png')
            print("📸 错误截图已保存: /tmp/upload_final_error.png")
            return None

        finally:
            browser.close()

if __name__ == "__main__":
    print("="*60)
    print("🚀 开始最终上传尝试")
    print("="*60)

    result = simple_upload()

    if result:
        print("\n" + "="*70)
        print("🎉 成功上传新涂色的Excel文件！")
        print("")
        print("📌 请访问以下链接验证颜色显示效果：")
        print(f"   {result}")
        print("")
        print("🎨 您应该能看到以下颜色：")
        print("   • L1级别(高风险): 红色 (#FF6666)")
        print("   • L2级别(中风险): 橙色 (#FFB366)")
        print("   • L3级别(低风险): 绿色 (#66FF66)")
        print("="*70)
    else:
        print("\n❌ 上传失败，请手动上传文件：")
        print("   /root/projects/tencent-doc-manager/excel_outputs/marked/new_colors_20250929_021336.xlsx")