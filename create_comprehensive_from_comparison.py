#!/usr/bin/env python3
"""从对比结果生成综合打分文件"""

import json
import datetime
import os

# 读取最新的对比结果
comparison_file = '/root/projects/tencent-doc-manager/comparison_results/comparison_20250923_190719.json'
with open(comparison_file, 'r', encoding='utf-8') as f:
    comparison_data = json.load(f)

# 统计变更数量
modifications = comparison_data.get('modifications', [])
total_mods = len(modifications)
print(f"发现 {total_mods} 处变更")

# 按列分组统计
column_modifications = {}
for mod in modifications:
    col_name = mod.get('column_name', '')
    if col_name:
        if col_name not in column_modifications:
            column_modifications[col_name] = []
        column_modifications[col_name].append(mod.get('cell', ''))

# 标准19列
STANDARD_COLUMNS = [
    "序号", "项目类型", "来源", "任务发起时间", "目标对齐",
    "关键KR对齐", "具体计划内容", "邓总指导登记", "负责人", "协助人",
    "监督人", "重要程度", "预计完成时间", "完成进度", "完成链接",
    "经理分析复盘", "最新复盘时间", "对上汇报", "应用情况"
]

# 生成热力图矩阵 (1行x19列)
matrix = []
row_data = []
for col in STANDARD_COLUMNS:
    # 查找该列的变更数量
    mod_count = 0
    for col_name, cells in column_modifications.items():
        if col in col_name or col_name in col:
            mod_count = len(cells)
            break

    # 根据变更数量设置热度值
    if mod_count == 0:
        heat = 0.05  # 蓝色
    elif mod_count <= 2:
        heat = 0.30  # 绿色
    elif mod_count <= 5:
        heat = 0.60  # 黄色
    else:
        heat = 0.90  # 红色

    row_data.append(heat)

matrix = [row_data]

# 构建综合打分数据
comprehensive_score = {
    "metadata": {
        "version": "2.0",
        "timestamp": datetime.datetime.now().isoformat(),
        "week": "W39",
        "generator": "manual_conversion",
        "baseline_week": "W39",
        "comparison_week": "W39",
        "baseline_file": "tencent_出国销售计划表_baseline_W39.csv",
        "target_file": "tencent_出国销售计划表_20250923_1907_midweek_W39.csv"
    },
    "summary": {
        "total_tables": 1,
        "total_columns": 19,
        "total_modifications": total_mods,
        "overall_risk_score": min(0.95, total_mods * 0.05),
        "processing_status": "complete",
        "data_source": "real_csv_comparison"
    },
    "table_names": ["副本-测试版本-出国销售计划表"],
    "column_names": STANDARD_COLUMNS,
    "heatmap_data": {
        "matrix": matrix,
        "rows": 1,
        "cols": 19,
        "generation_method": "real_data_comparison"
    },
    "table_details": {
        "副本-测试版本-出国销售计划表": {
            "total_rows": 270,
            "modified_rows": total_mods,
            "added_rows": 0,
            "deleted_rows": 0
        }
    },
    "statistics": {
        "total_cells": 5130,
        "modified_cells": total_mods,
        "modification_rate": round(total_mods / 5130, 4) if total_mods > 0 else 0.0
    },
    "column_modifications_by_table": {
        "副本-测试版本-出国销售计划表": {
            "column_modifications": {
                col: {
                    "modified_rows": cells,
                    "modification_count": len(cells)
                } for col, cells in column_modifications.items()
            },
            "total_rows": 270
        }
    }
}

# 保存文件
output_file = '/root/projects/tencent-doc-manager/scoring_results/comprehensive/comprehensive_score_W39_REAL_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + '.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(comprehensive_score, f, ensure_ascii=False, indent=2)

print(f"✅ 综合打分文件已生成: {output_file}")
print(f"📊 包含 {total_mods} 处变更")