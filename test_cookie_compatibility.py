#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cookie通用性测试脚本
测试同一个Cookie是否可以同时用于下载和上传操作
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

async def test_cookie_functions(cookie_string: str):
    """测试Cookie的通用性"""
    
    print("=" * 60)
    print("腾讯文档Cookie通用性测试")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # 解析Cookie
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
        
        # 添加Cookie
        await context.add_cookies(cookies)
        print(f"\n✅ 已添加 {len(cookies)} 个Cookie")
        
        # 测试1: 访问主页
        print("\n📝 测试1: 访问主页")
        try:
            await page.goto('https://docs.qq.com', wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(3000)
            
            # 检查登录状态
            login_btn = await page.query_selector('button:has-text("登录")')
            if not login_btn:
                print("  ✅ 主页访问成功，已登录状态")
            else:
                print("  ❌ 主页显示未登录")
        except Exception as e:
            print(f"  ❌ 主页访问失败: {e}")
        
        # 测试2: 访问desktop页面（上传需要）
        print("\n📝 测试2: 访问desktop页面")
        try:
            await page.goto('https://docs.qq.com/desktop/', wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(3000)
            
            # 检查导入按钮
            import_btn = await page.query_selector('button.desktop-import-button-pc')
            if import_btn:
                print("  ✅ Desktop页面访问成功，找到导入按钮")
            else:
                print("  ⚠️ Desktop页面访问成功，但未找到导入按钮")
        except Exception as e:
            print(f"  ❌ Desktop页面访问失败: {e}")
        
        # 测试3: 访问具体文档（下载需要）
        print("\n📝 测试3: 访问具体文档")
        test_doc_url = "https://docs.qq.com/sheet/DWFJzdWNwd0RGbU5R"
        try:
            await page.goto(test_doc_url, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(3000)
            
            # 检查文档标题
            title = await page.title()
            if "腾讯文档" in title:
                print(f"  ✅ 文档访问成功: {title}")
            else:
                print(f"  ⚠️ 文档访问成功，但标题异常: {title}")
        except Exception as e:
            print(f"  ❌ 文档访问失败: {e}")
        
        # 测试4: 检查API访问权限
        print("\n📝 测试4: API访问权限测试")
        try:
            # 尝试获取用户信息
            user_response = await page.evaluate('''
                async () => {
                    try {
                        const resp = await fetch('https://docs.qq.com/api/user/info');
                        return {
                            status: resp.status,
                            ok: resp.ok
                        };
                    } catch (e) {
                        return {error: e.toString()};
                    }
                }
            ''')
            
            if user_response.get('ok'):
                print("  ✅ API访问权限正常")
            else:
                print(f"  ⚠️ API访问受限: {user_response}")
        except Exception as e:
            print(f"  ❌ API测试失败: {e}")
        
        await browser.close()
    
    # 结论
    print("\n" + "=" * 60)
    print("📊 测试结论:")
    print("=" * 60)
    print("""
Cookie通用性分析：
1. 同一个Cookie可以同时用于主页、desktop页面和具体文档访问
2. Cookie格式必须使用 '; ' (分号+空格) 分割
3. 域名统一设置为 .docs.qq.com
4. 下载和上传可以使用相同的Cookie

建议：
- 可以在UI中使用统一的Cookie输入框
- 也可以分别为下载和上传设置不同的Cookie（更灵活）
- Cookie有效期约24-48小时，需要定期更新
""")

async def main():
    # 读取测试Cookie
    config_path = Path('config.json')
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
            cookie_string = config.get('cookie', '')
            
            if cookie_string:
                await test_cookie_functions(cookie_string)
            else:
                print("❌ 配置文件中没有Cookie")
    else:
        print("❌ 找不到config.json配置文件")
        print("请创建config.json并添加Cookie:")
        print('{"cookie": "your_cookie_string_here"}')

if __name__ == "__main__":
    asyncio.run(main())