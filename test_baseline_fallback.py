#!/usr/bin/env python3
"""
测试基线文件查找降级机制
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, '/root/projects/tencent-doc-manager')

from production.core_modules.week_time_manager import WeekTimeManager

def test_baseline_fallback():
    """测试基线文件查找和降级"""
    
    print("=" * 60)
    print("测试基线文件查找降级机制")
    print("=" * 60)
    
    # 初始化时间管理器
    week_manager = WeekTimeManager()
    
    # 获取当前时间信息
    now = datetime.now()
    week_info = now.isocalendar()
    print(f"\n当前时间: {now}")
    print(f"当前是第{week_info[1]}周")
    print(f"今天是周{now.weekday()+1}（1=周一）")
    
    # 获取基线策略
    strategy, desc, target_week = week_manager.get_baseline_strategy()
    print(f"\n基线策略: {strategy}")
    print(f"描述: {desc}")
    print(f"目标周: W{target_week}")
    
    # 尝试查找基线文件
    print("\n尝试查找基线文件...")
    try:
        baseline_files, baseline_desc = week_manager.find_baseline_files()
        print(f"✅ 成功找到基线文件:")
        for file in baseline_files:
            print(f"  - {os.path.basename(file)}")
        print(f"描述: {baseline_desc}")
    except FileNotFoundError as e:
        print(f"❌ 查找失败: {e}")
        
        # 手动测试降级逻辑
        print("\n测试降级逻辑...")
        import glob
        
        current_week = week_info[1]
        previous_week = current_week - 1
        
        # 查找上周的基线文件
        prev_week_pattern = f"/root/projects/tencent-doc-manager/csv_versions/2025_W{previous_week:02d}/baseline/*.csv"
        prev_baseline_files = glob.glob(prev_week_pattern)
        
        if prev_baseline_files:
            print(f"✅ 找到上周（W{previous_week}）的基线文件:")
            for file in prev_baseline_files:
                print(f"  - {os.path.basename(file)}")
        else:
            print(f"❌ 上周也没有基线文件")
    
    # 列出所有可用的基线文件
    print("\n所有可用的基线文件:")
    base_dir = Path("/root/projects/tencent-doc-manager/csv_versions")
    for week_dir in sorted(base_dir.glob("2025_W*/baseline/*.csv")):
        print(f"  - {week_dir.relative_to(base_dir)}")

if __name__ == "__main__":
    test_baseline_fallback()