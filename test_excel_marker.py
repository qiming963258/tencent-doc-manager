#!/usr/bin/env python3
"""
测试智能Excel标记系统
"""

import os
import json
from intelligent_excel_marker import DetailedScoreGenerator, IntelligentExcelMarker

def create_test_score_data():
    """创建测试用的详细打分数据"""
    
    # 创建测试打分数据
    score_data = {
        "metadata": {
            "comparison_id": "comp_20250110_test001",
            "baseline_file": "baseline.xlsx",
            "target_file": "副本-副本-测试版本-出国销售计划表_fixed.xlsx",
            "doc_name": "副本-副本-测试版本-出国销售计划表",
            "doc_id": "test001",
            "timestamp": "20250110_173500",
            "week_number": "37"
        },
        "statistics": {
            "total_cells": 2204,
            "changed_cells": 12,
            "high_risk_count": 3,
            "medium_risk_count": 5,
            "low_risk_count": 4
        },
        "cell_scores": {
            # 高风险变更（红色条纹）
            "B5": {
                "row": 5, "column": 2,
                "old_value": "100", "new_value": "",
                "change_type": "deletion",
                "risk_level": "high",
                "score": 20,
                "color_code": "FF0000"
            },
            "C7": {
                "row": 7, "column": 3,
                "old_value": "正常", "new_value": "异常",
                "change_type": "text_change",
                "risk_level": "high",
                "score": 25,
                "color_code": "FF0000"
            },
            "D10": {
                "row": 10, "column": 4,
                "old_value": "50", "new_value": "500",
                "change_type": "numeric_increase_major_change",
                "risk_level": "high",
                "score": 15,
                "color_code": "FF0000"
            },
            
            # 中等风险变更（黄色条纹）
            "E8": {
                "row": 8, "column": 5,
                "old_value": "100", "new_value": "150",
                "change_type": "numeric_increase_moderate_change",
                "risk_level": "medium",
                "score": 50,
                "color_code": "FFFF00"
            },
            "F9": {
                "row": 9, "column": 6,
                "old_value": "200", "new_value": "250",
                "change_type": "numeric_increase_moderate_change",
                "risk_level": "medium",
                "score": 55,
                "color_code": "FFFF00"
            },
            "G10": {
                "row": 10, "column": 7,
                "old_value": "", "new_value": "新增数据",
                "change_type": "addition",
                "risk_level": "medium",
                "score": 60,
                "color_code": "FFFF00"
            },
            "H11": {
                "row": 11, "column": 8,
                "old_value": "计划", "new_value": "执行中",
                "change_type": "text_change",
                "risk_level": "medium",
                "score": 45,
                "color_code": "FFFF00"
            },
            "I12": {
                "row": 12, "column": 9,
                "old_value": "300", "new_value": "350",
                "change_type": "numeric_increase_moderate_change",
                "risk_level": "medium",
                "score": 65,
                "color_code": "FFFF00"
            },
            
            # 低风险变更（绿色条纹）
            "J15": {
                "row": 15, "column": 10,
                "old_value": "100", "new_value": "105",
                "change_type": "numeric_increase_minor_change",
                "risk_level": "low",
                "score": 80,
                "color_code": "00FF00"
            },
            "K16": {
                "row": 16, "column": 11,
                "old_value": "备注1", "new_value": "备注1更新",
                "change_type": "text_change",
                "risk_level": "low",
                "score": 75,
                "color_code": "00FF00"
            },
            "L17": {
                "row": 17, "column": 12,
                "old_value": "1000", "new_value": "1020",
                "change_type": "numeric_increase_minor_change",
                "risk_level": "low",
                "score": 85,
                "color_code": "00FF00"
            },
            "M18": {
                "row": 18, "column": 13,
                "old_value": "状态A", "new_value": "状态B",
                "change_type": "text_change",
                "risk_level": "low",
                "score": 70,
                "color_code": "00FF00"
            }
        }
    }
    
    # 保存测试打分文件
    os.makedirs("/root/projects/tencent-doc-manager/scoring_results/detailed/", exist_ok=True)
    score_file = "/root/projects/tencent-doc-manager/scoring_results/detailed/detailed_scores_副本-副本-测试版本-出国销售计划表_20250110_173500.json"
    
    with open(score_file, 'w', encoding='utf-8') as f:
        json.dump(score_data, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 测试打分文件已创建: {score_file}")
    return score_file

def main():
    """主测试函数"""
    
    print("="*60)
    print("智能Excel标记系统测试")
    print("="*60)
    
    # 1. 创建测试打分数据
    print("\n1. 创建测试打分数据...")
    score_file = create_test_score_data()
    
    # 2. 使用已修复的Excel文件
    excel_file = "/root/projects/tencent-doc-manager/downloads/副本-副本-测试版本-出国销售计划表_fixed.xlsx"
    
    if not os.path.exists(excel_file):
        print(f"✗ Excel文件不存在: {excel_file}")
        return
    
    print(f"\n2. 使用Excel文件: {excel_file}")
    
    # 3. 初始化标记器并应用涂色
    print("\n3. 应用条纹涂色...")
    marker = IntelligentExcelMarker()
    
    output_file = marker.apply_striped_coloring(excel_file, score_file)
    
    # 4. 验证结果
    print("\n4. 验证结果...")
    if os.path.exists(output_file):
        import openpyxl
        try:
            wb = openpyxl.load_workbook(output_file)
            ws = wb.active
            
            # 检查涂色的单元格
            print("\n检查涂色效果:")
            test_cells = ["B5", "E8", "J15"]
            for cell_ref in test_cells:
                cell = ws[cell_ref]
                if cell.fill and cell.fill.patternType:
                    print(f"  ✓ {cell_ref}: 图案={cell.fill.patternType}, "
                          f"前景色={cell.fill.fgColor.rgb if cell.fill.fgColor else 'None'}")
                else:
                    print(f"  ✗ {cell_ref}: 无填充")
            
            wb.close()
            
            print(f"\n✅ 测试成功！")
            print(f"   输出文件: {output_file}")
            
        except Exception as e:
            print(f"\n✗ 验证失败: {e}")
    else:
        print(f"\n✗ 输出文件不存在")

if __name__ == "__main__":
    main()