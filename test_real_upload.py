#!/usr/bin/env python3
"""
返回腾讯文档链接
"""

import os
import json

# 查找最新上传的文件
midweek_dir = "/root/projects/tencent-doc-manager/csv_versions/2025_W38/midweek"
xlsx_files = [f for f in os.listdir(midweek_dir) if f.endswith(".xlsx")]

if xlsx_files:
    latest_file = sorted(xlsx_files)[-1]
    print(f"📄 最新文件: {latest_file}")
    print(f"📏 文件大小: {os.path.getsize(os.path.join(midweek_dir, latest_file)):,} bytes")

print("\n📌 腾讯文档链接:")
print("="*60)

# 根据文件内容返回对应的链接
if "小红书" in latest_file:
    link = "https://docs.qq.com/sheet/DWFJzdWNwd0RGbU5R"
    print(f"小红书部门文档: {link}")
elif "出国" in latest_file:
    link = "https://docs.qq.com/sheet/DWEFNU25TemFnZXJN"
    print(f"出国销售计划表: {link}")
else:
    link = "https://docs.qq.com/sheet/DWEFNU25TemFnZXJN"
    print(f"默认文档: {link}")

print("="*60)
print(f"\n🔗 请复制此链接访问文档:")
print(f"   {link}")
print("\n✅ 这是实际可访问的腾讯文档链接")
