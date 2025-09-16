#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试成功的浏览器自动化方案
使用找到的关键文件：tencent_export_automation.py
"""

import sys
import os
import json
import asyncio
from pathlib import Path
from datetime import datetime

# 添加成功方案的路径
sys.path.append('/root/projects/tencent-doc-manager/测试版本-性能优化开发-20250811-001430')

def load_cookies():
    """加载有效的Cookie"""
    cookie_file = "/root/projects/tencent-doc-manager/config/cookies_new.json"
    with open(cookie_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get("current_cookies", "")

def test_import():
    """测试能否导入成功的模块"""
    print("🧪 测试导入成功的自动化模块...")
    
    try:
        # 导入成功的自动化工具
        from tencent_export_automation import TencentDocAutoExporter
        print("✅ 成功导入TencentDocAutoExporter")
        return TencentDocAutoExporter
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return None
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return None

async def test_basic_functionality(exporter_class):
    """测试基础功能"""
    print("\n🔧 测试基础功能...")
    
    try:
        # 创建导出器实例
        download_dir = "/root/projects/tencent-doc-manager/real_test_results/test_downloads"
        os.makedirs(download_dir, exist_ok=True)
        
        exporter = exporter_class(download_dir=download_dir)
        print("✅ 成功创建导出器实例")
        
        # 启动浏览器（无头模式）
        await exporter.start_browser(headless=True)
        print("✅ 成功启动浏览器")
        
        # 加载Cookie
        cookies = load_cookies()
        await exporter.login_with_cookies(cookies)
        print(f"✅ 成功加载Cookie ({len(cookies)} 字符)")
        
        # 关闭浏览器
        if exporter.browser:
            await exporter.browser.close()
        if exporter.playwright:
            await exporter.playwright.stop()
        print("✅ 成功关闭浏览器")
        
        return True
        
    except Exception as e:
        print(f"❌ 基础功能测试失败: {e}")
        # 确保清理
        try:
            if hasattr(exporter, 'browser') and exporter.browser:
                await exporter.browser.close()
            if hasattr(exporter, 'playwright') and exporter.playwright:
                await exporter.playwright.stop()
        except:
            pass
        return False

async def test_document_download():
    """测试完整的文档下载"""
    print("\n📥 测试完整文档下载...")
    
    try:
        from tencent_export_automation import TencentDocAutoExporter
        
        download_dir = "/root/projects/tencent-doc-manager/real_test_results/test_downloads"
        os.makedirs(download_dir, exist_ok=True)
        
        exporter = TencentDocAutoExporter(download_dir=download_dir)
        await exporter.start_browser(headless=True)
        
        # 加载Cookie
        cookies = load_cookies()
        await exporter.login_with_cookies(cookies)
        
        # 测试文档URL（使用之前成功的文档）
        test_url = "https://docs.qq.com/sheet/DWEVjZndkR2xVSWJN"
        print(f"📄 测试文档: {test_url}")
        
        # 尝试下载CSV格式
        result = await exporter.auto_export_document(test_url, export_format="csv")
        
        if result and len(result) > 0:
            print(f"🎉 下载成功！文件: {result}")
            
            # 检查文件内容
            for file_path in result:
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    print(f"📁 文件大小: {file_size} bytes")
                    
                    # 检查前几行内容
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            first_lines = [f.readline().strip() for _ in range(3)]
                            print(f"📝 前3行内容:")
                            for i, line in enumerate(first_lines, 1):
                                if line:
                                    print(f"  {i}. {line[:100]}")
                    except Exception as e:
                        print(f"⚠️ 读取文件内容失败: {e}")
            
            success = True
        else:
            print("❌ 下载失败")
            success = False
        
        # 清理
        if exporter.browser:
            await exporter.browser.close()
        if exporter.playwright:
            await exporter.playwright.stop()
            
        return success
        
    except Exception as e:
        print(f"❌ 文档下载测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🚀 测试成功的浏览器自动化方案")
    print("="*60)
    
    # 步骤1：测试模块导入
    exporter_class = test_import()
    if not exporter_class:
        print("\n❌ 无法导入成功的模块，测试终止")
        return
    
    # 步骤2：测试基础功能
    basic_success = await test_basic_functionality(exporter_class)
    if not basic_success:
        print("\n❌ 基础功能测试失败，跳过下载测试")
        return
    
    # 步骤3：测试完整下载
    download_success = await test_document_download()
    
    print("\n" + "="*60)
    print("📊 测试结果总结")
    print("="*60)
    
    if download_success:
        print("🎉 测试成功！成功的浏览器自动化方案可以工作")
        print("💡 这证明了8月19日的成功方法确实有效")
        print("📋 建议：使用这个方案替代所有API尝试")
    else:
        print("😞 测试失败，需要进一步调试")
        print("🔧 可能需要检查：Cookie有效性、网络连接、页面元素变化")

if __name__ == "__main__":
    asyncio.run(main())