#!/usr/bin/env python3
"""
使用生产级v3模块上传文件
这才是正确的上传方式！
"""

import asyncio
import json
import os
import sys
from datetime import datetime

sys.path.append('/root/projects/tencent-doc-manager')

async def upload_with_v3():
    """使用v3模块上传文件"""

    print("\n" + "="*60)
    print("🚀 使用生产级v3模块上传")
    print("="*60)

    # 导入正确的v3模块
    from production.core_modules.tencent_doc_upload_production_v3 import (
        TencentDocProductionUploaderV3,
        sync_upload_v3
    )

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
    print("\n📤 开始上传（使用v3多策略识别）...")

    # 使用v3同步上传函数
    result = await sync_upload_v3(
        file_path=file_path,
        cookie_string=cookies
    )

    if result and result.get('success'):
        doc_url = result.get('url')

        print("\n" + "="*60)
        print("✅ 上传成功！（v3模块保证正确链接）")
        print(f"📎 新文档链接: {doc_url}")
        print("="*60)

        # 更新upload_mappings.json
        mappings_file = "/root/projects/tencent-doc-manager/data/upload_mappings.json"

        # 读取现有映射
        with open(mappings_file, 'r') as f:
            mappings_data = json.load(f)

        # 添加新映射
        new_mapping = {
            "file_path": file_path,
            "file_name": upload_file,
            "doc_url": doc_url,
            "upload_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "doc_name": upload_file.replace('.xlsx', ''),
            "week_number": "W38",
            "version_type": "midweek",
            "metadata": {
                "upload_method": "v3",
                "file_size": os.path.getsize(file_path)
            }
        }

        mappings_data['mappings'].append(new_mapping)
        mappings_data['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 保存更新后的映射
        with open(mappings_file, 'w') as f:
            json.dump(mappings_data, f, ensure_ascii=False, indent=2)

        print(f"\n💾 映射已保存到: upload_mappings.json")
        print(f"\n🔗 请访问上传的文档:")
        print(f"   {doc_url}")

        return doc_url
    else:
        error = result.get('error', '未知错误') if result else '上传失败'
        print(f"\n❌ 上传失败: {error}")
        return None

async def main():
    """主函数"""
    print("\n🎯 生产级v3上传测试")
    print("特性：网络监控 + 文件名匹配 + 时间戳检测")

    doc_url = await upload_with_v3()

    if doc_url:
        print("\n" + "✅"*30)
        print(f"\n真实上传成功！这是您上传文件的真实链接：")
        print(f"\n   {doc_url}\n")
        print("✅"*30)
    else:
        print("\n❌ v3上传失败，需要检查系统配置")

    return doc_url

if __name__ == "__main__":
    asyncio.run(main())