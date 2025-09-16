#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进的CSV对比分析处理器
支持字段级别的变化检测和ID匹配
"""

import csv
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple

def improved_csv_compare(baseline_path: str, target_path: str) -> Dict[str, Any]:
    """
    改进的CSV对比功能
    - 支持基于ID的行匹配
    - 检测字段级别的变化
    - 提供更准确的相似度计算
    
    Args:
        baseline_path: 基线CSV文件路径
        target_path: 目标CSV文件路径
        
    Returns:
        dict: 对比结果
    """
    result = {
        'total_changes': 0,
        'added_rows': 0,
        'modified_rows': 0,
        'deleted_rows': 0,
        'field_changes': 0,  # 新增：字段级别变化统计
        'similarity_score': 0,
        'details': []
    }
    
    try:
        # 先检查文件路径是否相同
        if baseline_path == target_path:
            result['error'] = f"错误：基线文件和目标文件路径相同 ({baseline_path})"
            result['similarity_score'] = 1.0
            return result
        
        # 读取基线文件
        baseline_data = {}
        baseline_headers = []
        with open(baseline_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            baseline_headers = reader.fieldnames or []
            for row in reader:
                # 假设第一列是ID
                row_id = row.get(baseline_headers[0]) if baseline_headers else None
                if row_id:
                    baseline_data[row_id] = row
        
        # 读取目标文件
        target_data = {}
        target_headers = []
        with open(target_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            target_headers = reader.fieldnames or []
            for row in reader:
                # 假设第一列是ID
                row_id = row.get(target_headers[0]) if target_headers else None
                if row_id:
                    target_data[row_id] = row
        
        # 分析差异
        baseline_ids = set(baseline_data.keys())
        target_ids = set(target_data.keys())
        
        # 新增的行
        added_ids = target_ids - baseline_ids
        result['added_rows'] = len(added_ids)
        
        # 删除的行
        deleted_ids = baseline_ids - target_ids
        result['deleted_rows'] = len(deleted_ids)
        
        # 修改的行和字段级别的变化
        common_ids = baseline_ids & target_ids
        modified_rows = 0
        total_field_changes = 0
        field_change_details = []
        
        for row_id in common_ids:
            baseline_row = baseline_data[row_id]
            target_row = target_data[row_id]
            
            # 比较每个字段
            row_changed = False
            field_changes = []
            
            # 使用所有可能的列名
            all_columns = set(baseline_headers) | set(target_headers)
            for col in all_columns:
                baseline_val = baseline_row.get(col, '')
                target_val = target_row.get(col, '')
                
                if baseline_val != target_val:
                    row_changed = True
                    field_changes.append({
                        'column': col,
                        'old_value': baseline_val,
                        'new_value': target_val
                    })
                    total_field_changes += 1
            
            if row_changed:
                modified_rows += 1
                if len(field_change_details) < 5:  # 只记录前5个变化的详情
                    field_change_details.append({
                        'row_id': row_id,
                        'changes': field_changes[:3]  # 每行最多显示3个字段变化
                    })
        
        result['modified_rows'] = modified_rows
        result['field_changes'] = total_field_changes
        
        # 计算总变化
        result['total_changes'] = result['added_rows'] + result['deleted_rows'] + result['modified_rows']
        
        # 计算相似度（更精细的算法）
        total_rows = len(baseline_ids | target_ids)
        if total_rows > 0:
            # 完全相同的行数
            unchanged_rows = len(common_ids) - modified_rows
            
            # 考虑字段级别的相似度
            if len(common_ids) > 0 and baseline_headers and target_headers:
                # 计算平均每行的字段数
                avg_fields = len(all_columns)
                # 计算字段级别的相似度
                total_possible_fields = len(common_ids) * avg_fields
                if total_possible_fields > 0:
                    field_similarity = 1 - (total_field_changes / total_possible_fields)
                else:
                    field_similarity = 1.0
            else:
                field_similarity = 0
            
            # 综合计算相似度
            # 50%权重给行级别的匹配，50%权重给字段级别的匹配
            row_similarity = unchanged_rows / total_rows if total_rows > 0 else 0
            result['similarity_score'] = (row_similarity * 0.5) + (field_similarity * 0.5)
        else:
            result['similarity_score'] = 1.0 if not baseline_data and not target_data else 0.0
        
        # 添加详细信息
        result['details'] = {
            'baseline_total_rows': len(baseline_data),
            'target_total_rows': len(target_data),
            'common_rows': len(common_ids),
            'unchanged_rows': len(common_ids) - modified_rows,
            'baseline_columns': len(baseline_headers),
            'target_columns': len(target_headers),
            'field_change_details': field_change_details
        }
        
        # 添加变化示例
        result['added_samples'] = [f"ID={id}: {target_data[id]}" for id in list(added_ids)[:3]]
        result['deleted_samples'] = [f"ID={id}: {baseline_data[id]}" for id in list(deleted_ids)[:3]]
        result['modified_samples'] = field_change_details[:3]
        
    except Exception as e:
        result['error'] = str(e)
        result['similarity_score'] = 0
    
    return result

def test_improved_algorithm():
    """测试改进的算法"""
    baseline = '/root/projects/tencent-doc-manager/csv_versions/2025_W36/baseline/tencent_test_comparison_csv_20250903_1200_baseline_W36.csv'
    target = '/root/projects/tencent-doc-manager/csv_versions/2025_W36/midweek/tencent_test_comparison_csv_20250904_1000_midweek_W36.csv'
    
    if Path(baseline).exists() and Path(target).exists():
        result = improved_csv_compare(baseline, target)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return result
    else:
        print("测试文件不存在")
        return None

if __name__ == "__main__":
    test_improved_algorithm()