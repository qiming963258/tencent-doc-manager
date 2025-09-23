#!/usr/bin/env python3
"""修正综合打分文件的列名映射"""

import json
import datetime

# 读取对比结果
comparison_file = '/root/projects/tencent-doc-manager/comparison_results/comparison_20250923_190719.json'
with open(comparison_file, 'r', encoding='utf-8') as f:
    comparison_data = json.load(f)

# 标准19列
STANDARD_COLUMNS = [
    "序号", "项目类型", "来源", "任务发起时间", "目标对齐",
    "关键KR对齐", "具体计划内容", "邓总指导登记", "负责人", "协助人",
    "监督人", "重要程度", "预计完成时间", "完成进度", "完成链接",
    "经理分析复盘", "最新复盘时间", "对上汇报", "应用情况"
]

# 列名映射（从原始列名到标准列名）
COLUMN_MAPPING = {
    "计划输出思路\n8/28": "序号",  # B列映射到第1列
    "项目类型": "项目类型",  # C列
    "来源": "来源",  # D列
    "任务发起时间": "任务发起时间",  # E列
    "目标对齐": "目标对齐",  # F列
    "关键KR对齐": "关键KR对齐",  # G列
    "具体计划内容": "具体计划内容",  # H列
    "邓总指导登记（日更新）": "邓总指导登记",  # I列
    "负责人": "负责人",  # J列
    "协助人": "协助人",  # K列
    "监督人": "监督人",  # 没有在原始数据中，补充
    "重要程度": "重要程度",  # L列
    "预计完成时间": "预计完成时间",  # M列
    "完成链接": "完成链接",  # N列改为标准列名
    "总完成进度": "完成进度",  # O列改为标准列名
    "经理分析复盘": "经理分析复盘",  # P列
}

# 统计变更
modifications = comparison_data.get('modifications', [])
total_mods = len(modifications)
print(f"发现 {total_mods} 处变更")

# 按标准列名分组统计
column_modifications = {}
for mod in modifications:
    original_col_name = mod.get('column_name', '')
    # 映射到标准列名
    standard_col_name = COLUMN_MAPPING.get(original_col_name, original_col_name)

    # 如果找到标准列名，添加到对应的修改列表
    if standard_col_name in STANDARD_COLUMNS:
        if standard_col_name not in column_modifications:
            column_modifications[standard_col_name] = []
        # 提取行号
        cell = mod.get('cell', '')
        if cell:
            row_num = int(''.join(filter(str.isdigit, cell)))
            column_modifications[standard_col_name].append(row_num)

# 生成热力图矩阵
matrix = []
row_data = []
for col in STANDARD_COLUMNS:
    mod_count = len(column_modifications.get(col, []))

    # 根据变更数量设置热度值
    if mod_count == 0:
        heat = 0.05  # 蓝色
    elif mod_count == 1:
        heat = 0.30  # 绿色
    elif mod_count <= 3:
        heat = 0.60  # 黄色
    else:
        heat = 0.90  # 红色

    row_data.append(heat)

matrix = [row_data]

# 构建column_modifications_by_table（使用标准列名）
formatted_column_mods = {}
for col_name, row_list in column_modifications.items():
    formatted_column_mods[col_name] = {
        'modified_rows': row_list,
        'modification_count': len(row_list)
    }

# 构建综合打分数据
comprehensive_score = {
    "metadata": {
        "version": "2.0",
        "timestamp": datetime.datetime.now().isoformat(),
        "week": "W39",
        "generator": "fixed_column_mapping",
        "baseline_week": "W38",
        "comparison_week": "W39",
        "baseline_file": "tencent_出国销售计划表_20250915_0145_baseline_W39.csv",
        "target_file": "tencent_出国销售计划表_20250923_1908_midweek_W39.csv"
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
            "column_modifications": formatted_column_mods,
            "total_rows": 270
        }
    }
}

# 保存文件
output_file = '/root/projects/tencent-doc-manager/scoring_results/comprehensive/comprehensive_score_W39_FIXED_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + '.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(comprehensive_score, f, ensure_ascii=False, indent=2)

print(f"✅ 修正版综合打分文件已生成: {output_file}")
print(f"📊 包含 {total_mods} 处变更")
print(f"📝 列修改详情：")
for col, rows in column_modifications.items():
    print(f"   {col}: {len(rows)}处修改 (行 {rows})")