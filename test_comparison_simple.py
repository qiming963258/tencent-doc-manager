#!/usr/bin/env python3
"""简化版对比测试 - 直接使用CSV文件"""

import csv
import json
import os
from datetime import datetime

def read_csv_file(file_path):
    """读取CSV文件"""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            data.append(row)
    return data

def compare_csv_files(baseline_file, target_file):
    """简单对比两个CSV文件"""
    print(f"\n📊 对比CSV文件")
    print(f"基线: {os.path.basename(baseline_file)}")
    print(f"目标: {os.path.basename(target_file)}")

    baseline_data = read_csv_file(baseline_file)
    target_data = read_csv_file(target_file)

    print(f"\n基线文件: {len(baseline_data)} 行 × {len(baseline_data[0]) if baseline_data else 0} 列")
    print(f"目标文件: {len(target_data)} 行 × {len(target_data[0]) if target_data else 0} 列")

    # 查找差异
    changes = []

    # 比较行数
    max_rows = max(len(baseline_data), len(target_data))

    for row_idx in range(max_rows):
        if row_idx >= len(baseline_data):
            # 新增行
            changes.append({
                "type": "row_added",
                "row": row_idx,
                "content": target_data[row_idx][:5] if row_idx < len(target_data) else []
            })
        elif row_idx >= len(target_data):
            # 删除行
            changes.append({
                "type": "row_deleted",
                "row": row_idx,
                "content": baseline_data[row_idx][:5]
            })
        else:
            # 比较单元格
            baseline_row = baseline_data[row_idx]
            target_row = target_data[row_idx]

            max_cols = max(len(baseline_row), len(target_row))

            for col_idx in range(max_cols):
                baseline_val = baseline_row[col_idx] if col_idx < len(baseline_row) else ""
                target_val = target_row[col_idx] if col_idx < len(target_row) else ""

                if baseline_val != target_val:
                    changes.append({
                        "type": "cell_changed",
                        "row": row_idx,
                        "col": col_idx,
                        "old_value": baseline_val[:50],
                        "new_value": target_val[:50]
                    })

    return changes

def main():
    """主测试函数"""

    print("========== CSV对比测试 ==========")

    # 文件路径
    baseline_file = "/root/projects/tencent-doc-manager/csv_versions/2025_W38/baseline/tencent_出国销售计划表_20250915_0145_baseline_W38.csv"
    target_file = "/root/projects/tencent-doc-manager/csv_versions/2025_W38/midweek/tencent_111测试版本-出国销售计划表-工作表1_20250915_0239_midweek_W38.csv"

    if not os.path.exists(baseline_file):
        print(f"❌ 基线文件不存在: {baseline_file}")
        return

    if not os.path.exists(target_file):
        print(f"❌ 目标文件不存在: {target_file}")
        return

    # 执行对比
    changes = compare_csv_files(baseline_file, target_file)

    print(f"\n🔍 发现 {len(changes)} 处变更")

    # 显示前20个变更
    print("\n📝 变更详情（前20个）:")
    for i, change in enumerate(changes[:20], 1):
        if change['type'] == 'cell_changed':
            print(f"  {i}. 单元格[行{change['row']+1},列{change['col']+1}]:")
            print(f"     旧值: {change['old_value']}")
            print(f"     新值: {change['new_value']}")
        elif change['type'] == 'row_added':
            print(f"  {i}. 新增行{change['row']+1}: {change['content']}")
        elif change['type'] == 'row_deleted':
            print(f"  {i}. 删除行{change['row']+1}: {change['content']}")

    # 统计变更类型
    change_stats = {}
    for change in changes:
        change_type = change['type']
        change_stats[change_type] = change_stats.get(change_type, 0) + 1

    print(f"\n📊 变更统计:")
    for change_type, count in change_stats.items():
        print(f"  {change_type}: {count}")

    # 查找关键变更（包含"123"的变更）
    key_changes = []
    for change in changes:
        if change['type'] == 'cell_changed':
            if '123' in change['new_value'] or '123' in change['old_value']:
                key_changes.append(change)

    print(f"\n⚠️ 包含'123'的关键变更: {len(key_changes)} 处")
    for i, change in enumerate(key_changes[:10], 1):
        print(f"  {i}. 单元格[行{change['row']+1},列{change['col']+1}]:")
        print(f"     旧值: {change['old_value']}")
        print(f"     新值: {change['new_value']}")

    # 保存结果
    result = {
        "test_time": datetime.now().isoformat(),
        "baseline_file": baseline_file,
        "target_file": target_file,
        "total_changes": len(changes),
        "change_stats": change_stats,
        "key_changes_count": len(key_changes),
        "sample_changes": changes[:20]
    }

    result_file = f"/root/projects/tencent-doc-manager/comparison_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 测试结果保存到: {result_file}")

    return result

if __name__ == "__main__":
    main()