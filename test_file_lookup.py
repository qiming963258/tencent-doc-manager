#!/usr/bin/env python3
"""测试文件查找逻辑"""

import os
import glob
from pathlib import Path

# 模拟complete_workflow_ui.py中的查找逻辑
BASE_DIR = Path('/root/projects/tencent-doc-manager')
filename = 'tencent_副本-副本-测试版本-出国销售计划表_csv_20250909_2055_midweek_W37.csv'
safe_filename = os.path.basename(filename)

print(f"查找文件: {safe_filename}")
print("=" * 50)

# 检查csv_versions目录
csv_versions_dir = BASE_DIR / 'csv_versions'
print(f"CSV版本目录: {csv_versions_dir}")
print(f"目录存在: {csv_versions_dir.exists()}")

if csv_versions_dir.exists():
    # 搜索所有周数目录
    pattern = str(csv_versions_dir / '**' / safe_filename)
    print(f"搜索模式: {pattern}")
    
    matches = glob.glob(pattern, recursive=True)
    print(f"找到 {len(matches)} 个匹配文件:")
    
    for match in matches:
        file_path = Path(match)
        print(f"  - {file_path}")
        print(f"    文件大小: {file_path.stat().st_size} bytes")
        print(f"    文件存在: {file_path.exists()}")
        
    if matches:
        # 使用最新的文件
        latest_file = Path(max(matches, key=os.path.getmtime))
        print(f"\n选择最新文件: {latest_file}")
        print(f"文件可读: {os.access(latest_file, os.R_OK)}")