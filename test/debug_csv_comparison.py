#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV对比算法深度分析和调试脚本
"""

import csv
import json
from pathlib import Path
import sys
sys.path.append('/root/projects/tencent-doc-manager/production/core_modules')
from real_data_loader import RealDataLoader

def analyze_csv_comparison():
    """深度分析CSV对比算法中的问题"""
    
    print("=== CSV对比算法深度分析 ===\n")
    
    loader = RealDataLoader()
    
    # 获取真实文件
    real_files = loader.get_real_csv_files()
    print(f"1. 发现 {len(real_files)} 个文件对:")
    
    for i, file_info in enumerate(real_files):
        print(f"   [{i}] {file_info['name']}")
        print(f"       Previous: {file_info['previous_file']}")
        print(f"       Current:  {file_info['current_file']}")
        
        # 检查文件存在性
        prev_exists = Path(file_info['previous_file']).exists()
        curr_exists = Path(file_info['current_file']).exists()
        print(f"       文件存在: Previous={prev_exists}, Current={curr_exists}")
        print()
    
    # 选择第一个存在的文件对进行深度分析
    test_file = None
    for file_info in real_files:
        prev_path = Path(file_info['previous_file'])
        curr_path = Path(file_info['current_file'])
        if prev_path.exists() and curr_path.exists():
            test_file = file_info
            break
    
    if not test_file:
        print("❌ 未找到可用的文件对进行测试")
        return
    
    print(f"2. 选择测试文件: {test_file['name']}")
    print(f"   Previous: {test_file['previous_file']}")
    print(f"   Current:  {test_file['current_file']}")
    print()
    
    # 手动读取CSV文件分析结构
    prev_file = test_file['previous_file']
    curr_file = test_file['current_file']
    
    print("3. CSV文件结构分析:")
    
    # 读取previous文件
    with open(prev_file, 'r', encoding='utf-8-sig') as f:
        prev_reader = csv.reader(f)
        prev_data = list(prev_reader)
    
    # 读取current文件
    with open(curr_file, 'r', encoding='utf-8-sig') as f:
        curr_reader = csv.reader(f)
        curr_data = list(curr_reader)
    
    print(f"   Previous文件: {len(prev_data)}行 x {len(prev_data[0]) if prev_data else 0}列")
    print(f"   Current文件:  {len(curr_data)}行 x {len(curr_data[0]) if curr_data else 0}列")
    
    # 显示前几行数据
    print("\n   Previous文件内容(前5行):")
    for i, row in enumerate(prev_data[:5]):
        print(f"     行{i}: {row}")
    
    print("\n   Current文件内容(前5行):")
    for i, row in enumerate(curr_data[:5]):
        print(f"     行{i}: {row}")
    
    print("\n4. 调用load_comparison_result方法分析:")
    comparison_result = loader.load_comparison_result(prev_file, curr_file)
    
    print(f"   总差异数: {comparison_result['total_differences']}")
    print(f"   Previous行数: {comparison_result.get('previous_rows', 'N/A')}")
    print(f"   Current行数:  {comparison_result.get('current_rows', 'N/A')}")
    print(f"   Previous列数: {comparison_result.get('previous_cols', 'N/A')}")
    print(f"   Current列数:  {comparison_result.get('current_cols', 'N/A')}")
    
    # 详细分析差异
    differences = comparison_result['differences']
    print(f"\n5. 差异详细分析 (共{len(differences)}个差异):")
    
    if differences:
        # 显示前10个差异
        for i, diff in enumerate(differences[:10]):
            print(f"   差异{i+1}:")
            print(f"     位置: 行{diff['row']}, 列{diff['col']}")
            print(f"     旧值: '{diff['old_value']}'")
            print(f"     新值: '{diff['new_value']}'")
            print(f"     列名: {diff['column_name']}")
            
            # 验证差异位置的准确性
            actual_old = ''
            actual_new = ''
            
            if diff['row'] < len(prev_data) and diff['col'] < len(prev_data[diff['row']]):
                actual_old = prev_data[diff['row']][diff['col']]
            if diff['row'] < len(curr_data) and diff['col'] < len(curr_data[diff['row']]):
                actual_new = curr_data[diff['row']][diff['col']]
                
            verification = "✅" if (actual_old == diff['old_value'] and actual_new == diff['new_value']) else "❌"
            print(f"     验证: {verification} (实际: '{actual_old}' -> '{actual_new}')")
            print()
    
    print("6. 热力图生成分析:")
    heatmap_data = loader.generate_heatmap_data([test_file])
    
    matrix = heatmap_data['matrix']
    cols = heatmap_data['cols']
    
    print(f"   热力图矩阵大小: {len(matrix)}行 x {cols}列")
    print(f"   列名数量: {len(heatmap_data['column_names'])}")
    
    # 分析热力图映射逻辑的问题
    print("\n7. 热力图映射逻辑分析:")
    
    if differences:
        print("   差异列索引分布:")
        col_distribution = {}
        for diff in differences:
            col_idx = diff['col']
            mapped_col = min(col_idx, cols - 1)  # 这是第269行的映射逻辑
            
            if col_idx not in col_distribution:
                col_distribution[col_idx] = 0
            col_distribution[col_idx] += 1
            
            if col_idx != mapped_col:
                print(f"   ⚠️  列{col_idx}被映射到列{mapped_col} (数据丢失)")
        
        print(f"   原始差异涉及列: {sorted(col_distribution.keys())}")
        print(f"   最大列索引: {max(col_distribution.keys()) if col_distribution else 0}")
        print(f"   热力图列数限制: {cols}")
    
    # 分析热团形成逻辑
    print("\n8. 热团形成分析:")
    if matrix:
        row = matrix[0]
        print(f"   第一行热力值: {[f'{v:.3f}' for v in row[:10]]}")
        
        # 统计不同热力值的分布
        heat_distribution = {}
        for row in matrix:
            for val in row:
                val_range = round(val, 1)
                if val_range not in heat_distribution:
                    heat_distribution[val_range] = 0
                heat_distribution[val_range] += 1
        
        print("   热力值分布:")
        for heat_val, count in sorted(heat_distribution.items()):
            print(f"     {heat_val}: {count}个单元格")
    
    print("\n=== 问题总结 ===")
    issues = []
    
    # 检查是否真正读取了CSV文件
    if comparison_result['total_differences'] > 0:
        issues.append("✅ CSV文件读取和对比功能正常")
    else:
        issues.append("⚠️  没有发现差异，可能是文件相同或读取有问题")
    
    # 检查差异位置准确性
    accurate_diffs = 0
    for diff in differences[:5]:  # 检查前5个差异
        actual_old = ''
        actual_new = ''
        
        if diff['row'] < len(prev_data) and diff['col'] < len(prev_data[diff['row']]):
            actual_old = prev_data[diff['row']][diff['col']]
        if diff['row'] < len(curr_data) and diff['col'] < len(curr_data[diff['row']]):
            actual_new = curr_data[diff['row']][diff['col']]
            
        if actual_old == diff['old_value'] and actual_new == diff['new_value']:
            accurate_diffs += 1
    
    if accurate_diffs == len(differences[:5]):
        issues.append("✅ 差异位置索引准确")
    else:
        issues.append(f"❌ 差异位置索引不准确 ({accurate_diffs}/{len(differences[:5])})")
    
    # 检查映射逻辑问题
    max_col_idx = max([diff['col'] for diff in differences]) if differences else 0
    if max_col_idx >= cols:
        issues.append(f"❌ 列映射问题: 最大列索引{max_col_idx} >= 热力图列数{cols}，会导致数据丢失")
    else:
        issues.append("✅ 列映射在合理范围内")
    
    # 检查热团形成
    if matrix and any(any(val >= 0.3 for val in row) for row in matrix):
        issues.append("✅ 热团形成正常，热力值足够显示差异")
    else:
        issues.append("⚠️  热团可能不够明显，建议调整热力值")
    
    for issue in issues:
        print(issue)
    
    return comparison_result, heatmap_data

if __name__ == "__main__":
    analyze_csv_comparison()