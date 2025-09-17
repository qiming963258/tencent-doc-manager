#!/usr/bin/env python3
"""
生成包含更多热点数据的综合打分文件，用于展示热聚集效果
"""
import json
import random
import datetime
import os
import sys

# 导入必要的模块
sys.path.append('/root/projects/tencent-doc-manager')
from standard_columns_config import STANDARD_COLUMNS
from production.core_modules.comprehensive_score_generator_v2 import ComprehensiveScoreGeneratorV2

def generate_hotspot_pattern_score():
    """生成带有热点聚集模式的综合打分文件"""

    # 使用官方生成器
    generator = ComprehensiveScoreGeneratorV2()

    # 随机生成10-15个表格
    num_tables = random.randint(10, 15)
    print(f"生成 {num_tables} 个表格的热点聚集数据...")

    # 定义热点区域（前5个表格的前8个列会有更高的修改概率）
    hotspot_tables = 5
    hotspot_columns = 8

    # 准备表格数据
    table_details = []

    for i in range(num_tables):
        table_name = f"表格_{i+1:02d}_{'高风险' if i < hotspot_tables else '普通'}"

        # 为每个表格生成列详情
        column_details = []
        total_modifications = 0

        for j, col_name in enumerate(STANDARD_COLUMNS):
            # 判断是否在热点区域
            is_hotspot = (i < hotspot_tables) and (j < hotspot_columns)

            # 热点区域有80%概率产生修改，非热点区域只有20%
            has_modification = random.random() < (0.8 if is_hotspot else 0.2)

            if has_modification:
                # 热点区域生成更多修改
                num_mods = random.randint(5, 15) if is_hotspot else random.randint(1, 3)
                modified_rows = sorted(random.sample(range(1, 200), min(num_mods, 199)))

                # 生成修改详情
                modification_details = []
                for row in modified_rows[:5]:  # 只记录前5个详细修改
                    modification_details.append({
                        "row": row,
                        "old_value": f"旧值_{row}",
                        "new_value": f"新值_{row}",
                        "change_type": random.choice(["修改", "新增", "删除"]),
                        "confidence": random.uniform(0.7, 1.0) if is_hotspot else random.uniform(0.5, 0.8)
                    })

                # 计算风险分数
                risk_score = random.uniform(0.7, 1.0) if is_hotspot else random.uniform(0.1, 0.5)

                column_details.append({
                    "column_name": col_name,
                    "column_index": j,
                    "modification_count": num_mods,
                    "modified_rows": modified_rows,
                    "modification_details": modification_details,
                    "risk_score": risk_score,
                    "risk_level": "L1" if risk_score > 0.7 else ("L2" if risk_score > 0.3 else "L3")
                })

                total_modifications += num_mods
            else:
                # 无修改的列
                column_details.append({
                    "column_name": col_name,
                    "column_index": j,
                    "modification_count": 0,
                    "modified_rows": [],
                    "modification_details": [],
                    "risk_score": 0.05,
                    "risk_level": "L3"
                })

        # 计算表格的总体风险分数
        if column_details:
            avg_risk = sum(cd['risk_score'] for cd in column_details) / len(column_details)
        else:
            avg_risk = 0.05

        table_detail = {
            "table_name": table_name,
            "table_index": i,
            "total_rows": 200,
            "total_modifications": total_modifications,
            "column_details": column_details,
            "risk_score": avg_risk * 1.2 if i < hotspot_tables else avg_risk,  # 热点表格风险更高
            "overall_risk_score": min(avg_risk * 1.2, 1.0) if i < hotspot_tables else avg_risk,
            "risk_level": "L1" if avg_risk > 0.6 else ("L2" if avg_risk > 0.3 else "L3"),
            "excel_url": f"https://docs.qq.com/sheet/table_{i+1}",
            "ai_analysis": {
                "summary": f"{'热点区域表格' if i < hotspot_tables else '普通表格'}，修改集中在{'前部列' if i < hotspot_tables else '分散列'}",
                "recommendation": "重点审查" if i < hotspot_tables else "常规审查",
                "confidence": 0.95
            }
        }

        table_details.append(table_detail)

    # 生成热力图矩阵
    heatmap_matrix = []
    for table in table_details:
        row = []
        for col_detail in table['column_details']:
            # 使用风险分数作为热力值
            heat_value = col_detail['risk_score']
            row.append(round(heat_value, 2))
        heatmap_matrix.append(row)

    # 生成hover_data
    hover_data = []
    for table in table_details:
        hover_item = {
            "table_index": table['table_index'],
            "table_name": table['table_name'],
            "column_details": [
                {
                    "column_name": cd['column_name'],
                    "modification_count": cd['modification_count'],
                    "modified_rows": cd['modified_rows']
                }
                for cd in table['column_details']
            ]
        }
        hover_data.append(hover_item)

    # 统计信息
    total_params = sum(len(td['column_details']) * td['total_rows'] for td in table_details)
    total_modifications = sum(td['total_modifications'] for td in table_details)

    # 构建完整的综合打分数据
    comprehensive_score_data = {
        "metadata": {
            "version": "2.0",
            "generated_at": datetime.datetime.now().isoformat(),
            "generator": "hotspot_pattern_generator",
            "data_source": "simulated_hotspot_data",
            "total_params": total_params,
            "total_tables": num_tables,
            "hotspot_pattern": True,
            "hotspot_config": {
                "hotspot_tables": hotspot_tables,
                "hotspot_columns": hotspot_columns
            }
        },
        "table_names": [td['table_name'] for td in table_details],
        "column_names": STANDARD_COLUMNS.copy(),
        "table_details": table_details,
        "heatmap_data": {
            "matrix": heatmap_matrix,
            "rows": len(heatmap_matrix),
            "cols": len(STANDARD_COLUMNS),
            "clustered": False  # 将由服务器应用聚类
        },
        "hover_data": {
            "data": hover_data
        },
        "statistics": {
            "total_modifications": total_modifications,
            "average_modifications_per_table": total_modifications / num_tables,
            "high_risk_count": sum(1 for row in heatmap_matrix for v in row if v >= 0.7),
            "medium_risk_count": sum(1 for row in heatmap_matrix for v in row if 0.3 <= v < 0.7),
            "low_risk_count": sum(1 for row in heatmap_matrix for v in row if 0.05 < v < 0.3),
            "tables_with_modifications": sum(1 for td in table_details if td['total_modifications'] > 0),
            "hotspot_concentration": f"{(hotspot_tables/num_tables)*100:.1f}% 表格包含 {(total_modifications*0.7/total_modifications)*100:.1f}% 修改"
        }
    }

    # 保存文件
    output_dir = '/root/projects/tencent-doc-manager/scoring_results/comprehensive'
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(output_dir, f'comprehensive_score_W38_{timestamp}_hotspot.json')

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(comprehensive_score_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 生成热点聚集模式综合打分文件: {output_file}")
    print(f"   - 表格数量: {num_tables}")
    print(f"   - 热点表格: 前{hotspot_tables}个")
    print(f"   - 热点列: 前{hotspot_columns}列")
    print(f"   - 总修改数: {total_modifications}")
    print(f"   - 总参数: {total_params}")

    return output_file

if __name__ == "__main__":
    generate_hotspot_pattern_score()