#!/usr/bin/env python3
"""
生成多文档综合打分文件
模拟多个文档的热力图数据
"""

import json
from datetime import datetime
from pathlib import Path

def generate_multi_document_score():
    """生成包含3个文档的综合打分文件"""

    # 三个配置的文档
    documents = [
        "副本-测试版本-出国销售计划表",
        "副本-测试版本-回国销售计划表",
        "测试版本-小红书部门"
    ]

    # 标准19列
    columns = [
        "序号", "项目类型", "来源", "任务发起时间", "目标对齐",
        "关键KR对齐", "具体计划内容", "邓总指导登记", "负责人", "协助人",
        "监督人", "重要程度", "预计完成时间", "完成进度", "完成链接",
        "经理分析复盘", "最新复盘时间", "对上汇报", "应用情况"
    ]

    # 生成3行热力图矩阵（每个文档一行）
    heatmap_matrix = []
    for doc_idx, doc_name in enumerate(documents):
        row = []
        for col_idx, col in enumerate(columns):
            # 模拟不同的风险等级
            if col == "重要程度" and doc_idx == 2:  # 小红书部门的重要程度列
                heat_value = 0.90  # 高风险（红色）- 对应92处变更
            elif col in ["来源", "任务发起时间", "目标对齐"]:
                heat_value = 0.60  # 中风险（橙色）
            elif col in ["完成进度", "完成链接"]:
                heat_value = 0.30  # 低风险（绿色）
            else:
                heat_value = 0.05  # 无修改（蓝色）
            row.append(heat_value)
        heatmap_matrix.append(row)

    # 构建综合打分数据
    comprehensive_data = {
        "metadata": {
            "version": "2.0",
            "timestamp": datetime.now().isoformat(),
            "week": "W39",
            "generator": "multi_document_generator",
            "source_type": "multi_document_scoring"
        },
        "summary": {
            "total_tables": 3,
            "total_columns": 19,
            "total_modifications": 150,  # 模拟总修改数
            "l1_modifications": 92,  # 主要是小红书的重要程度列
            "l2_modifications": 38,
            "l3_modifications": 20,
            "overall_risk_score": 0.65
        },
        "table_names": documents,
        "column_names": columns,
        "heatmap_data": {
            "matrix": heatmap_matrix,
            "rows": 3,
            "cols": 19,
            "generation_method": "multi_document_simulation"
        },
        "table_details": {
            documents[0]: {
                "total_rows": 270,
                "modified_rows": 35,
                "excel_url": "https://docs.qq.com/sheet/DWEFNU25TemFnZXJN"
            },
            documents[1]: {
                "total_rows": 180,
                "modified_rows": 23,
                "excel_url": "https://docs.qq.com/sheet/DWGZDZkxpaGVQaURr"
            },
            documents[2]: {
                "total_rows": 270,
                "modified_rows": 92,
                "excel_url": "https://docs.qq.com/sheet/DWFJzdWNwd0RGbU5R"
            }
        },
        "excel_urls": {
            documents[0]: "https://docs.qq.com/sheet/DWEFNU25TemFnZXJN",
            documents[1]: "https://docs.qq.com/sheet/DWGZDZkxpaGVQaURr",
            documents[2]: "https://docs.qq.com/sheet/DWFJzdWNwd0RGbU5R"
        }
    }

    # 保存到多个位置
    output_dir = Path('/root/projects/tencent-doc-manager/scoring_results/comprehensive')
    week_dir = Path('/root/projects/tencent-doc-manager/scoring_results/2025_W39')

    output_dir.mkdir(parents=True, exist_ok=True)
    week_dir.mkdir(parents=True, exist_ok=True)

    # 保存文件
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # 1. comprehensive目录的latest文件
    latest_file = output_dir / 'comprehensive_score_W39_latest.json'
    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump(comprehensive_data, f, ensure_ascii=False, indent=2)
    print(f"✅ 已生成: {latest_file}")

    # 2. 周目录的带时间戳文件
    timestamped_file = week_dir / f'comprehensive_score_W39_MULTI_{timestamp}.json'
    with open(timestamped_file, 'w', encoding='utf-8') as f:
        json.dump(comprehensive_data, f, ensure_ascii=False, indent=2)
    print(f"✅ 已生成: {timestamped_file}")

    # 3. 周目录的latest文件
    week_latest = week_dir / 'comprehensive_score_W39_latest.json'
    with open(week_latest, 'w', encoding='utf-8') as f:
        json.dump(comprehensive_data, f, ensure_ascii=False, indent=2)
    print(f"✅ 已生成: {week_latest}")

    print(f"\n📊 生成的多文档综合打分:")
    print(f"   - 文档数量: {len(documents)}")
    print(f"   - 热力图行数: {len(heatmap_matrix)}")
    print(f"   - 总修改数: 150")
    print(f"\n🔥 包含的文档:")
    for i, doc in enumerate(documents, 1):
        print(f"   {i}. {doc}")

if __name__ == "__main__":
    generate_multi_document_score()