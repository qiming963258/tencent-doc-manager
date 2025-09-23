#!/usr/bin/env python3
"""从详细打分生成综合打分（包含正确的风险颜色）"""

import json
import os
from datetime import datetime
from pathlib import Path

def generate_comprehensive_from_detailed():
    """从最新的详细打分文件生成综合打分"""

    # 查找最新的详细打分文件
    detailed_dir = Path('/root/projects/tencent-doc-manager/scoring_results/detailed')
    detailed_files = sorted(detailed_dir.glob('detailed_score_*.json'),
                          key=lambda x: x.stat().st_mtime, reverse=True)

    if not detailed_files:
        print("❌ 没有找到详细打分文件")
        return None

    latest_detailed = detailed_files[0]
    print(f"📖 使用详细打分文件: {latest_detailed.name}")

    with open(latest_detailed, 'r', encoding='utf-8') as f:
        detailed_data = json.load(f)

    # 标准19列
    STANDARD_COLUMNS = [
        "序号", "项目类型", "来源", "任务发起时间", "目标对齐",
        "关键KR对齐", "具体计划内容", "邓总指导登记", "负责人", "协助人",
        "监督人", "重要程度", "预计完成时间", "完成进度", "完成链接",
        "经理分析复盘", "最新复盘时间", "对上汇报", "应用情况"
    ]

    # 列名映射
    COLUMN_MAPPING = {
        "计划输出思路\n8/28": "序号",
        "项目类型": "项目类型",
        "来源": "来源",
        "任务发起时间": "任务发起时间",
        "目标对齐": "目标对齐",
        "关键KR对齐": "关键KR对齐",
        "具体计划内容": "具体计划内容",
        "邓总指导登记（日更新）": "邓总指导登记",
        "负责人": "负责人",
        "协助人": "协助人",
        "重要程度": "重要程度",
        "预计完成时间": "预计完成时间",
        "完成链接": "完成链接",
        "总完成进度": "完成进度",
        "经理分析复盘": "经理分析复盘",
    }

    # 统计每列的修改和风险等级
    column_data = {}  # {标准列名: {'modifications': [], 'risk_level': 'L1/L2/L3', 'scores': []}}

    l1_count = 0
    l2_count = 0
    l3_count = 0

    for score in detailed_data.get('scores', []):
        original_col = score['column_name']
        standard_col = COLUMN_MAPPING.get(original_col, original_col)

        if standard_col in STANDARD_COLUMNS:
            if standard_col not in column_data:
                column_data[standard_col] = {
                    'modifications': [],
                    'risk_level': score['column_level'],
                    'scores': []
                }

            # 提取行号
            cell = score['cell']
            row_num = int(''.join(filter(str.isdigit, cell)))
            column_data[standard_col]['modifications'].append(row_num)
            column_data[standard_col]['scores'].append(score.get('scoring_details', {}).get('final_score', 0))

            # 统计风险等级
            if score['column_level'] == 'L1':
                l1_count += 1
            elif score['column_level'] == 'L2':
                l2_count += 1
            elif score['column_level'] == 'L3':
                l3_count += 1

    # 生成热力图矩阵（基于风险等级和修改情况）
    matrix_row = []
    for col in STANDARD_COLUMNS:
        if col in column_data:
            risk_level = column_data[col]['risk_level']
            has_modification = len(column_data[col]['modifications']) > 0

            if not has_modification:
                heat_value = 0.05  # 无修改
            elif risk_level == 'L1':
                heat_value = 0.90  # L1红色
            elif risk_level == 'L2':
                heat_value = 0.60  # L2橙色
            else:  # L3
                heat_value = 0.30  # L3绿色
        else:
            heat_value = 0.05  # 该列无修改

        matrix_row.append(heat_value)

    # 构建column_modifications_by_table
    column_modifications = {}
    for col_name, data in column_data.items():
        column_modifications[col_name] = {
            'modified_rows': data['modifications'],
            'modification_count': len(data['modifications']),
            'risk_level': data['risk_level'],
            'average_score': round(sum(data['scores']) / len(data['scores']), 2) if data['scores'] else 0
        }

    # 生成综合打分数据
    comprehensive = {
        "metadata": {
            "version": "2.0",
            "timestamp": datetime.now().isoformat(),
            "week": "W39",
            "generator": "detailed_to_comprehensive",
            "source_file": latest_detailed.name,
            "baseline_week": "W38",
            "comparison_week": "W39"
        },
        "summary": {
            "total_tables": 1,
            "total_columns": 19,
            "total_modifications": detailed_data['metadata']['total_modifications'],
            "l1_modifications": l1_count,
            "l2_modifications": l2_count,
            "l3_modifications": l3_count,
            "overall_risk_score": round((l1_count * 0.9 + l2_count * 0.6 + l3_count * 0.3) / max(1, l1_count + l2_count + l3_count), 2),
            "processing_status": "complete",
            "data_source": "detailed_scoring"
        },
        "table_names": ["副本-测试版本-出国销售计划表"],
        "column_names": STANDARD_COLUMNS,
        "heatmap_data": {
            "matrix": [matrix_row],
            "rows": 1,
            "cols": 19,
            "generation_method": "risk_based_from_detailed",
            "color_distribution": {
                "red_0.9": matrix_row.count(0.90),
                "orange_0.6": matrix_row.count(0.60),
                "green_0.3": matrix_row.count(0.30),
                "blue_0.05": matrix_row.count(0.05)
            }
        },
        "table_details": {
            "副本-测试版本-出国销售计划表": {
                "total_rows": 270,
                "modified_rows": detailed_data['metadata']['total_modifications'],
                "added_rows": 0,
                "deleted_rows": 0
            }
        },
        "statistics": {
            "total_cells": 5130,
            "modified_cells": detailed_data['metadata']['total_modifications'],
            "modification_rate": round(detailed_data['metadata']['total_modifications'] / 5130, 4),
            "risk_distribution": detailed_data.get('summary', {}).get('risk_distribution', {})
        },
        "column_modifications_by_table": {
            "副本-测试版本-出国销售计划表": {
                "column_modifications": column_modifications,
                "total_rows": 270
            }
        }
    }

    # 保存文件
    output_file = Path('/root/projects/tencent-doc-manager/scoring_results/comprehensive') / \
                  f"comprehensive_score_W39_AUTO_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(comprehensive, f, ensure_ascii=False, indent=2)

    print(f"✅ 综合打分文件已生成: {output_file}")
    print(f"📊 风险分布:")
    print(f"   🔴 L1高风险: {l1_count}处")
    print(f"   🟠 L2中风险: {l2_count}处")
    print(f"   🟢 L3低风险: {l3_count}处")
    print(f"🎨 热力图颜色:")
    print(f"   红色格子: {matrix_row.count(0.90)}个")
    print(f"   橙色格子: {matrix_row.count(0.60)}个")
    print(f"   绿色格子: {matrix_row.count(0.30)}个")
    print(f"   蓝色格子: {matrix_row.count(0.05)}个")

    return str(output_file)

if __name__ == "__main__":
    generate_comprehensive_from_detailed()