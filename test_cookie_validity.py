#!/usr/bin/env python3
"""
测试Cookie是否真正有效的脚本
通过尝试创建新文档来验证Cookie是否过期
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright

async def test_cookie_validity():
    """测试Cookie是否能真正创建新文档"""

    # 读取Cookie
    cookie_file = Path('/root/projects/tencent-doc-manager/config/cookies.json')
    with open(cookie_file) as f:
        cookie_data = json.load(f)

    cookie_string = cookie_data.get('current_cookies', '')
    last_update = cookie_data.get('last_update', 'Unknown')

    print(f"📅 Cookie最后更新: {last_update}")
    print(f"📅 当前时间: {datetime.now().isoformat()}")

    # 计算Cookie年龄
    if last_update != 'Unknown':
        update_time = datetime.fromisoformat(last_update)
        age_days = (datetime.now() - update_time).days
        print(f"⏰ Cookie年龄: {age_days}天")
        if age_days > 7:
            print("⚠️ 警告: Cookie已超过7天，可能已过期！")

    # 解析Cookie
    cookies = []
    for cookie_pair in cookie_string.split('; '):
        if '=' in cookie_pair:
            name, value = cookie_pair.strip().split('=', 1)
            cookies.append({
                'name': name,
                'value': value,
                'domain': '.qq.com',
                'path': '/'
            })

    print(f"🍪 Cookie数量: {len(cookies)}")

    # 使用Playwright测试
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        # 添加Cookie
        await context.add_cookies(cookies)

        page = await context.new_page()

        print("🌐 访问腾讯文档...")
        await page.goto('https://docs.qq.com/desktop/', wait_until='networkidle')

        # 等待页面加载
        await page.wait_for_timeout(3000)

        # 检查登录状态
        try:
            # 查找登录按钮
            login_btn = await page.query_selector('button:has-text("登录")')
            has_login_btn = login_btn is not None

            # 查找用户信息
            user_info = await page.query_selector('.user-info, .user-avatar, .user-name')
            has_user_info = user_info is not None

            # 查找导入按钮（登录后才有）
            import_btn = await page.query_selector('button.desktop-import-button-pc')
            has_import_btn = import_btn is not None

            print(f"🔍 检查结果:")
            print(f"   - 登录按钮存在: {has_login_btn}")
            print(f"   - 用户信息存在: {has_user_info}")
            print(f"   - 导入按钮存在: {has_import_btn}")

            if has_login_btn:
                print("❌ Cookie已失效！页面显示登录按钮")
                print("💡 解决方案: 需要手动登录腾讯文档并重新导出Cookie")
                return False
            elif has_user_info or has_import_btn:
                print("✅ Cookie有效！已成功登录")

                # 尝试获取文档列表数量作为额外验证
                doc_cards = await page.query_selector_all('.doc-card, .file-list-item')
                print(f"📄 可见文档数量: {len(doc_cards)}")

                return True
            else:
                print("⚠️ 无法确定登录状态")
                return None

        except Exception as e:
            print(f"❌ 测试失败: {e}")
            return False
        finally:
            await browser.close()

if __name__ == "__main__":
    result = asyncio.run(test_cookie_validity())

    print("\n" + "="*50)
    if result is True:
        print("✅ 结论: Cookie仍然有效，可以正常使用")
    elif result is False:
        print("❌ 结论: Cookie已失效，需要更新！")
        print("\n📝 更新步骤:")
        print("1. 手动登录 https://docs.qq.com")
        print("2. 使用浏览器开发者工具导出Cookie")
        print("3. 更新 /root/projects/tencent-doc-manager/config/cookies.json")
    else:
        print("⚠️ 结论: 无法确定Cookie状态，建议手动检查")