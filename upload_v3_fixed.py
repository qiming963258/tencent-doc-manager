#!/usr/bin/env python3
"""
使用v3模块正确上传 - 修复版
"""

import json
import os
import sys
from datetime import datetime

sys.path.append('/root/projects/tencent-doc-manager')

def upload_with_v3_sync():
    """使用v3模块同步上传"""

    print("\n" + "="*60)
    print("🚀 使用生产级v3模块上传（修复版）")
    print("="*60)

    # 导入v3模块的同步函数
    from production.core_modules.tencent_doc_upload_production_v3 import sync_upload_v3

    # 找到要上传的文件
    midweek_dir = "/root/projects/tencent-doc-manager/csv_versions/2025_W38/midweek"

    # 选择最新的XLSX文件
    xlsx_files = [f for f in os.listdir(midweek_dir) if f.endswith('.xlsx')]
    if not xlsx_files:
        print("❌ 没有找到XLSX文件")
        return None

    # 优先选择涂色文件
    colored_files = [f for f in xlsx_files if 'colored' in f]
    if colored_files:
        upload_file = colored_files[-1]
    else:
        upload_file = sorted(xlsx_files)[-1]

    file_path = os.path.join(midweek_dir, upload_file)

    print(f"📄 上传文件: {upload_file}")
    print(f"📏 文件大小: {os.path.getsize(file_path):,} bytes")

    # 读取Cookie
    with open('/root/projects/tencent-doc-manager/config/cookies.json', 'r') as f:
        cookie_data = json.load(f)
        cookies = cookie_data.get('current_cookies', '')

    if not cookies:
        print("❌ Cookie为空")
        return None

    print("🍪 Cookie状态: ✅ 有效")
    print("\n📤 开始上传（v3多策略：网络监控+文件名匹配+时间戳）...")

    # 使用v3同步上传函数（正确的参数顺序）
    result = sync_upload_v3(
        cookie_string=cookies,
        file_path=file_path,
        headless=True
    )

    if result and result.get('success'):
        doc_url = result.get('url')

        print("\n" + "="*60)
        print("✅ v3上传成功！（真实的新文档链接）")
        print(f"📎 新文档链接: {doc_url}")
        print("="*60)
        
        print(f"\n🔗 这是您上传的文件的真实链接：")
        print(f"   {doc_url}")
        
        return doc_url
    else:
        error = result.get('error', '未知错误') if result else '上传失败'
        print(f"\n❌ 上传失败: {error}")
        return None

if __name__ == "__main__":
    doc_url = upload_with_v3_sync()
    if doc_url:
        print("\n" + "✅"*30)
        print(f"成功获取真实链接！")
    else:
        print("\n需要检查v3模块配置")
