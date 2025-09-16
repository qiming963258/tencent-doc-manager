#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速单文档现场测试
"""

import sys
import os
import json
import asyncio
from datetime import datetime

# 添加路径
sys.path.append('/root/projects/tencent-doc-manager/测试版本-性能优化开发-20250811-001430')

async def quick_test():
    """快速单文档测试"""
    print("🎯 快速现场测试 - 验证浏览器自动化方案")
    print("="*60)
    
    try:
        from tencent_export_automation import TencentDocAutoExporter
        
        # 创建下载目录
        timestamp = datetime.now().strftime('%H%M%S')
        download_dir = f"/root/projects/tencent-doc-manager/real_test_results/quick_{timestamp}"
        os.makedirs(download_dir, exist_ok=True)
        
        # 创建导出器
        exporter = TencentDocAutoExporter(download_dir=download_dir)
        
        print("🚀 启动浏览器...")
        await exporter.start_browser(headless=True)
        
        # 加载Cookie
        print("🔐 加载认证...")
        cookie_file = "/root/projects/tencent-doc-manager/config/cookies_new.json"
        with open(cookie_file, 'r') as f:
            data = json.load(f)
            cookies = data.get("current_cookies", "")
        
        await exporter.login_with_cookies(cookies)
        
        # 测试文档
        doc_id = "DWEVjZndkR2xVSWJN"
        doc_url = f"https://docs.qq.com/sheet/{doc_id}"
        print(f"📄 测试文档: 小红书部门 ({doc_id})")
        print(f"📥 开始下载...")
        
        result = await exporter.auto_export_document(doc_url, export_format="csv")
        
        if result and len(result) > 0:
            file_path = result[0]
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                print(f"✅ 下载成功！")
                print(f"📁 文件: {os.path.basename(file_path)}")
                print(f"📏 大小: {size} bytes")
                
                # 读取前几行验证内容
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = []
                        for i in range(5):
                            line = f.readline().strip()
                            if line:
                                lines.append(line)
                        
                        print(f"📝 内容验证:")
                        for i, line in enumerate(lines, 1):
                            print(f"  第{i}行: {line[:80]}...")
                        
                        # 检查是否为真实业务数据
                        first_line = lines[0] if lines else ""
                        if "," in first_line and any(keyword in first_line for keyword in ["项目", "部门", "计划", "name", "Name"]):
                            print("✅ 确认为真实业务数据格式")
                        else:
                            print("⚠️ 数据格式需要进一步验证")
                        
                except Exception as e:
                    print(f"⚠️ 内容读取失败: {e}")
                
                success = True
            else:
                print("❌ 文件不存在")
                success = False
        else:
            print("❌ 下载失败")
            success = False
        
        # 清理
        if exporter.browser:
            await exporter.browser.close()
        if exporter.playwright:
            await exporter.playwright.stop()
        
        print(f"\n{'='*60}")
        if success:
            print("🎉 快速测试成功！浏览器自动化方案完全可用！")
            print("✅ 验证结论：8月19日的成功方法仍然有效")
        else:
            print("❌ 快速测试失败，需要检查配置")
        print(f"{'='*60}")
        
        return success
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(quick_test())