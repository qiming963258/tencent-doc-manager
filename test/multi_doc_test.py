#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多文档现场测试 - 验证不同文档ID的通用性
"""

import sys
import os
import json
import asyncio
from datetime import datetime
import time

# 添加路径
sys.path.append('/root/projects/tencent-doc-manager/测试版本-性能优化开发-20250811-001430')

async def test_single_doc(doc_info, test_id):
    """测试单个文档"""
    doc_id = doc_info['id']
    doc_name = doc_info['name']
    export_format = doc_info['format']
    
    print(f"\n{'='*60}")
    print(f"📄 测试 {test_id}: {doc_name}")
    print(f"🆔 文档ID: {doc_id}")
    print(f"📊 格式: {export_format}")
    print(f"{'='*60}")
    
    result = {
        'doc_id': doc_id,
        'doc_name': doc_name,
        'format': export_format,
        'success': False,
        'file_size': 0,
        'content_preview': '',
        'error': None,
        'duration': 0
    }
    
    try:
        from tencent_export_automation import TencentDocAutoExporter
        
        start_time = time.time()
        
        # 创建下载目录
        timestamp = datetime.now().strftime('%H%M%S')
        download_dir = f"/root/projects/tencent-doc-manager/real_test_results/multi_{timestamp}_{test_id}"
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
        print(f"📥 开始下载...")
        
        download_result = await exporter.auto_export_document(doc_url, export_format=export_format)
        
        end_time = time.time()
        result['duration'] = round(end_time - start_time, 2)
        
        if download_result and len(download_result) > 0:
            file_path = download_result[0]
            if os.path.exists(file_path):
                result['success'] = True
                result['file_size'] = os.path.getsize(file_path)
                
                # 读取内容预览
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        first_line = f.readline().strip()
                        result['content_preview'] = first_line[:100]
                except:
                    result['content_preview'] = "无法读取内容"
                
                print(f"✅ 下载成功！")
                print(f"📁 文件: {os.path.basename(file_path)}")
                print(f"📏 大小: {result['file_size']} bytes")
                print(f"⏱️ 用时: {result['duration']} 秒")
                print(f"📝 首行: {result['content_preview']}")
            else:
                print("❌ 文件不存在")
                result['error'] = "文件不存在"
        else:
            print("❌ 下载失败")
            result['error'] = "下载返回空结果"
        
        # 清理
        if exporter.browser:
            await exporter.browser.close()
        if exporter.playwright:
            await exporter.playwright.stop()
            
    except Exception as e:
        result['error'] = str(e)
        print(f"❌ 测试异常: {e}")
    
    return result

async def multi_doc_test():
    """多文档测试主函数"""
    print("🎯 多文档现场测试 - 验证不同文档ID通用性")
    print("="*60)
    
    # 测试文档列表
    test_docs = [
        {'id': 'DWEVjZndkR2xVSWJN', 'name': '小红书部门项目计划', 'format': 'csv'},
        {'id': 'DRFppYm15RGZ2WExN', 'name': '回国销售计划表', 'format': 'csv'},
        {'id': 'DRHZrS1hOS3pwRGZB', 'name': '出国销售计划表', 'format': 'csv'}
    ]
    
    results = []
    success_count = 0
    
    for i, doc_info in enumerate(test_docs, 1):
        test_result = await test_single_doc(doc_info, i)
        results.append(test_result)
        
        if test_result['success']:
            success_count += 1
        
        # 间隔等待
        if i < len(test_docs):
            print("⏳ 等待5秒后进行下一个测试...")
            await asyncio.sleep(5)
    
    # 生成总结报告
    print(f"\n{'='*60}")
    print("📊 多文档测试总结报告")
    print(f"{'='*60}")
    
    print(f"📈 统计结果:")
    print(f"  总测试数: {len(test_docs)}")
    print(f"  成功数量: {success_count}")
    print(f"  失败数量: {len(test_docs) - success_count}")
    print(f"  成功率: {(success_count/len(test_docs)*100):.1f}%")
    
    print(f"\n📋 详细结果:")
    for i, result in enumerate(results, 1):
        status = "✅ 成功" if result['success'] else "❌ 失败"
        print(f"  {i}. {result['doc_name']} - {status}")
        if result['success']:
            print(f"     📏 {result['file_size']} bytes | ⏱️ {result['duration']}s")
            print(f"     📝 {result['content_preview']}")
        else:
            print(f"     ❌ {result['error']}")
    
    # 最终结论
    if success_count == len(test_docs):
        print(f"\n🎉 多文档测试完全成功！")
        print("✅ 浏览器自动化方案具备完美的通用性")
        print("✅ 可以处理不同类型的腾讯文档")
    elif success_count > 0:
        print(f"\n⚠️ 多文档测试部分成功 ({success_count}/{len(test_docs)})")
        print("📝 部分文档可能存在权限或格式问题")
    else:
        print(f"\n❌ 多文档测试失败")
        print("🔧 需要检查配置或网络问题")
    
    return results

if __name__ == "__main__":
    asyncio.run(multi_doc_test())