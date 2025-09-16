#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
格式测试 - 验证CSV和Excel导出格式
"""

import sys
import os
import json
import asyncio
from datetime import datetime
import time

# 添加路径
sys.path.append('/root/projects/tencent-doc-manager/测试版本-性能优化开发-20250811-001430')

async def test_format(doc_id, export_format):
    """测试特定导出格式"""
    print(f"\n{'='*50}")
    print(f"📊 格式测试: {export_format.upper()}")
    print(f"📄 文档ID: {doc_id}")
    print(f"{'='*50}")
    
    try:
        from tencent_export_automation import TencentDocAutoExporter
        
        start_time = time.time()
        
        # 创建下载目录
        timestamp = datetime.now().strftime('%H%M%S')
        download_dir = f"/root/projects/tencent-doc-manager/real_test_results/format_{export_format}_{timestamp}"
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
        
        # 下载文档
        doc_url = f"https://docs.qq.com/sheet/{doc_id}"
        print(f"📥 开始下载 {export_format} 格式...")
        
        result = await exporter.auto_export_document(doc_url, export_format=export_format)
        
        end_time = time.time()
        duration = round(end_time - start_time, 2)
        
        if result and len(result) > 0:
            file_path = result[0]
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                file_name = os.path.basename(file_path)
                
                print(f"✅ {export_format.upper()} 格式下载成功！")
                print(f"📁 文件名: {file_name}")
                print(f"📏 文件大小: {file_size} bytes")
                print(f"⏱️ 下载用时: {duration} 秒")
                
                # 文件格式验证
                if export_format == "csv" and file_name.endswith('.csv'):
                    print("✅ CSV格式验证通过")
                    # 读取CSV内容样例
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            sample_line = f.readline().strip()
                            print(f"📝 CSV样例: {sample_line[:50]}...")
                    except:
                        print("⚠️ CSV内容读取失败")
                
                elif export_format == "excel" and (file_name.endswith('.xlsx') or file_name.endswith('.xls')):
                    print("✅ Excel格式验证通过")
                    print(f"📊 Excel文件类型: {file_name.split('.')[-1].upper()}")
                
                else:
                    print(f"⚠️ 文件格式异常: 期望 {export_format}, 实际 {file_name}")
                
                success = True
                
            else:
                print("❌ 下载的文件不存在")
                success = False
        else:
            print(f"❌ {export_format.upper()} 格式下载失败")
            success = False
        
        # 清理
        if exporter.browser:
            await exporter.browser.close()
        if exporter.playwright:
            await exporter.playwright.stop()
        
        return {
            'format': export_format,
            'success': success,
            'file_size': file_size if success else 0,
            'duration': duration,
            'file_name': file_name if success else None
        }
        
    except Exception as e:
        print(f"❌ {export_format.upper()} 格式测试失败: {e}")
        return {
            'format': export_format,
            'success': False,
            'error': str(e),
            'duration': 0
        }

async def format_comparison_test():
    """格式对比测试"""
    print("🎯 腾讯文档格式对比测试")
    print("="*50)
    print("📋 测试计划: CSV vs Excel 格式导出对比")
    print("="*50)
    
    # 使用已验证可用的文档ID
    doc_id = "DWEVjZndkR2xVSWJN"  # 小红书部门项目计划
    
    # 测试格式列表
    formats = ["csv", "excel"]
    results = []
    
    for i, fmt in enumerate(formats, 1):
        print(f"\n🔄 格式测试 {i}/{len(formats)}")
        
        result = await test_format(doc_id, fmt)
        results.append(result)
        
        # 间隔等待
        if i < len(formats):
            print("⏳ 等待3秒后进行下一格式测试...")
            await asyncio.sleep(3)
    
    # 生成对比报告
    print(f"\n{'='*60}")
    print("📊 格式对比测试报告")
    print(f"{'='*60}")
    
    success_count = sum(1 for r in results if r['success'])
    
    print(f"📈 总体统计:")
    print(f"  测试格式数: {len(formats)}")
    print(f"  成功格式数: {success_count}")
    print(f"  格式兼容率: {(success_count/len(formats)*100):.1f}%")
    
    print(f"\n📋 详细对比:")
    for result in results:
        status = "✅ 支持" if result['success'] else "❌ 不支持"
        print(f"  {result['format'].upper()} 格式: {status}")
        
        if result['success']:
            print(f"    📏 文件大小: {result.get('file_size', 0)} bytes")
            print(f"    ⏱️ 导出用时: {result.get('duration', 0)} 秒")
            print(f"    📁 文件名: {result.get('file_name', 'N/A')}")
        else:
            error = result.get('error', '未知错误')
            print(f"    ❌ 错误信息: {error}")
    
    # 最终结论
    if success_count == len(formats):
        print(f"\n🎉 格式测试完全成功！")
        print("✅ 浏览器自动化方案支持多种导出格式")
        print("✅ CSV和Excel格式导出均正常工作")
    elif success_count > 0:
        print(f"\n⚠️ 部分格式支持 ({success_count}/{len(formats)})")
        working_formats = [r['format'] for r in results if r['success']]
        print(f"✅ 支持格式: {', '.join(working_formats).upper()}")
    else:
        print(f"\n❌ 格式测试失败")
        print("🔧 需要检查导出功能配置")
    
    return results

if __name__ == "__main__":
    asyncio.run(format_comparison_test())