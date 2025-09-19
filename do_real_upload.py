#!/usr/bin/env python3
"""
真实上传XLSX到腾讯文档
"""

import asyncio
import json
import os
import sys
from datetime import datetime

sys.path.append('/root/projects/tencent-doc-manager')

async def main():
    print("\n" + "="*60)
    print("🚀 上传XLSX文件到腾讯文档")
    print("="*60)

    # 文件路径
    file_path = "/root/projects/tencent-doc-manager/csv_versions/2025_W38/midweek/tencent_111测试版本-小红书部门_20250919_2255_midweek_W38_colored.xlsx"

    if not os.path.exists(file_path):
        # 尝试原始文件
        file_path = "/root/projects/tencent-doc-manager/csv_versions/2025_W38/midweek/tencent_111测试版本-小红书部门_20250919_2255_midweek_W38.xlsx"

    print(f"📄 文件: {os.path.basename(file_path)}")
    print(f"📏 大小: {os.path.getsize(file_path):,} bytes")

    # 读取Cookie
    with open('/root/projects/tencent-doc-manager/config/cookies.json', 'r') as f:
        cookie_data = json.load(f)
        cookies = cookie_data.get('current_cookies', '')

    # 导入上传函数
    from tencent_doc_uploader import upload_file

    print("\n📤 开始上传...")

    # 调用上传函数
    result = await upload_file(
        file_path=file_path,
        upload_option='new',
        target_url='',
        cookie_string=cookies
    )

    if result and result.get('success'):
        doc_url = result.get('url')
        print("\n" + "="*60)
        print("✅ 上传成功！")
        print(f"📎 新文档链接: {doc_url}")
        print("="*60)
        print(f"\n🔗 请复制此链接访问上传的文档:")
        print(f"   {doc_url}")
        return doc_url
    else:
        error = result.get('error', '未知错误') if result else '上传失败'
        print(f"\n❌ 上传失败: {error}")

        # 提供备用方案
        print("\n📌 备用方案 - 使用现有文档:")
        print("   https://docs.qq.com/sheet/DWFJzdWNwd0RGbU5R")
        return None

if __name__ == "__main__":
    asyncio.run(main())
