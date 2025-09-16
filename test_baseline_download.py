#!/usr/bin/env python3
"""测试基线文件下载功能"""

import sys
import os
import json
from datetime import datetime
import pytz

# 添加项目路径
sys.path.insert(0, '/root/projects/tencent-doc-manager')

from production.core_modules.tencent_export_automation import TencentDocAutoExporter
from production.core_modules.week_time_manager import WeekTimeManager

def test_baseline_download():
    """测试下载基线文件"""

    # 初始化时间管理器
    wtm = WeekTimeManager()
    week_info = wtm.get_current_week_info()
    current_week = week_info['week_number']
    print(f"📅 当前周数: 第{current_week}周")

    # 创建基线文件夹
    baseline_dir = f"/root/projects/tencent-doc-manager/csv_versions/2025_W{current_week}/baseline"
    os.makedirs(baseline_dir, exist_ok=True)
    print(f"📁 基线文件夹: {baseline_dir}")

    # 读取Cookie
    with open('/root/projects/tencent-doc-manager/config/cookies.json', 'r') as f:
        cookie_data = json.load(f)
    cookie_string = cookie_data.get('current_cookies', '')
    print(f"🔑 Cookie长度: {len(cookie_string)} 字符")

    # 初始化下载器
    exporter = TencentDocAutoExporter()

    # 要下载的文档
    documents = [
        {
            "name": "111测试版本-出国销售计划表",
            "url": "https://docs.qq.com/sheet/DWEFNU25TemFnZXJN?tab=BB08J2"
        },
        {
            "name": "111测试版本-小红书部门",
            "url": "https://docs.qq.com/sheet/DWFJzdWNwd0RGbU5R?tab=000001"
        }
    ]

    # 下载每个文档
    for doc in documents:
        print(f"\n📥 正在下载: {doc['name']}")
        print(f"   URL: {doc['url']}")

        try:
            # 调用导出方法
            result = exporter.export_document(
                url=doc['url'],
                cookies=cookie_string,
                format='csv',
                download_dir=baseline_dir
            )

            if result['success']:
                print(f"   ✅ 下载成功!")
                print(f"   📄 文件路径: {result.get('file_path', 'N/A')}")

                # 重命名为基线文件格式
                if 'file_path' in result:
                    old_path = result['file_path']
                    # 生成基线文件名
                    beijing_tz = pytz.timezone('Asia/Shanghai')
                    now = datetime.now(beijing_tz)
                    timestamp = now.strftime('%Y%m%d_%H%M')

                    # 清理文档名称
                    clean_name = doc['name'].replace('111测试版本-', '')

                    # 生成新文件名（避免双重tencent_前缀）
                    new_filename = f"tencent_{clean_name}_{timestamp}_baseline_W{current_week}.csv"
                    new_path = os.path.join(baseline_dir, new_filename)

                    # 重命名文件
                    if os.path.exists(old_path):
                        os.rename(old_path, new_path)
                        print(f"   📝 重命名为: {new_filename}")

            else:
                print(f"   ❌ 下载失败: {result.get('error', '未知错误')}")

        except Exception as e:
            print(f"   ❌ 异常: {str(e)}")

    # 列出基线文件夹内容
    print(f"\n📋 基线文件夹内容:")
    for file in os.listdir(baseline_dir):
        file_path = os.path.join(baseline_dir, file)
        file_size = os.path.getsize(file_path) / 1024  # KB
        print(f"   - {file} ({file_size:.1f} KB)")

if __name__ == "__main__":
    test_baseline_download()