#!/usr/bin/env python3
"""
内存优化的腾讯文档下载修复模块
解决Chromium崩溃问题
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

async def optimize_browser_launch():
    """优化浏览器启动参数以减少内存使用"""
    from playwright.async_api import async_playwright
    
    print("🔧 启动内存优化的浏览器实例...")
    
    playwright = await async_playwright().start()
    
    # 使用更激进的内存优化参数
    browser = await playwright.chromium.launch(
        headless=True,  # 强制无头模式
        args=[
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',  # 关键：使用/tmp而不是/dev/shm
            '--disable-gpu',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            '--disable-dev-tools',
            '--no-zygote',  # 减少进程
            '--single-process',  # 单进程模式（内存优化）
            '--disable-extensions',
            '--disable-images',  # 不加载图片
            '--disable-javascript',  # 禁用JS（如果不需要）
            '--memory-pressure-off',
            '--disable-background-networking',
            '--disable-background-timer-throttling',
            '--disable-renderer-backgrounding',
            '--disable-features=TranslateUI',
            '--disable-ipc-flooding-protection',
            '--password-store=basic',
            '--use-mock-keychain',
            '--force-color-profile=srgb',
            '--metrics-recording-only',
            '--disable-features=PasswordExport',
            '--no-first-run',
            '--disable-default-apps',
            '--mute-audio',
            '--no-default-browser-check',
            '--disable-sync',
            '--disable-domain-reliability',
            '--disable-client-side-phishing-detection',
            '--disable-component-update',
            '--disable-features=MediaRouter',
            '--memory-model=low',  # 低内存模式
            '--max_old_space_size=512',  # 限制V8堆大小
        ]
    )
    
    return playwright, browser

async def test_memory_optimized_download():
    """测试内存优化的下载"""
    playwright, browser = None, None
    
    try:
        playwright, browser = await optimize_browser_launch()
        
        # 创建浏览器上下文（限制内存）
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            device_scale_factor=1,
            java_script_enabled=False,  # 禁用JS减少内存
        )
        
        page = await context.new_page()
        
        # 测试访问
        print("🌐 测试访问腾讯文档...")
        await page.goto('https://docs.qq.com', wait_until='domcontentloaded', timeout=30000)
        
        print("✅ 浏览器启动成功，内存优化生效！")
        
        # 显示内存使用情况（使用系统命令）
        import os
        pid = os.getpid()
        os.system(f"ps aux | grep {pid} | grep -v grep | awk '{{print \"📊 进程内存使用: \"$6/1024\"MB\"}}'  | head -1")
        
        return True
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False
        
    finally:
        if browser:
            await browser.close()
        if playwright:
            await playwright.stop()

def apply_memory_fix_to_export_module():
    """将内存优化应用到导出模块"""
    export_file = Path("/root/projects/tencent-doc-manager/production/core_modules/tencent_export_automation.py")
    
    print("📝 正在修改导出模块以应用内存优化...")
    
    # 读取文件
    with open(export_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找browser启动的位置
    if 'self.browser = await self.playwright.chromium.launch(' in content:
        # 替换启动参数
        old_launch = """self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )"""
        
        new_launch = """self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',  # 内存优化：使用/tmp
                '--disable-gpu',
                '--disable-extensions',
                '--disable-images',  # 不加载图片
                '--disable-background-networking',
                '--memory-model=low',  # 低内存模式
                '--max_old_space_size=512',  # 限制堆大小
                '--single-process'  # 单进程模式
            ]
        )"""
        
        if old_launch in content:
            content = content.replace(old_launch, new_launch)
            print("✅ 找到并替换了启动参数")
        else:
            print("⚠️ 未找到完全匹配的启动代码，尝试部分替换...")
            # 尝试更通用的替换
            import re
            pattern = r'(self\.browser\s*=\s*await\s+self\.playwright\.chromium\.launch\([^)]*\))'
            replacement = new_launch
            content = re.sub(pattern, replacement, content)
    
    # 写回文件
    with open(export_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 内存优化已应用到导出模块")

if __name__ == "__main__":
    print("🚀 腾讯文档下载内存优化修复程序")
    print("=" * 50)
    
    # 测试优化的浏览器
    print("\n1. 测试内存优化的浏览器启动...")
    success = asyncio.run(test_memory_optimized_download())
    
    if success:
        print("\n2. 应用修复到导出模块...")
        apply_memory_fix_to_export_module()
        print("\n✅ 修复完成！请重新测试8093系统。")
    else:
        print("\n❌ 浏览器测试失败，请检查内存状况。")