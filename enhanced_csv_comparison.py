#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强的CSV对比算法 - 单元格级别精确对比
符合CSV对比规范要求，支持不同列数的文件对比
"""

import csv
from typing import Dict, List, Any, Tuple
import difflib

def enhanced_csv_compare(baseline_path: str, target_path: str) -> Dict[str, Any]:
    """
    专业CSV对比功能 - 单元格级别对比
    
    Args:
        baseline_path: 基线CSV文件路径
        target_path: 目标CSV文件路径
        
    Returns:
        dict: 详细的对比结果，包含相似度评分
    """
    
    # 读取文件
    with open(baseline_path, 'r', encoding='utf-8') as f:
        baseline_data = list(csv.reader(f))
    
    with open(target_path, 'r', encoding='utf-8') as f:
        target_data = list(csv.reader(f))
    
    # 基本信息
    baseline_rows = len(baseline_data)
    target_rows = len(target_data)
    baseline_cols = len(baseline_data[0]) if baseline_data else 0
    target_cols = len(target_data[0]) if target_data else 0
    
    # 处理列数不同的情况 - 以较少的列数为准进行对比
    min_cols = min(baseline_cols, target_cols)
    max_cols = max(baseline_cols, target_cols)
    
    # 统计变量
    total_cells_compared = 0
    identical_cells = 0
    modified_cells = 0
    added_rows = []
    deleted_rows = []
    modified_rows = []
    
    # 行级别对比 - 使用difflib进行智能匹配
    # 将列表转换为元组以便比较 - 仅比较共同的列数
    # 这样确保不同列数的文件也能正确对比
    baseline_tuples = [tuple(row[:min_cols] if len(row) >= min_cols else row + ['']*(min_cols-len(row))) 
                       for row in baseline_data]
    target_tuples = [tuple(row[:min_cols] if len(row) >= min_cols else row + ['']*(min_cols-len(row))) 
                     for row in target_data]
    matcher = difflib.SequenceMatcher(None, baseline_tuples, target_tuples)
    
    # 处理每个操作码
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            # 相同的行结构，但仍需检查每个单元格（因为可能有细微差异）
            for baseline_idx, target_idx in zip(range(i1, i2), range(j1, j2)):
                baseline_row = baseline_data[baseline_idx]
                target_row = target_data[target_idx]
                
                # 对比共同列的单元格
                row_has_changes = False
                for col_idx in range(min_cols):
                    total_cells_compared += 1
                    baseline_cell = baseline_row[col_idx] if col_idx < len(baseline_row) else ""
                    target_cell = target_row[col_idx] if col_idx < len(target_row) else ""
                    
                    if baseline_cell == target_cell:
                        identical_cells += 1
                    else:
                        modified_cells += 1
                        row_has_changes = True
                
                if row_has_changes and baseline_idx not in modified_rows:
                    modified_rows.append(baseline_idx)
        
        elif tag == 'replace':
            # 被替换的行 - 也进行单元格级别对比
            # 对于替换的行，仍然进行单元格级别的对比
            # 这能更准确地反映实际的修改情况
            for baseline_idx in range(i1, min(i2, i1 + (j2-j1))):
                target_idx = j1 + (baseline_idx - i1)
                if target_idx < j2:
                    baseline_row = baseline_data[baseline_idx]
                    target_row = target_data[target_idx]
                    
                    # 对比单元格
                    row_has_changes = False
                    for col_idx in range(min_cols):
                        total_cells_compared += 1
                        baseline_cell = baseline_row[col_idx] if col_idx < len(baseline_row) else ""
                        target_cell = target_row[col_idx] if col_idx < len(target_row) else ""
                        
                        if baseline_cell == target_cell:
                            identical_cells += 1
                        else:
                            modified_cells += 1
                            row_has_changes = True
                    
                    if row_has_changes:
                        modified_rows.append(baseline_idx)
            
            # 处理行数不匹配的情况
            if i2-i1 > j2-j1:
                # 基线有更多行 - 标记为删除
                for i in range(i1 + (j2-j1), i2):
                    deleted_rows.append(i)
            elif j2-j1 > i2-i1:
                # 目标有更多行 - 标记为新增
                for j in range(j1 + (i2-i1), j2):
                    added_rows.append(j)
                
        elif tag == 'delete':
            # 删除的行
            for i in range(i1, i2):
                deleted_rows.append(i)
                
        elif tag == 'insert':
            # 新增的行
            for j in range(j1, j2):
                added_rows.append(j)
    
    # 计算相似度分数（根据规范）
    # 权重分配：单元格内容0.6，表格结构0.3，行数差异0.1
    
    # 1. 单元格内容相似度
    if total_cells_compared > 0:
        cell_score = identical_cells / total_cells_compared
    else:
        cell_score = 0 if (baseline_rows > 0 or target_rows > 0) else 1
    
    # 2. 表格结构相似度（列数相似度）
    if max_cols > 0:
        structure_score = min_cols / max_cols
    else:
        structure_score = 1
    
    # 3. 行数差异相似度
    max_rows = max(baseline_rows, target_rows)
    if max_rows > 0:
        row_score = 1 - abs(baseline_rows - target_rows) / max_rows
    else:
        row_score = 1
    
    # 加权计算总相似度
    similarity = (
        cell_score * 0.6 +
        structure_score * 0.3 +
        row_score * 0.1
    )
    
    # 收集样本数据
    def get_row_sample(data: List[List[str]], indices: List[int], limit: int = 5) -> List[str]:
        """获取行样本"""
        samples = []
        for idx in indices[:limit]:
            if idx < len(data):
                row = data[idx]
                # 限制每行显示的字符数
                row_str = ','.join(row[:min(len(row), 10)])
                if len(row_str) > 150:
                    row_str = row_str[:150] + "..."
                samples.append(f"{idx},{row_str}")
        return samples
    
    # 构建结果
    result = {
        'total_changes': len(added_rows) + len(deleted_rows) + len(modified_rows),
        'added_rows': len(added_rows),
        'deleted_rows': len(deleted_rows),
        'modified_rows': len(modified_rows),
        'similarity_score': round(similarity, 3),
        'details': {
            'baseline_total_rows': baseline_rows,
            'target_total_rows': target_rows,
            'baseline_columns': baseline_cols,
            'target_columns': target_cols,
            'common_columns': min_cols,
            'total_cells_compared': total_cells_compared,
            'identical_cells': identical_cells,
            'modified_cells': modified_cells,
            'cell_similarity': round(cell_score, 3),
            'structure_similarity': round(structure_score, 3),
            'row_similarity': round(row_score, 3)
        },
        'added_samples': get_row_sample(target_data, added_rows),
        'deleted_samples': get_row_sample(baseline_data, deleted_rows),
        'comparator_type': 'EnhancedCSVComparator'
    }
    
    # 添加调试信息
    if baseline_cols != target_cols:
        result['warning'] = f"列数不匹配：基线 {baseline_cols} 列，目标 {target_cols} 列。仅对比前 {min_cols} 列。"
    
    return result


def test_comparison():
    """测试对比功能"""
    baseline = "/root/projects/tencent-doc-manager/csv_versions/2025_W36/midweek/tencent_副本-测试版本-出国销售计划表-工作表1_csv_20250905_0033_midweek_W36.csv"
    target = "/root/projects/tencent-doc-manager/csv_versions/2025_W36/midweek/tencent_副本-副本-测试版本-出国销售计划表-工作表1_csv_20250905_0034_midweek_W36.csv"
    
    result = enhanced_csv_compare(baseline, target)
    
    print("📊 增强CSV对比结果:")
    print(f"相似度: {result['similarity_score']*100:.1f}%")
    print(f"总变更: {result['total_changes']}")
    print(f"详细信息: {result['details']}")
    if 'warning' in result:
        print(f"⚠️ 警告: {result['warning']}")
    
    return result


if __name__ == "__main__":
    test_comparison()