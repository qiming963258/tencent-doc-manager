#!/usr/bin/env python3
"""
测试智能基线下载和规范化存储功能
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, '/root/projects/tencent-doc-manager')

def test_baseline_storage_logic():
    """测试基线存储逻辑"""
    
    print("=" * 60)
    print("测试智能基线下载和存储逻辑")
    print("=" * 60)
    
    # 获取当前时间信息
    now = datetime.now()
    week_info = now.isocalendar()
    current_year = week_info[0]
    current_week = week_info[1]
    weekday = now.weekday()  # 0=周一
    hour = now.hour
    
    print(f"\n当前时间: {now}")
    print(f"当前是{current_year}年第{current_week}周")
    print(f"今天是周{weekday+1}（0=周一）")
    print(f"现在是{hour}点")
    
    # 判断基线应该存储到哪一周
    if weekday < 1 or (weekday == 1 and hour < 12):
        # 周一全天 OR 周二12点前 -> 使用上周
        target_week = current_week - 1
        print(f"\n根据规范：基线应存储到上周（W{target_week}）")
    else:
        # 周二12点后至周日 -> 使用本周
        target_week = current_week
        print(f"\n根据规范：基线应存储到本周（W{target_week}）")
    
    # 显示目标存储路径
    baseline_dir = Path(f"/root/projects/tencent-doc-manager/csv_versions/{current_year}_W{target_week:02d}/baseline")
    print(f"\n目标存储路径: {baseline_dir}")
    
    # 生成示例文件名
    timestamp = now.strftime("%Y%m%d_%H%M")
    example_name = f"tencent_测试文档_{timestamp}_baseline_W{target_week:02d}.csv"
    print(f"规范化文件名示例: {example_name}")
    
    # 检查目录是否存在
    if baseline_dir.exists():
        print(f"\n✅ 目录已存在")
        # 列出目录内容
        files = list(baseline_dir.glob("*"))
        if files:
            print(f"目录中现有{len(files)}个文件:")
            for file in files:
                print(f"  - {file.name}")
        else:
            print("目录为空")
    else:
        print(f"\n⚠️ 目录不存在，下载时将自动创建")
    
    # 测试完整的下载和存储流程
    print("\n" + "=" * 60)
    print("完整功能说明:")
    print("=" * 60)
    print("1. 用户输入基线URL并点击执行")
    print("2. 系统下载基线文档到临时目录")
    print("3. 系统自动判断当前应该使用哪一周")
    print(f"4. 系统生成规范化文件名（包含W{target_week}标记）")
    print(f"5. 系统将文件移动到正确的baseline目录")
    print("6. WeekTimeManager能够找到并使用该基线文件")
    
    # 显示系统将查找的文件模式
    print(f"\n系统查找文件模式:")
    print(f"  - *_baseline_W{target_week:02d}.csv")
    print(f"  - *_baseline_W{target_week:02d}.xlsx")
    print(f"  - *_baseline_W{target_week:02d}.xls")

if __name__ == "__main__":
    test_baseline_storage_logic()