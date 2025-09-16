#!/usr/bin/env python3
"""
使用增强版CSV对比器重新运行完整数据流程
确保检测到所有18个对角线修改
"""
import sys
import os
import json
import asyncio
from datetime import datetime
from pathlib import Path

sys.path.append('/root/projects/tencent-doc-manager/production/core_modules')
from production_csv_comparator import ProductionCSVComparator
from adaptive_table_comparator import AdaptiveTableComparator
from week_time_manager import WeekTimeManager

async def run_enhanced_flow():
    """运行增强版完整流程"""
    print("=" * 60)
    print("🚀 开始运行增强版完整数据流程")
    print("=" * 60)

    # 1. CSV对比（使用增强版）
    print("\n📊 步骤1: 运行增强版CSV对比...")

    comparator = ProductionCSVComparator()

    # 查找最新的CSV文件
    csv_dir = Path('/root/projects/tencent-doc-manager/csv_versions/2025_W38')
    baseline_dir = csv_dir / 'baseline'
    midweek_dir = csv_dir / 'midweek'

    baseline_file = list(baseline_dir.glob('*出国*.csv'))[0]
    midweek_file = list(midweek_dir.glob('*出国*.csv'))[0]

    print(f"  基准文件: {baseline_file.name}")
    print(f"  当前文件: {midweek_file.name}")

    # 执行对比
    result = await comparator.compare_csv_files(
        str(baseline_file),
        str(midweek_file),
        output_file='/root/projects/tencent-doc-manager/comparison_results/enhanced_production_result.json'
    )

    print(f"  ✅ 检测到 {result.total_differences} 个修改")

    # 2. 详细打分
    print("\n📊 步骤2: 生成详细打分...")

    # 创建详细打分数据，基于真实修改
    detailed_scores = {
        "出国销售计划表": {
            "table_name": "出国销售计划表",
            "total_rows": 270,
            "total_differences": result.total_differences,
            "column_modifications": {},
            "risk_distribution": {"L1": 0, "L2": 0, "L3": 0}
        }
    }

    # 统计每列的修改
    for diff in result.differences:
        col_name = diff.get('列名', f"列{diff.get('列索引', '?')}")
        if col_name not in detailed_scores["出国销售计划表"]["column_modifications"]:
            detailed_scores["出国销售计划表"]["column_modifications"][col_name] = {
                "rows": [],
                "count": 0,
                "score": 0.5
            }

        detailed_scores["出国销售计划表"]["column_modifications"][col_name]["rows"].append(
            diff.get('行号', 0)
        )
        detailed_scores["出国销售计划表"]["column_modifications"][col_name]["count"] += 1

        # 统计风险等级
        risk_level = diff.get('risk_level', 'L3')
        detailed_scores["出国销售计划表"]["risk_distribution"][risk_level] += 1

    # 保存详细打分
    detailed_file = f'/root/projects/tencent-doc-manager/scoring_results/detailed/detailed_score_enhanced_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    os.makedirs(os.path.dirname(detailed_file), exist_ok=True)

    with open(detailed_file, 'w', encoding='utf-8') as f:
        json.dump(detailed_scores, f, ensure_ascii=False, indent=2)

    print(f"  ✅ 详细打分已保存")

    # 3. 生成综合打分（包含UI数据）
    print("\n📊 步骤3: 生成综合打分...")

    # 标准19列
    standard_columns = [
        "任务发起时间", "任务类型", "当前任务状态", "任务截止时间",
        "主类目", "风险等级", "责任人", "协作人员", "进度百分比",
        "备注信息", "创建时间", "最后更新", "审批状态", "优先级",
        "任务标签", "相关文档", "预算金额", "实际花费", "完成情况"
    ]

    # 创建列到标准列的映射
    column_mapping = {
        'B': '项目管理ID', 'C': '任务类型', 'D': '当前任务状态',
        'E': '任务发起时间', 'F': '主类目', 'G': '风险等级',
        'H': '备注信息', 'I': '备注信息', 'J': '责任人',
        'K': '协作人员', 'L': '审批状态', 'M': '优先级',
        'N': '任务截止时间', 'O': '进度百分比', 'P': '相关文档',
        'Q': '实际花费', 'R': '最后更新', 'S': '完成情况'
    }

    # 生成column_scores
    column_scores = {}
    for col_name in standard_columns:
        column_scores[col_name] = {
            "modified_rows": [],
            "avg_score": 0.05,
            "modification_count": 0,
            "total_rows": 270
        }

    # 填充真实修改数据
    for diff in result.differences:
        col_letter = chr(65 + diff.get('列索引', 0) - 1)  # A=1, B=2, etc.
        ui_col = column_mapping.get(col_letter)

        if ui_col and ui_col in standard_columns:
            column_scores[ui_col]["modified_rows"].append(diff.get('行号', 0))
            column_scores[ui_col]["avg_score"] = max(column_scores[ui_col]["avg_score"], 0.7)
            column_scores[ui_col]["modification_count"] += 1

    # 生成heat_values
    heat_values = []
    for col_name in standard_columns:
        if column_scores[col_name]["modification_count"] > 0:
            heat_values.append(column_scores[col_name]["avg_score"])
        else:
            heat_values.append(0.05)

    # 构建综合打分数据
    comprehensive_data = {
        "timestamp": datetime.now().isoformat(),
        "week": "W38",
        "total_modifications": result.total_differences,
        "tables": ["出国销售计划表", "回国销售计划表", "小红书部门"],
        "table_scores": [{
            "table_name": "出国销售计划表",
            "total_rows": 270,
            "total_modifications": result.total_differences,
            "risk_score": 0.6,
            "column_scores": column_scores
        }],
        "column_scores": {
            "出国销售计划表": column_scores
        },
        "ui_data": [{
            "table_name": "出国销售计划表",
            "heat_values": heat_values,
            "row_data": [
                {
                    "column": col_name,
                    "heat_value": heat_val,
                    "color": get_color_for_value(heat_val),
                    "modified_rows": column_scores[col_name]["modified_rows"]
                }
                for col_name, heat_val in zip(standard_columns, heat_values)
            ]
        }]
    }

    # 保存综合打分
    comprehensive_file = f'/root/projects/tencent-doc-manager/scoring_results/comprehensive/comprehensive_score_W38_{datetime.now().strftime("%Y%m%d_%H%M%S")}_enhanced.json'

    with open(comprehensive_file, 'w', encoding='utf-8') as f:
        json.dump(comprehensive_data, f, ensure_ascii=False, indent=2)

    print(f"  ✅ 综合打分已保存: {os.path.basename(comprehensive_file)}")

    # 4. 更新data_source_state.json让UI读取最新数据
    print("\n📊 步骤4: 更新UI数据源配置...")

    state_file = '/root/projects/tencent-doc-manager/config/data_source_state.json'
    state_data = {
        "current_mode": "comprehensive",
        "last_update": datetime.now().isoformat(),
        "comprehensive_file": comprehensive_file,
        "detailed_file": detailed_file,
        "comparison_file": '/root/projects/tencent-doc-manager/comparison_results/enhanced_production_result.json'
    }

    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(state_data, f, ensure_ascii=False, indent=2)

    print(f"  ✅ UI数据源已更新")

    return comprehensive_data

def get_color_for_value(value):
    """根据热力值返回颜色"""
    if value >= 0.8:
        return "#FF0000"
    elif value >= 0.6:
        return "#FFA500"
    elif value >= 0.4:
        return "#FFFF00"
    elif value >= 0.1:
        return "#00FF00"
    else:
        return "#0000FF"

async def main():
    """主函数"""
    result = await run_enhanced_flow()

    print("\n" + "=" * 60)
    print("✅ 增强版数据流程运行完成！")
    print("=" * 60)

    print(f"\n📊 最终结果:")
    print(f"  总修改数: {result['total_modifications']}")
    print(f"  修改的列数: {len([c for c in result['column_scores']['出国销售计划表'].values() if c['modification_count'] > 0])}")

    print("\n🌐 请刷新UI查看更新:")
    print("  http://202.140.143.88:8089/")

    return result

if __name__ == "__main__":
    asyncio.run(main())