#!/usr/bin/env python3
"""
测试v3上传模块返回值
"""

import os
import sys
import json
from datetime import datetime

sys.path.append('/root/projects/tencent-doc-manager')

from production.core_modules.tencent_doc_upload_production_v3 import sync_upload_v3

# 文件路径
colored_file = "/root/projects/tencent-doc-manager/csv_versions/2025_W38/midweek/tencent_111测试版本-小红书部门_20250919_2255_midweek_W38_colored.xlsx"

print(f"📄 测试文件: {os.path.basename(colored_file)}")
print(f"📏 文件大小: {os.path.getsize(colored_file):,} bytes")

# 获取Cookie
with open('/root/projects/tencent-doc-manager/config/cookies.json', 'r') as f:
    cookies = json.load(f)

cookie_str = cookies.get('current_cookies', '')
print(f"📝 Cookie长度: {len(cookie_str)} 字符")
print(f"📝 Cookie前50字符: {cookie_str[:50]}...")

# 调用v3模块 - 注意参数顺序是 (cookie_string, file_path)
print("\n🔄 调用v3模块上传...")
result = sync_upload_v3(cookie_str, colored_file)

print(f"\n📊 返回值类型: {type(result)}")
print(f"📊 返回内容: {result}")

if isinstance(result, dict):
    print("\n返回的是字典，包含键:")
    for key in result.keys():
        print(f"  - {key}: {result[key]}")
elif isinstance(result, str):
    print(f"\n返回的是字符串: {result}")
else:
    print(f"\n返回的是其他类型: {type(result)}")
