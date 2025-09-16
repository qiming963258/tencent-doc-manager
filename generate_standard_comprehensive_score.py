#!/usr/bin/env python3
"""
生成符合10-综合打分绝对规范的测试文件
包含完整的9类UI参数
"""

import sys
import json
from datetime import datetime
from pathlib import Path

sys.path.append('/root/projects/tencent-doc-manager')
from production.core_modules.comprehensive_score_generator_v2 import ComprehensiveScoreGeneratorV2
from standard_columns_config import STANDARD_COLUMNS

def generate_test_data():
    """生成测试数据"""

    # 模拟3个表格的详细打分数据
    detailed_scores = [
        {
            "table_name": "副本-测试版本-出国销售计划表",
            "table_index": 0,
            "total_rows": 270,
            "modifications": [
                {"row": 2, "column": "负责人", "old": "张三", "new": "李四"},
                {"row": 5, "column": "预计完成时间", "old": "2025-09-01", "new": "2025-09-15"},
                {"row": 8, "column": "完成进度", "old": "50%", "new": "75%"},
            ] * 50  # 模拟150个修改
        },
        {
            "table_name": "副本-测试版本-回国销售计划表",
            "table_index": 1,
            "total_rows": 185,
            "modifications": [
                {"row": 10, "column": "项目类型", "old": "A类", "new": "B类"},
                {"row": 15, "column": "重要程度", "old": "高", "new": "中"},
            ] * 40  # 模拟80个修改
        },
        {
            "table_name": "测试版本-小红书部门",
            "table_index": 2,
            "total_rows": 2010,
            "modifications": [
                {"row": 100, "column": "目标对齐", "old": "KR1", "new": "KR2"},
                {"row": 200, "column": "监督人", "old": "王五", "new": "赵六"},
            ] * 60  # 模拟120个修改
        }
    ]

    # Excel URLs映射
    excel_urls = {
        "副本-测试版本-出国销售计划表": "https://docs.qq.com/sheet/DWEFNU25TemFnZXJN",
        "副本-测试版本-回国销售计划表": "https://docs.qq.com/sheet/DWGZDZkxpaGVQaURr",
        "测试版本-小红书部门": "https://docs.qq.com/sheet/DWFJzdWNwd0RGbU5R"
    }

    return detailed_scores, excel_urls

def main():
    """主函数"""
    print("=" * 60)
    print("🎯 生成符合规范的综合打分文件")
    print("=" * 60)

    # 初始化生成器
    generator = ComprehensiveScoreGeneratorV2()

    # 生成测试数据
    detailed_scores, excel_urls = generate_test_data()

    # 生成综合打分文件
    week_number = "38"
    filepath = generator.generate(
        week_number=week_number,
        detailed_scores=detailed_scores,
        excel_urls=excel_urls
    )

    # 验证生成的文件
    print("\n📋 验证生成的文件...")
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 检查关键字段
    print("\n🔍 关键字段检查：")
    checks = [
        ("metadata", "元数据"),
        ("summary", "摘要"),
        ("table_names", "表名列表"),
        ("column_names", "列名列表"),
        ("heatmap_data", "热力图数据"),
        ("table_details", "表格详情"),
        ("hover_data", "悬浮数据"),
        ("statistics", "统计信息")
    ]

    for field, desc in checks:
        status = "✅" if field in data else "❌"
        print(f"  {status} {desc:15s} ({field})")

    # 检查右侧UI三个关键参数
    print("\n📊 右侧UI关键参数检查：")
    if "statistics" in data:
        stats_checks = [
            ("table_modifications", "每表总修改数"),
            ("table_row_counts", "每表总行数"),
            ("column_total_modifications", "每列总修改数")
        ]
        for field, desc in stats_checks:
            status = "✅" if field in data["statistics"] else "❌"
            if field in data["statistics"]:
                count = len(data["statistics"][field])
                print(f"  {status} {desc:20s} - {count}个值")
            else:
                print(f"  {status} {desc:20s} - 缺失")

    # 检查修改行位置
    if "table_details" in data and len(data["table_details"]) > 0:
        table = data["table_details"][0]
        if "column_details" in table and len(table["column_details"]) > 0:
            col = table["column_details"][0]
            has_modified_rows = "modified_rows" in col
            status = "✅" if has_modified_rows else "❌"
            print(f"  {status} 修改行位置数据")

    print("\n📊 文件信息：")
    print(f"  - 版本: {data['metadata'].get('version')}")
    print(f"  - 周数: {data['metadata'].get('week')}")
    print(f"  - 参数总数: {data['metadata'].get('total_params')}")
    print(f"  - 表格数量: {len(data.get('table_names', []))}")
    print(f"  - 列数量: {len(data.get('column_names', []))}")

    # 验证列名
    if data.get('column_names') == STANDARD_COLUMNS:
        print("\n✅ 列名与标准配置完全一致")
    else:
        print("\n❌ 列名与标准配置不一致")

    print("\n" + "=" * 60)
    print(f"✅ 文件已生成: {filepath}")
    print("=" * 60)

    return filepath

if __name__ == "__main__":
    main()