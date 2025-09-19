#!/usr/bin/env python3
"""
立即测试下载，生成带当前时间戳的文件
"""

import asyncio
import json
import os
from datetime import datetime
import sys

sys.path.append('/root/projects/tencent-doc-manager')

async def test_download_now():
    """立即执行下载测试"""
    print("=" * 60)
    print(f"⏰ 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    from production.core_modules.playwright_downloader import PlaywrightDownloader

    # 读取cookie
    with open('/root/projects/tencent-doc-manager/config/cookies.json', 'r') as f:
        cookie_data = json.load(f)
        cookies = cookie_data.get('current_cookies', '')

    # 创建唯一的下载目录（带时间戳）
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    download_dir = f"/root/projects/tencent-doc-manager/test_download_{timestamp}"
    os.makedirs(download_dir, exist_ok=True)

    print(f"📁 下载目录: {download_dir}")
    print(f"🔗 测试URL: https://docs.qq.com/sheet/DWEFNU25TemFnZXJN")
    print("⬇️ 开始下载...")

    # 使用PlaywrightDownloader下载
    downloader = PlaywrightDownloader()
    result = await downloader.download(
        url="https://docs.qq.com/sheet/DWEFNU25TemFnZXJN",
        cookies=cookies,
        download_dir=download_dir,
        format='csv'
    )

    if result['success']:
        file_path = result['file_path']
        print(f"\n✅ 下载成功!")
        print(f"📄 文件路径: {file_path}")
        print(f"📏 文件大小: {result['file_size']:,} bytes")
        print(f"⏱️ 下载耗时: {result['download_time']:.2f}秒")

        # 显示文件时间戳
        if os.path.exists(file_path):
            stat = os.stat(file_path)
            created_time = datetime.fromtimestamp(stat.st_ctime)
            print(f"🕐 文件创建时间: {created_time.strftime('%Y-%m-%d %H:%M:%S')}")

            # 读取前3行验证内容
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                print(f"\n📊 文件内容验证:")
                print(f"   总行数: {len(lines)}")
                print(f"   前2行内容:")
                for i, line in enumerate(lines[:2], 1):
                    preview = line[:60] + "..." if len(line) > 60 else line.strip()
                    print(f"   {i}: {preview}")
    else:
        print(f"\n❌ 下载失败: {result['error']}")

    print("\n" + "=" * 60)
    print(f"⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_download_now())