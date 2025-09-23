#!/usr/bin/env python3
"""
下载所有文档作为W39基线文件
"""

import os
import json
import sys
sys.path.insert(0, '/root/projects/tencent-doc-manager')

from production.core_modules.tencent_export_automation import TencentDocAutoExporter
from production.core_modules.week_time_manager import WeekTimeManager
from pathlib import Path
import datetime

def download_all_baselines():
    """下载所有配置的文档作为基线文件"""

    # 读取配置
    config_path = '/root/projects/tencent-doc-manager/config/download_config.json'
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # 读取Cookie
    cookie_path = '/root/projects/tencent-doc-manager/config/cookies.json'
    with open(cookie_path, 'r', encoding='utf-8') as f:
        cookie_data = json.load(f)
        # 兼容多种Cookie字段名
        cookie = cookie_data.get('current_cookies') or cookie_data.get('cookie_string') or cookie_data.get('cookie')
        if not cookie:
            print("❌ Cookie文件中没有找到有效的Cookie字段")
            return

    # 初始化下载器和周管理器
    downloader = TencentDocAutoExporter()
    week_manager = WeekTimeManager()
    week_info = week_manager.get_current_week_info()
    current_week = week_info['week_number']
    current_year = week_info['year']

    # 确保基线目录存在
    baseline_dir = Path(f'/root/projects/tencent-doc-manager/csv_versions/{current_year}_W{current_week:02d}/baseline')
    baseline_dir.mkdir(parents=True, exist_ok=True)

    print(f"📁 基线文件将保存到: {baseline_dir}")
    print(f"📅 当前周数: W{current_week:02d}")

    results = []

    # 下载每个文档
    for doc in config.get('document_links', []):
        if not doc.get('enabled', True):
            continue

        url = doc['url']
        name = doc['name']
        doc_id = doc['id']

        print(f"\n{'='*60}")
        print(f"📥 下载文档: {name}")
        print(f"🔗 URL: {url}")

        try:
            # 下载文档
            print(f"⏳ 正在下载...")
            # 使用export_document方法，传入cookie
            result = downloader.export_document(url, cookies=cookie, format='csv')

            if result and result.get('success'):
                downloaded_file = result.get('file_path')

            if downloaded_file and os.path.exists(downloaded_file):
                # 构建规范的基线文件名
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M')
                clean_name = name.replace('副本-测试版本-', '').replace('测试版本-', '')
                baseline_filename = f"tencent_{clean_name}_{timestamp}_baseline_W{current_week:02d}.csv"
                baseline_path = baseline_dir / baseline_filename

                # 移动文件到基线目录
                import shutil
                shutil.move(downloaded_file, str(baseline_path))

                print(f"✅ 基线文件已保存: {baseline_filename}")
                results.append({
                    'name': name,
                    'file': str(baseline_path),
                    'success': True
                })
            else:
                print(f"❌ 下载失败")
                results.append({
                    'name': name,
                    'success': False
                })

        except Exception as e:
            print(f"❌ 下载出错: {str(e)}")
            results.append({
                'name': name,
                'success': False,
                'error': str(e)
            })

    # 显示结果汇总
    print(f"\n{'='*60}")
    print("📊 下载结果汇总:")
    for result in results:
        if result['success']:
            print(f"  ✅ {result['name']}")
            print(f"     文件: {os.path.basename(result['file'])}")
        else:
            print(f"  ❌ {result['name']}")
            if 'error' in result:
                print(f"     错误: {result['error']}")

    # 显示当前所有基线文件
    print(f"\n📁 W{current_week:02d}基线目录内容:")
    for file in sorted(baseline_dir.glob("*.csv")):
        size = file.stat().st_size / 1024
        print(f"  📄 {file.name} ({size:.1f} KB)")

if __name__ == "__main__":
    download_all_baselines()