#!/usr/bin/env python3
"""测试修复后的上传功能"""

import asyncio
import sys
from pathlib import Path

sys.path.append('/root/projects/tencent-doc-manager')

from production.core_modules.tencent_doc_upload_production_v3 import TencentDocProductionUploaderV3

async def test_upload():
    """测试上传功能"""
    # 使用最新生成的涂色文件
    file_path = "/root/projects/tencent-doc-manager/excel_outputs/marked/tencent_副本-副本-测试版本-出国销售计划表_20250929_0121_midweek_W40_marked_20250929_012144_W00.xlsx"

    if not Path(file_path).exists():
        print(f"❌ 文件不存在: {file_path}")
        return None

    print(f"📁 准备上传文件: {Path(file_path).name}")
    print(f"📊 文件大小: {Path(file_path).stat().st_size / 1024:.2f} KB")

    uploader = TencentDocProductionUploaderV3(headless=True)

    try:
        # 启动浏览器
        print("🌐 初始化浏览器...")
        await uploader.start()

        # 上传文件
        print("📤 开始上传...")
        result = await uploader.upload_file(file_path)

        # 打印结果
        print("\n" + "="*60)
        print("📊 上传结果:")
        print(f"  成功: {result.get('success', False)}")
        print(f"  URL: {result.get('url', 'N/A')}")
        print(f"  消息: {result.get('message', 'N/A')}")
        if result.get('storage_warning'):
            print(f"  ⚠️ 存储警告: {result.get('storage_warning')}")
        print("="*60)

        return result

    except Exception as e:
        print(f"❌ 上传失败: {e}")
        import traceback
        traceback.print_exc()
        return None

    finally:
        print("🔚 清理资源...")
        await uploader.cleanup()

if __name__ == "__main__":
    print("🚀 开始测试上传功能（95%限制已移除）")
    print("-"*60)

    result = asyncio.run(test_upload())

    if result and result.get('success'):
        print(f"\n✅ 上传成功！文档URL: {result.get('url')}")
    else:
        print(f"\n❌ 上传失败")