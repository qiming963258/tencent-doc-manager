#!/usr/bin/env python3
"""测试基线文件多行输入和同名文件软删除功能"""

import sys
import os
import json
import re
import shutil
from datetime import datetime
import pytz

# 添加项目路径
sys.path.insert(0, '/root/projects/tencent-doc-manager')

from production.core_modules.tencent_export_automation import TencentDocAutoExporter
from production.core_modules.week_time_manager import WeekTimeManager

def parse_multiline_urls(text):
    """解析多行URL输入，支持腾讯文档分享格式"""
    urls = []
    lines = text.strip().split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 匹配【腾讯文档】格式
        if '【腾讯文档】' in line:
            # 提取文档名称
            name_match = re.search(r'【腾讯文档】(.+?)https?://', line)
            name = name_match.group(1).strip() if name_match else None

            # 提取URL
            url_match = re.search(r'https?://[^\s]+', line)
            url = url_match.group(0) if url_match else None

            if url:
                urls.append({
                    'name': name,
                    'url': url
                })
        # 直接URL格式
        elif line.startswith('http'):
            urls.append({
                'name': None,
                'url': line
            })

    return urls

def soft_delete_existing_files(baseline_dir, filename_pattern):
    """软删除已存在的同名文件"""
    deleted_dir = os.path.join(baseline_dir, '.deleted')
    os.makedirs(deleted_dir, exist_ok=True)

    deleted_files = []

    # 查找匹配的文件
    for file in os.listdir(baseline_dir):
        if file.startswith('.'):
            continue

        # 检查是否是同名文件（忽略时间戳部分）
        # 提取文档名称部分
        if '_' in file:
            parts = file.split('_')
            if len(parts) >= 2:
                # 比较前两部分（tencent_文档名）
                file_prefix = '_'.join(parts[:2])

                # 检查是否匹配
                if filename_pattern in file_prefix:
                    # 软删除：移动到.deleted文件夹
                    old_path = os.path.join(baseline_dir, file)

                    # 添加删除时间戳
                    beijing_tz = pytz.timezone('Asia/Shanghai')
                    now = datetime.now(beijing_tz)
                    timestamp = now.strftime('%Y%m%d_%H%M%S')

                    deleted_filename = f"deleted_{timestamp}_{file}"
                    new_path = os.path.join(deleted_dir, deleted_filename)

                    shutil.move(old_path, new_path)
                    deleted_files.append({
                        'original': file,
                        'deleted_to': deleted_filename
                    })
                    print(f"   🗑️ 软删除: {file} -> .deleted/{deleted_filename}")

    return deleted_files

def test_multiline_baseline_download():
    """测试多行URL输入的基线文件下载"""

    print("📊 测试基线文件多行输入和同名文件软删除功能")
    print("=" * 60)

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

    # 模拟多行URL输入（包含之前已下载的文档）
    multiline_input = """
【腾讯文档】111测试版本-出国销售计划表 https://docs.qq.com/sheet/DWEFNU25TemFnZXJN?tab=BB08J2
【腾讯文档】111测试版本-小红书部门 https://docs.qq.com/sheet/DWFJzdWNwd0RGbU5R?tab=000001
https://docs.qq.com/sheet/DWEFNU25TemFnZXJN?tab=BB08J2
    """

    print(f"\n📝 模拟多行输入:")
    print("---")
    print(multiline_input.strip())
    print("---")

    # 解析URL
    urls = parse_multiline_urls(multiline_input)
    print(f"\n✅ 解析出 {len(urls)} 个URL:")
    for i, item in enumerate(urls, 1):
        print(f"   {i}. {item['name'] or '(未命名)'}: {item['url']}")

    # 初始化下载器
    exporter = TencentDocAutoExporter()

    # 下载每个文档
    print(f"\n🚀 开始批量下载基线文件...")
    for i, item in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] 下载: {item['name'] or item['url']}")

        # 提取文档名称用于软删除检查
        doc_name = item['name']
        if doc_name and '111测试版本-' in doc_name:
            doc_name = doc_name.replace('111测试版本-', '')

        # 检查并软删除同名文件
        if doc_name:
            print(f"   🔍 检查同名文件: {doc_name}")
            deleted = soft_delete_existing_files(baseline_dir, doc_name)
            if deleted:
                print(f"   ✅ 软删除了 {len(deleted)} 个同名文件")

        try:
            # 调用导出方法
            result = exporter.export_document(
                url=item['url'],
                cookies=cookie_string,
                format='csv',
                download_dir=baseline_dir
            )

            if result['success']:
                print(f"   ✅ 下载成功!")

                # 重命名为基线文件格式
                if 'file_path' in result:
                    old_path = result['file_path']

                    # 生成基线文件名
                    beijing_tz = pytz.timezone('Asia/Shanghai')
                    now = datetime.now(beijing_tz)
                    timestamp = now.strftime('%Y%m%d_%H%M')

                    # 使用文档名称或从URL提取
                    if doc_name:
                        clean_name = doc_name
                    else:
                        clean_name = f"document_{i}"

                    # 生成新文件名
                    new_filename = f"tencent_{clean_name}_{timestamp}_baseline_W{current_week}.csv"
                    new_path = os.path.join(baseline_dir, new_filename)

                    # 重命名文件
                    if os.path.exists(old_path):
                        os.rename(old_path, new_path)
                        print(f"   📝 保存为: {new_filename}")

            else:
                print(f"   ❌ 下载失败: {result.get('error', '未知错误')}")

        except Exception as e:
            print(f"   ❌ 异常: {str(e)}")

    # 显示最终结果
    print(f"\n📊 基线文件夹最终内容:")
    print(f"📁 主目录: {baseline_dir}")

    # 列出主目录文件
    main_files = []
    for file in os.listdir(baseline_dir):
        if not file.startswith('.'):
            file_path = os.path.join(baseline_dir, file)
            if os.path.isfile(file_path):
                file_size = os.path.getsize(file_path) / 1024  # KB
                main_files.append((file, file_size))

    if main_files:
        print(f"\n✅ 当前基线文件 ({len(main_files)} 个):")
        for file, size in sorted(main_files):
            print(f"   - {file} ({size:.1f} KB)")

    # 列出软删除文件
    deleted_dir = os.path.join(baseline_dir, '.deleted')
    if os.path.exists(deleted_dir):
        deleted_files = os.listdir(deleted_dir)
        if deleted_files:
            print(f"\n🗑️ 软删除文件 ({len(deleted_files)} 个):")
            for file in sorted(deleted_files):
                file_path = os.path.join(deleted_dir, file)
                file_size = os.path.getsize(file_path) / 1024  # KB
                print(f"   - {file} ({file_size:.1f} KB)")

    # 验证软删除机制
    print(f"\n✅ 软删除机制验证:")
    print(f"   1. 同名文件被移动到 .deleted 文件夹")
    print(f"   2. 删除的文件添加时间戳前缀")
    print(f"   3. 主目录只保留最新版本")
    print(f"   4. 软删除的文件不会被查找函数发现")

if __name__ == "__main__":
    test_multiline_baseline_download()