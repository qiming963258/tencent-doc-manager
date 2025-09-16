#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接下载测试 - 回国销售计划表
使用浏览器自动化程序直接下载指定链接
"""

import sys
import os
import json
import asyncio
from datetime import datetime

# 添加浏览器自动化工具路径
sys.path.append('/root/projects/tencent-doc-manager/测试版本-性能优化开发-20250811-001430')

async def direct_download_test():
    """直接下载测试"""
    print("🎯 直接下载测试 - 回国销售计划表")
    print("=" * 60)
    print(f"🌐 目标链接: https://docs.qq.com/sheet/DRFppYm15RGZ2WExN")
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        from tencent_export_automation import TencentDocAutoExporter
        
        # 创建下载目录
        timestamp = datetime.now().strftime('%H%M%S')
        download_dir = f"/root/projects/tencent-doc-manager/real_test_results/direct_download_{timestamp}"
        os.makedirs(download_dir, exist_ok=True)
        
        # 读取Cookie
        print("🔐 读取认证信息...")
        with open('/root/projects/参考/cookie', 'r') as f:
            content = f.read()
            # 提取cookie行
            lines = content.strip().split('\n')
            cookies = ""
            for line in lines:
                if line.startswith('fingerprint='):
                    cookies = line
                    break
        
        print(f"📍 Cookie认证: {len(cookies)} 字符")
        
        # 创建导出器
        exporter = TencentDocAutoExporter(download_dir=download_dir)
        
        print("🚀 启动浏览器...")
        await exporter.start_browser(headless=True)
        
        print("🔐 加载认证...")
        await exporter.login_with_cookies(cookies)
        
        # 下载指定文档
        target_url = "https://docs.qq.com/sheet/DRFppYm15RGZ2WExN"
        print(f"📥 开始下载...")
        print(f"🎯 正在访问: {target_url}")
        
        # 下载Excel格式
        print("📊 导出格式: Excel")
        result = await exporter.auto_export_document(target_url, export_format="excel")
        
        if result and len(result) > 0:
            file_path = result[0]
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                file_name = os.path.basename(file_path)
                
                print(f"✅ 下载成功！")
                print(f"📁 文件名: {file_name}")
                print(f"📂 文件路径: {file_path}")
                print(f"📏 文件大小: {file_size} bytes")
                
                # 验证文件格式
                with open(file_path, 'rb') as f:
                    header = f.read(4)
                
                if header == b'PK\x03\x04':
                    print("✅ Excel格式验证通过")
                else:
                    print("⚠️ 文件格式异常")
                
                success = True
                result_info = {
                    'file_path': file_path,
                    'file_name': file_name,
                    'file_size': file_size,
                    'download_time': datetime.now().isoformat(),
                    'target_url': target_url,
                    'format_valid': header == b'PK\x03\x04'
                }
            else:
                print("❌ 下载的文件不存在")
                success = False
                result_info = {'error': '文件不存在'}
        else:
            print("❌ 下载失败")
            success = False
            result_info = {'error': '下载返回空结果'}
        
        # 清理资源
        if exporter.browser:
            await exporter.browser.close()
        if exporter.playwright:
            await exporter.playwright.stop()
        
        # 生成测试报告
        print(f"\n{'=' * 60}")
        print("📊 下载测试结果")
        print(f"{'=' * 60}")
        
        if success:
            print("🎉 直接下载测试成功！")
            print(f"✅ 成功下载: {result_info['file_name']}")
            print(f"✅ 文件大小: {result_info['file_size']} bytes")
            print(f"✅ 格式验证: {'通过' if result_info['format_valid'] else '失败'}")
            print("✅ 浏览器自动化程序运行正常")
        else:
            print("❌ 直接下载测试失败")
            print(f"错误信息: {result_info.get('error', '未知错误')}")
        
        # 保存测试结果
        test_report = {
            'test_timestamp': datetime.now().isoformat(),
            'target_url': target_url,
            'success': success,
            'result_info': result_info,
            'test_type': '直接下载测试',
            'document_name': '回国销售计划表'
        }
        
        report_file = os.path.join(download_dir, 'download_test_report.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(test_report, f, ensure_ascii=False, indent=2)
        
        print(f"💾 测试报告: {report_file}")
        
        return success
        
    except Exception as e:
        print(f"❌ 下载测试异常: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(direct_download_test())