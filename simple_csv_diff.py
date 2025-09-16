#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单CSV差异对比器 - 无依赖版本
直接输出：行、列、差异内容
"""

import csv
import sys
import json
from pathlib import Path

def load_csv(file_path):
    """加载CSV文件"""
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            data = list(reader)
        return data
    except:
        with open(file_path, 'r', encoding='gbk') as f:
            reader = csv.reader(f)
            data = list(reader)
        return data

def preprocess_csv_data(data):
    """预处理CSV数据，处理多行标题"""
    if len(data) >= 3:
        first_row = data[0]
        if first_row[0] and not any(first_row[1:10]):  # 标题行检测
            if len(data) >= 4:
                header1 = data[1]
                header2 = data[2]
                
                # 合并列名
                merged_header = []
                max_cols = max(len(header1), len(header2))
                for i in range(max_cols):
                    col1 = header1[i] if i < len(header1) else ""
                    col2 = header2[i] if i < len(header2) else ""
                    final_col = col1 if col1.strip() else col2
                    merged_header.append(final_col)
                
                return [merged_header] + data[3:]
    
    return data

def compare_csv_simple(file1_path, file2_path, output_file=None):
    """
    简单对比两个CSV文件
    直接输出：行、列、差异内容
    """
    print(f"🔍 对比文件:")
    print(f"  基准文件: {Path(file1_path).name}")
    print(f"  当前文件: {Path(file2_path).name}")
    
    # 加载文件
    try:
        data1 = load_csv(file1_path)
        data2 = load_csv(file2_path)
    except Exception as e:
        print(f"❌ 文件加载失败: {e}")
        return
    
    # 预处理数据
    data1 = preprocess_csv_data(data1)
    data2 = preprocess_csv_data(data2)
    
    if not data1 or not data2:
        print("❌ 文件为空")
        return
    
    headers1 = data1[0]
    headers2 = data2[0]
    
    print(f"  基准文件: {len(data1)-1}行 × {len(headers1)}列")
    print(f"  当前文件: {len(data2)-1}行 × {len(headers2)}列")
    
    # 找到共同列
    common_columns = []
    for i, h1 in enumerate(headers1):
        if i < len(headers2):
            common_columns.append((i, h1, headers2[i]))
    
    print(f"  对比列数: {len(common_columns)}")
    print()
    
    # 差异列表
    differences = []
    diff_count = 0
    
    # 逐行逐列对比
    min_rows = min(len(data1)-1, len(data2)-1)
    
    for row_idx in range(min_rows):
        row1 = data1[row_idx + 1]  # 跳过标题行
        row2 = data2[row_idx + 1]
        
        for col_idx, col_name1, col_name2 in common_columns:
            if col_idx < len(row1) and col_idx < len(row2):
                old_val = str(row1[col_idx]).strip()
                new_val = str(row2[col_idx]).strip()
                
                if old_val != new_val:
                    diff_count += 1
                    column_name = col_name1 if col_name1.strip() else col_name2
                    
                    diff = {
                        "序号": diff_count,
                        "行号": row_idx + 1,
                        "列名": column_name,
                        "列索引": col_idx + 1,
                        "原值": old_val,
                        "新值": new_val,
                        "位置": f"行{row_idx+1}列{col_idx+1}({column_name})"
                    }
                    differences.append(diff)
    
    # 输出结果
    print("="*80)
    print("📊 差异对比结果")
    print("="*80)
    print(f"总差异数: {diff_count}")
    print()
    
    if differences:
        print("📋 详细差异列表:")
        print("-" * 80)
        
        for diff in differences[:20]:  # 显示前20个差异
            print(f"{diff['序号']:3d}. {diff['位置']}")
            print(f"     原值: \"{diff['原值']}\"")
            print(f"     新值: \"{diff['新值']}\"")
            print()
        
        if len(differences) > 20:
            print(f"... 还有 {len(differences) - 20} 个差异")
            print()
        
        # 保存完整结果
        if output_file:
            result = {
                "comparison_summary": {
                    "baseline_file": Path(file1_path).name,
                    "current_file": Path(file2_path).name,
                    "total_differences": diff_count,
                    "rows_compared": min_rows,
                    "columns_compared": len(common_columns)
                },
                "differences": differences
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 完整结果已保存: {output_file}")
        
        # 返回核心参数
        return {
            "total_differences": diff_count,
            "differences": differences
        }
    else:
        print("✅ 两个文件内容完全相同，无差异")
        return {"total_differences": 0, "differences": []}

def main():
    """命令行入口"""
    if len(sys.argv) < 3:
        print("用法: python3 simple_csv_diff.py 基准文件.csv 当前文件.csv [输出文件.json]")
        return
    
    file1 = sys.argv[1]
    file2 = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) > 3 else None
    
    compare_csv_simple(file1, file2, output)

if __name__ == "__main__":
    main()