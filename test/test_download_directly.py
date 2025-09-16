#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试download_file_from_url函数
"""

import json
import sys
from pathlib import Path

# 设置路径
sys.path.append('/root/projects/tencent-doc-manager')

# 读取保存的Cookie
config_file = Path('/root/projects/tencent-doc-manager/config.json')
with open(config_file, 'r', encoding='utf-8') as f:
    config = json.load(f)
    cookie = config.get('cookie', '')

print(f"Cookie长度: {len(cookie)} 字符")
print(f"Cookie前100字符: {cookie[:100]}...")
print(f"Cookie后100字符: ...{cookie[-100:]}")

# 导入下载函数
print("\n正在导入下载函数...")
try:
    from auto_download_ui_system import download_file_from_url
    print("✅ 导入成功")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

# 测试下载
test_url = "https://docs.qq.com/sheet/DWFJzdWNwd0RGbU5R"  # 测试版本-小红书部门
print(f"\n测试下载: {test_url}")
print("这可能需要一些时间，请耐心等待...")

# 设置超时
import signal

def timeout_handler(signum, frame):
    print("\n⏰ 下载超时（60秒）")
    print("可能的原因：")
    print("1. Cookie已过期或无效")
    print("2. 网络连接问题")
    print("3. 腾讯文档页面结构变化")
    sys.exit(1)

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(60)  # 60秒超时

try:
    result = download_file_from_url(test_url, format_type='csv')
    signal.alarm(0)  # 取消超时
    
    print("\n下载结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    if result and result.get('success'):
        print("\n✅ 下载成功！")
        if result.get('files'):
            for file in result['files']:
                print(f"  - 文件: {file.get('name')}")
                print(f"    路径: {file.get('path')}")
    else:
        print(f"\n❌ 下载失败: {result.get('error', '未知错误')}")
        
except Exception as e:
    signal.alarm(0)
    print(f"\n❌ 异常: {e}")
    import traceback
    traceback.print_exc()