#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上传稳定性测试 - 验证是否可以稳定复现
"""

import sys
import os
import asyncio
import json
from datetime import datetime

sys.path.append('/root/projects/tencent-doc-manager/测试版本-性能优化开发-20250811-001430')
from tencent_upload_automation import TencentDocUploader

async def stability_test():
    """稳定性测试 - 连续执行多次上传"""
    print("🧪 上传稳定性测试")
    print("=" * 60)
    
    # 准备测试文件（使用不同的文件避免重复）
    test_files = [
        "/root/projects/tencent-doc-manager/real_test_results/direct_download_174042/测试版本-回国销售计划表_I6修改.xlsx",
        "/root/projects/tencent-doc-manager/real_test_results/verified_test_163708/测试版本-小红书部门.xlsx"
    ]
    
    # 读取Cookie
    with open('/root/projects/参考/cookie', 'r') as f:
        content = f.read()
        lines = content.strip().split('\n')
        cookies = ""
        for line in lines:
            if line.startswith('fingerprint='):
                cookies = line
                break
    
    results = []
    
    for i, file_path in enumerate(test_files[:2], 1):  # 测试2个文件验证稳定性
        if not os.path.exists(file_path):
            print(f"❌ 文件不存在: {file_path}")
            continue
            
        print(f"\n🔄 测试 {i}: {os.path.basename(file_path)}")
        print("-" * 40)
        
        uploader = TencentDocUploader()
        
        try:
            # 启动浏览器
            await uploader.start_browser(headless=True)
            
            # 加载认证
            await uploader.login_with_cookies(cookies)
            
            # 执行上传
            start_time = datetime.now()
            success = await uploader.upload_file_to_main_page(
                file_path=file_path,
                homepage_url="https://docs.qq.com/desktop",
                max_retries=1  # 减少重试次数以快速测试
            )
            end_time = datetime.now()
            
            result = {
                'test_number': i,
                'file': os.path.basename(file_path),
                'success': success,
                'duration': (end_time - start_time).total_seconds(),
                'timestamp': datetime.now().isoformat()
            }
            
            results.append(result)
            
            if success:
                print(f"✅ 测试{i} 成功！用时: {result['duration']:.2f}秒")
            else:
                print(f"❌ 测试{i} 失败")
                
        except Exception as e:
            print(f"❌ 测试{i} 异常: {e}")
            results.append({
                'test_number': i,
                'file': os.path.basename(file_path),
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            
        finally:
            # 清理资源
            if uploader.browser:
                await uploader.browser.close()
            if hasattr(uploader, 'playwright'):
                await uploader.playwright.stop()
        
        # 测试间隔
        if i < len(test_files):
            print("⏳ 等待5秒后进行下一次测试...")
            await asyncio.sleep(5)
    
    # 生成稳定性报告
    print("\n" + "=" * 60)
    print("📊 稳定性测试报告")
    print("=" * 60)
    
    success_count = sum(1 for r in results if r.get('success', False))
    total_count = len(results)
    
    print(f"总测试次数: {total_count}")
    print(f"成功次数: {success_count}")
    print(f"成功率: {(success_count/total_count*100) if total_count > 0 else 0:.1f}%")
    
    # 保存报告
    report = {
        'test_timestamp': datetime.now().isoformat(),
        'total_tests': total_count,
        'successful_tests': success_count,
        'success_rate': (success_count/total_count*100) if total_count > 0 else 0,
        'test_results': results,
        'conclusion': '稳定可复现' if success_count == total_count else '需要优化'
    }
    
    with open('/root/projects/tencent-doc-manager/real_test_results/upload_stability_report.json', 'w') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    return success_count == total_count

if __name__ == "__main__":
    is_stable = asyncio.run(stability_test())
    
    if is_stable:
        print("\n🎉 结论: 上传功能稳定可复现！")
    else:
        print("\n⚠️ 结论: 上传功能需要进一步优化")