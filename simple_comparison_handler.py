#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的对比分析处理器
使用项目现有的CSV对比功能
"""

import csv
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

def simple_csv_compare(baseline_path: str, target_path: str) -> Dict[str, Any]:
    """
    专业CSV对比功能 - 使用增强的单元格级别对比算法
    
    Args:
        baseline_path: 基线CSV文件路径
        target_path: 目标CSV文件路径
        
    Returns:
        dict: 对比结果
    """
    # 使用增强的CSV对比算法
    from enhanced_csv_comparison import enhanced_csv_compare
    
    try:
        # 先检查文件路径是否相同
        if baseline_path == target_path:
            return {
                'error': f"错误：基线文件和目标文件路径相同 ({baseline_path})，可能是下载模块的问题",
                'similarity_score': 1.0,
                'total_changes': 0,
                'added_rows': 0,
                'deleted_rows': 0,
                'modified_rows': 0,
                'details': {
                    'issue_type': 'same_file_path',
                    'file_path': baseline_path
                }
            }
        
        # 执行增强的CSV对比
        result = enhanced_csv_compare(baseline_path, target_path)
        
        # 使用统一接口获取简化格式结果
        try:
            from unified_csv_comparator import UnifiedCSVComparator
            comparator = UnifiedCSVComparator()
            output_dir = '/root/projects/tencent-doc-manager/comparison_results'
            unified_result = comparator.compare(baseline_path, target_path, output_dir)
            
            # 合并简化格式的额外信息
            if 'modified_columns' in unified_result:
                result['simplified_columns'] = unified_result['modified_columns']
                result['format_version'] = unified_result.get('format_version', 'simplified_v1.0')
        except:
            # 如果统一接口不可用，继续使用增强算法的结果
            pass
        
        return result
        
    except Exception as e:
        return {
            'error': str(e),
            'similarity_score': 0,
            'total_changes': 0,
            'added_rows': 0,
            'deleted_rows': 0,
            'modified_rows': 0,
            'details': {}
        }

def save_comparison_result(result: Dict[str, Any], output_path: str) -> bool:
    """
    保存对比结果到JSON文件
    
    Args:
        result: 对比结果
        output_path: 输出文件路径
        
    Returns:
        bool: 是否成功
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存结果失败: {e}")
        return False

if __name__ == "__main__":
    # 测试用例
    test_baseline = "/root/projects/tencent-doc-manager/comparison_baseline/test.csv"
    test_target = "/root/projects/tencent-doc-manager/comparison_target/test.csv"
    
    if Path(test_baseline).exists() and Path(test_target).exists():
        result = simple_csv_compare(test_baseline, test_target)
        print(json.dumps(result, ensure_ascii=False, indent=2))