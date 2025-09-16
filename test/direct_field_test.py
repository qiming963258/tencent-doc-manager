#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接现场测试 - 简化版本
"""

import sys
import os
import json
import asyncio
from datetime import datetime

# 添加路径
sys.path.append('/root/projects/tencent-doc-manager/测试版本-性能优化开发-20250811-001430')

async def single_test(doc_id, doc_name, format_type):
    """单个文档测试"""
    print(f"\n{'='*60}")
    print(f"📄 测试文档: {doc_name}")
    print(f"🆔 ID: {doc_id}")
    print(f"📊 格式: {format_type}")
    print(f"{'='*60}")
    
    try:
        from tencent_export_automation import TencentDocAutoExporter
        
        # 创建下载目录
        timestamp = datetime.now().strftime('%H%M%S')
        download_dir = f"/root/projects/tencent-doc-manager/real_test_results/field_{timestamp}"
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
        
        # 下载
        doc_url = f"https://docs.qq.com/sheet/{doc_id}"
        print(f"📥 开始下载...")
        
        result = await exporter.auto_export_document(doc_url, export_format=format_type)
        
        if result and len(result) > 0:
            file_path = result[0]
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                print(f"✅ 成功！文件: {os.path.basename(file_path)}")
                print(f"📏 大小: {size} bytes")
                
                # 读取前几行
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for i in range(3):
                            line = f.readline().strip()
                            if line:
                                print(f"📝 第{i+1}行: {line[:80]}...")
                except:
                    print("⚠️ 无法预览内容")
                    
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
            
        return success
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

async def main():
    """主测试"""
    print("🎯 腾讯文档 - 真实现场测试")
    print("="*60)
    
    # 测试文档列表
    tests = [
        ("DWEVjZndkR2xVSWJN", "小红书部门", "csv"),
        ("DRFppYm15RGZ2WExN", "回国销售计划", "csv"),
        ("DRHZrS1hOS3pwRGZB", "出国销售计划", "csv"),
    ]
    
    results = []
    
    for doc_id, doc_name, format_type in tests:
        success = await single_test(doc_id, doc_name, format_type)
        results.append((doc_name, success))
        
        # 间隔
        print("⏳ 等待5秒...")
        await asyncio.sleep(5)
    
    # 总结
    print(f"\n{'='*60}")
    print("📊 现场测试总结")
    print(f"{'='*60}")
    
    success_count = sum(1 for _, success in results if success)
    total_count = len(results)
    
    print(f"总测试: {total_count}")
    print(f"成功: {success_count}")
    print(f"成功率: {success_count/total_count*100:.1f}%")
    
    print("\n详细结果:")
    for i, (name, success) in enumerate(results, 1):
        status = "✅" if success else "❌"
        print(f"  {i}. {name} - {status}")
    
    if success_count == total_count:
        print("\n🎉 现场测试完全成功！浏览器自动化方案完全可用！")
    elif success_count > 0:
        print(f"\n⚠️ 部分成功 ({success_count}/{total_count})")
    else:
        print("\n❌ 全部失败")

if __name__ == "__main__":
    asyncio.run(main())