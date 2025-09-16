#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
8093系统上传功能测试脚本
"""

import requests
import json
from pathlib import Path

def test_upload_api():
    """测试8093系统的上传API"""
    
    print("=" * 60)
    print("8093系统上传功能测试")
    print("=" * 60)
    
    # 准备测试文件
    test_file = Path('/root/projects/tencent-doc-manager/excel_outputs/risk_analysis_report_20250819_024132.xlsx')
    
    if not test_file.exists():
        # 创建一个测试文件
        test_file = Path('/tmp/test_upload.txt')
        test_file.write_text("测试上传内容")
        print(f"\n✅ 创建测试文件: {test_file}")
    else:
        print(f"\n✅ 使用现有测试文件: {test_file}")
    
    # 读取Cookie
    cookie_string = ""
    config_path = Path('config.json')
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
            cookie_string = config.get('cookie', '')
    
    if not cookie_string:
        print("⚠️ 警告: 未找到Cookie配置，将使用模拟模式")
    
    # 测试上传API
    print("\n📤 测试上传API...")
    
    upload_data = {
        'file_path': str(test_file),
        'upload_option': 'new',
        'target_url': '',
        'cookie_string': cookie_string
    }
    
    try:
        response = requests.post(
            'http://localhost:8093/api/upload',
            json=upload_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n📊 上传结果:")
            print(f"  成功: {result.get('success')}")
            print(f"  消息: {result.get('message')}")
            print(f"  URL: {result.get('url')}")
            
            if result.get('success'):
                print("\n✅ 上传测试成功！")
            else:
                print(f"\n❌ 上传失败: {result.get('error')}")
        else:
            print(f"\n❌ HTTP错误: {response.status_code}")
            
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
    
    # 测试UI访问
    print("\n🌐 测试Web UI...")
    try:
        response = requests.get('http://localhost:8093/', timeout=5)
        if response.status_code == 200:
            # 检查新UI元素
            html = response.text
            if 'uploadFilePath' in html and 'uploadCookie' in html:
                print("  ✅ UI包含文件路径输入框")
                print("  ✅ UI包含Cookie输入框")
                print("  ✅ UI更新成功")
            else:
                print("  ⚠️ UI可能未完全更新")
    except Exception as e:
        print(f"  ❌ UI访问失败: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("访问 http://202.140.143.88:8093/ 进行手动测试")
    print("=" * 60)

if __name__ == "__main__":
    test_upload_api()