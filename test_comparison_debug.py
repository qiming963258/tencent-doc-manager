#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试CSV对比问题
验证为什么明明有差异的文件却检测到0个变更
"""

import csv
import json
from pathlib import Path
from production.core_modules.adaptive_table_comparator import AdaptiveTableComparator

def test_comparison_with_real_files():
    """使用实际下载的文件测试对比"""
    
    print("\n" + "="*60)
    print("CSV对比调试测试")
    print("="*60)
    
    # 实际文件路径
    baseline_file = "/root/projects/tencent-doc-manager/csv_versions/2025_W37/midweek/tencent_副本-测试版本-出国销售计划表-工作表1_20250911_1131_midweek_W37.csv"
    target_file = "/root/projects/tencent-doc-manager/csv_versions/2025_W37/midweek/tencent_副本-副本-测试版本-出国销售计划表-工作表1_20250911_1132_midweek_W37.csv"
    
    print(f"\n基线文件: {Path(baseline_file).name}")
    print(f"目标文件: {Path(target_file).name}")
    
    # 读取文件数据
    with open(baseline_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        baseline_data = list(reader)
    
    with open(target_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        target_data = list(reader)
    
    print(f"\n基线数据: {len(baseline_data)} 行")
    print(f"目标数据: {len(target_data)} 行")
    
    # 显示前几行的差异
    print("\n前5行差异示例:")
    for i in range(min(5, len(baseline_data), len(target_data))):
        if i < len(baseline_data) and i < len(target_data):
            baseline_row = baseline_data[i]
            target_row = target_data[i]
            if baseline_row != target_row:
                print(f"\n第{i+1}行有差异:")
                # 找出具体哪些列不同
                for j in range(min(len(baseline_row), len(target_row))):
                    if j < len(baseline_row) and j < len(target_row):
                        if baseline_row[j] != target_row[j]:
                            print(f"  列{j+1}: '{baseline_row[j][:50]}...' → '{target_row[j][:50]}...'")
    
    # 使用AdaptiveTableComparator进行对比
    print("\n" + "-"*60)
    print("使用AdaptiveTableComparator进行对比:")
    
    comparator = AdaptiveTableComparator()
    
    # 构造表格数据结构
    baseline_tables = [{"name": "基线表格", "data": baseline_data}]
    target_tables = [{"name": "目标表格", "data": target_data}]
    
    # 调用对比方法
    comparison_result = comparator.adaptive_compare_tables(
        current_tables=target_tables,
        reference_tables=baseline_tables
    )
    
    # 分析结果
    if 'comparison_results' in comparison_result and comparison_result['comparison_results']:
        result = comparison_result['comparison_results'][0]
        change_detection = result.get('change_detection_result', {})
        changes = change_detection.get('changes', [])
        
        print(f"\n检测到的变更数: {len(changes)}")
        
        if len(changes) == 0:
            print("\n⚠️ 问题确认：明明有差异但检测到0个变更！")
            print("\n可能的原因:")
            print("1. column_mapping为空或不正确")
            print("2. 列名匹配失败导致无法找到对应列")
            print("3. 标准化过程出现问题")
            
            # 检查column_mapping
            if 'matching_result' in result:
                mapping = result['matching_result'].get('mapping', {})
                print(f"\n列映射(column_mapping): {len(mapping)}个")
                if not mapping:
                    print("  ⚠️ 列映射为空！这就是问题所在。")
                else:
                    for k, v in list(mapping.items())[:5]:
                        print(f"  {k} → {v}")
        else:
            print("\n检测到的变更详情:")
            for change in changes[:5]:
                print(f"  行{change['row_index']+1}, 列{change['column_name']}: "
                      f"'{change['original_value']}' → '{change['new_value']}'")
    
    # 保存详细结果用于分析
    debug_file = "/tmp/comparison_debug_result.json"
    with open(debug_file, 'w', encoding='utf-8') as f:
        json.dump(comparison_result, f, ensure_ascii=False, indent=2)
    print(f"\n详细结果已保存到: {debug_file}")

def simple_direct_comparison():
    """直接简单对比，绕过复杂的列映射逻辑"""
    
    print("\n" + "="*60)
    print("简单直接对比（绕过列映射）")
    print("="*60)
    
    baseline_file = "/root/projects/tencent-doc-manager/csv_versions/2025_W37/midweek/tencent_副本-测试版本-出国销售计划表-工作表1_20250911_1131_midweek_W37.csv"
    target_file = "/root/projects/tencent-doc-manager/csv_versions/2025_W37/midweek/tencent_副本-副本-测试版本-出国销售计划表-工作表1_20250911_1132_midweek_W37.csv"
    
    with open(baseline_file, 'r', encoding='utf-8') as f:
        baseline_data = list(csv.reader(f))
    
    with open(target_file, 'r', encoding='utf-8') as f:
        target_data = list(csv.reader(f))
    
    changes = []
    for i in range(min(len(baseline_data), len(target_data))):
        for j in range(min(len(baseline_data[i]), len(target_data[i]))):
            if baseline_data[i][j] != target_data[i][j]:
                changes.append({
                    'row': i + 1,
                    'col': j + 1,
                    'old': baseline_data[i][j][:100],
                    'new': target_data[i][j][:100]
                })
    
    print(f"\n直接对比发现 {len(changes)} 个单元格差异")
    
    # 显示前10个差异
    for change in changes[:10]:
        print(f"  [{change['row']},{change['col']}]: '{change['old']}' → '{change['new']}'")
    
    return len(changes)

if __name__ == "__main__":
    # 运行测试
    test_comparison_with_real_files()
    
    # 运行简单直接对比
    actual_changes = simple_direct_comparison()
    
    print("\n" + "="*60)
    print("诊断结论")
    print("="*60)
    
    if actual_changes > 0:
        print(f"✅ 文件确实有 {actual_changes} 个差异")
        print("❌ AdaptiveTableComparator未能正确检测这些差异")
        print("\n建议修复方案:")
        print("1. 修复列映射逻辑，确保能正确匹配列")
        print("2. 或者使用更简单的逐单元格对比方法")
        print("3. 检查标准化过程是否正确处理了数据")