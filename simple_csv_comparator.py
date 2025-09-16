#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单CSV对比器
不依赖复杂的列映射，直接逐单元格对比
"""

import csv
import json
from typing import List, Dict, Any
from pathlib import Path

class SimpleCsvComparator:
    """简单直接的CSV对比器"""
    
    def compare_csv_files(self, baseline_file: str, target_file: str) -> Dict[str, Any]:
        """
        对比两个CSV文件，返回所有变更
        
        Args:
            baseline_file: 基线文件路径
            target_file: 目标文件路径
            
        Returns:
            包含变更信息的字典
        """
        # 读取文件
        with open(baseline_file, 'r', encoding='utf-8-sig') as f:
            baseline_data = list(csv.reader(f))
        
        with open(target_file, 'r', encoding='utf-8-sig') as f:
            target_data = list(csv.reader(f))
        
        changes = []
        high_risk_count = 0
        medium_risk_count = 0
        low_risk_count = 0
        
        # 逐单元格对比
        max_rows = max(len(baseline_data), len(target_data))
        for row_idx in range(max_rows):
            # 获取当前行数据
            baseline_row = baseline_data[row_idx] if row_idx < len(baseline_data) else []
            target_row = target_data[row_idx] if row_idx < len(target_data) else []
            
            max_cols = max(len(baseline_row), len(target_row))
            
            for col_idx in range(max_cols):
                baseline_value = baseline_row[col_idx] if col_idx < len(baseline_row) else ""
                target_value = target_row[col_idx] if col_idx < len(target_row) else ""
                
                # 忽略空值变化
                if not baseline_value and not target_value:
                    continue
                
                # 检测变更
                if baseline_value != target_value:
                    # 简单的风险评估
                    risk_level = self._assess_risk(baseline_value, target_value, row_idx, col_idx)
                    
                    change = {
                        "row": row_idx + 1,  # 人类可读的行号（从1开始）
                        "column": col_idx + 1,  # 人类可读的列号（从1开始）
                        "cell_reference": f"{chr(65 + col_idx % 26)}{row_idx + 1}",  # Excel格式
                        "old_value": baseline_value[:200],  # 限制长度
                        "new_value": target_value[:200],
                        "risk_level": risk_level,
                        "change_type": self._get_change_type(baseline_value, target_value)
                    }
                    
                    changes.append(change)
                    
                    # 统计风险等级
                    if risk_level == "high":
                        high_risk_count += 1
                    elif risk_level == "medium":
                        medium_risk_count += 1
                    else:
                        low_risk_count += 1
        
        # 返回结果
        return {
            "changes": changes,
            "statistics": {
                "total_changes": len(changes),
                "high_risk_count": high_risk_count,
                "medium_risk_count": medium_risk_count,
                "low_risk_count": low_risk_count,
                "baseline_rows": len(baseline_data),
                "target_rows": len(target_data),
                "baseline_file": Path(baseline_file).name,
                "target_file": Path(target_file).name
            }
        }
    
    def _assess_risk(self, old_value: str, new_value: str, row: int, col: int) -> str:
        """
        评估变更风险等级
        
        基于简单规则：
        - 数字大幅变化（>50%）: high
        - 状态变化（正常→异常等）: high
        - 日期变化: medium
        - 其他: low
        """
        # 尝试检测数字变化
        try:
            old_num = float(old_value.replace(',', '').replace('%', ''))
            new_num = float(new_value.replace(',', '').replace('%', ''))
            if old_num != 0:
                change_rate = abs((new_num - old_num) / old_num)
                if change_rate > 0.5:  # 变化超过50%
                    return "high"
                elif change_rate > 0.2:  # 变化超过20%
                    return "medium"
        except:
            pass
        
        # 检测状态变化
        status_keywords = ["正常", "异常", "缺货", "停产", "完成", "未完成", "已结项", "进行中"]
        if any(keyword in old_value or keyword in new_value for keyword in status_keywords):
            if old_value != new_value:
                return "high"
        
        # 检测日期变化
        if "/" in old_value or "/" in new_value or "-" in old_value or "-" in new_value:
            if any(char.isdigit() for char in old_value) and any(char.isdigit() for char in new_value):
                return "medium"
        
        # 默认低风险
        return "low"
    
    def _get_change_type(self, old_value: str, new_value: str) -> str:
        """判断变更类型"""
        if not old_value and new_value:
            return "addition"
        elif old_value and not new_value:
            return "deletion"
        else:
            return "modification"

def test_simple_comparator():
    """测试简单对比器"""
    baseline = "/root/projects/tencent-doc-manager/csv_versions/2025_W37/midweek/tencent_副本-测试版本-出国销售计划表-工作表1_20250911_1131_midweek_W37.csv"
    target = "/root/projects/tencent-doc-manager/csv_versions/2025_W37/midweek/tencent_副本-副本-测试版本-出国销售计划表-工作表1_20250911_1132_midweek_W37.csv"
    
    comparator = SimpleCsvComparator()
    result = comparator.compare_csv_files(baseline, target)
    
    print(f"\n✅ 简单对比器检测到 {result['statistics']['total_changes']} 个变更")
    print(f"   高风险: {result['statistics']['high_risk_count']}")
    print(f"   中风险: {result['statistics']['medium_risk_count']}")
    print(f"   低风险: {result['statistics']['low_risk_count']}")
    
    print("\n前5个变更:")
    for change in result['changes'][:5]:
        print(f"  [{change['row']},{change['column']}] {change['cell_reference']}: "
              f"'{change['old_value'][:30]}...' → '{change['new_value'][:30]}...' ({change['risk_level']})")
    
    return result

if __name__ == "__main__":
    test_simple_comparator()