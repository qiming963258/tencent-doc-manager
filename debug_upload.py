#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试上传问题脚本
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

async def debug_upload():
    """调试上传流程，查看每一步的详细信息"""
    
    print("=" * 60)
    print("上传调试模式")
    print("=" * 60)
    
    # 读取Cookie
    config_path = Path('config.json')
    if not config_path.exists():
        print("❌ 找不到config.json")
        return
        
    with open(config_path, 'r') as f:
        config = json.load(f)
        cookie_string = config.get('cookie', '')
    
    if not cookie_string:
        print("❌ Cookie为空")
        return
    
    # 测试文件
    test_file = Path('/root/projects/tencent-doc-manager/excel_outputs/risk_analysis_report_20250819_024132.xlsx')
    if not test_file.exists():
        test_file = Path('/tmp/test.txt')
        test_file.write_text("测试内容")
    
    print(f"\n📁 测试文件: {test_file}")
    
    # 启动浏览器（无头模式）
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=True,  # 无头模式
        args=['--start-maximized', '--no-sandbox']
    )
    
    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080}
    )
    
    page = await context.new_page()
    
    # 解析并添加Cookie
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
    
    await context.add_cookies(cookies)
    print(f"✅ 已添加 {len(cookies)} 个Cookie")
    
    # 访问desktop页面
    print("\n📄 访问desktop页面...")
    await page.goto('https://docs.qq.com/desktop/', wait_until='domcontentloaded')
    await page.wait_for_timeout(5000)
    
    print(f"当前URL: {page.url}")
    print(f"页面标题: {await page.title()}")
    
    # 查找导入按钮
    import_btn = await page.query_selector('button.desktop-import-button-pc')
    if import_btn:
        print("✅ 找到导入按钮")
    else:
        print("❌ 未找到导入按钮")
        await browser.close()
        await playwright.stop()
        return
    
    # 点击导入按钮
    print("\n🖱️ 点击导入按钮...")
    await import_btn.click()
    await page.wait_for_timeout(2000)
    
    # 选择文件
    print("📂 选择文件...")
    file_inputs = await page.query_selector_all('input[type="file"]')
    if file_inputs:
        print(f"  找到 {len(file_inputs)} 个file input")
        await file_inputs[-1].set_input_files(str(test_file))
        print(f"  ✅ 已选择文件")
    else:
        print("  ⚠️ 使用filechooser")
        async with page.expect_file_chooser() as fc_info:
            await import_btn.click()
        file_chooser = await fc_info.value
        await file_chooser.set_files(str(test_file))
    
    await page.wait_for_timeout(2000)
    
    # 查找确定按钮
    print("\n🔍 查找确定按钮...")
    confirm_selectors = [
        'button.dui-button-type-primary:has-text("确定")',
        '.import-kit-import-file-footer button.dui-button-type-primary',
        'button:has-text("确定")'
    ]
    
    clicked = False
    for selector in confirm_selectors:
        try:
            btn = await page.wait_for_selector(selector, timeout=2000)
            if btn:
                await btn.click()
                print(f"  ✅ 点击了确定按钮: {selector}")
                clicked = True
                break
        except:
            continue
    
    if not clicked:
        print("  ⚠️ 未找到确定按钮，尝试Enter键")
        await page.keyboard.press('Enter')
    
    # 等待并监控URL变化
    print("\n⏳ 等待上传完成，监控URL变化...")
    initial_url = page.url
    print(f"初始URL: {initial_url}")
    
    for i in range(12):  # 等待60秒
        await page.wait_for_timeout(5000)
        current_url = page.url
        print(f"  [{i*5}秒] URL: {current_url}")
        
        # 检查是否有错误提示
        error_elements = await page.query_selector_all('.dui-message-error, .error-message, [class*="error"]')
        if error_elements:
            print("  ⚠️ 检测到错误元素")
            for elem in error_elements[:3]:  # 只显示前3个
                text = await elem.text_content()
                if text:
                    print(f"    错误: {text}")
        
        # 检查URL是否变化
        if current_url != initial_url:
            print(f"  ✅ URL已变化: {current_url}")
            if '/sheet/' in current_url or '/doc/' in current_url:
                print("  🎉 上传成功！")
                break
        
        # 检查页面内容
        if i % 2 == 0:  # 每10秒检查一次
            # 检查是否还在导入对话框
            dialog = await page.query_selector('.import-kit-import-file')
            if dialog:
                print("  📋 导入对话框仍然打开")
            
            # 检查进度条
            progress = await page.query_selector('[class*="progress"], [class*="loading"]')
            if progress:
                print("  ⏳ 检测到进度指示器")
    
    print(f"\n最终URL: {page.url}")
    
    # 保持浏览器打开10秒供观察
    print("\n浏览器将在10秒后关闭...")
    await page.wait_for_timeout(10000)
    
    await browser.close()
    await playwright.stop()
    print("调试完成")

if __name__ == "__main__":
    asyncio.run(debug_upload())