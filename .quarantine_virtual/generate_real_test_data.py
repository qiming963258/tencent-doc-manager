#!/usr/bin/env python3
"""
生成真实的测试数据
"""

import json
import random
from pathlib import Path
from datetime import datetime

# 标准列名
STANDARD_COLUMNS = [
    "序号", "项目类型", "来源", "任务发起时间", "目标对齐",
    "关键KR对齐", "具体计划内容", "邓总指导登记", "负责人",
    "协助人", "监督人", "重要程度", "预计完成时间", "完成进度",
    "完成链接", "经理分析复盘", "最新复盘时间", "对上汇报", "应用情况"
]

def generate_test_comparison_data():
    """生成测试对比数据"""

    # 创建3个表格的对比数据
    tables = [
        ("副本-测试版本-出国销售计划表", 150, 20),
        ("副本-测试版本-回国销售计划表", 120, 15),
        ("测试版本-小红书部门", 100, 12)
    ]

    all_comparison_files = []

    for table_name, total_rows, num_modifications in tables:
        # 生成修改数据
        modifications = []
        modified_rows = random.sample(range(1, total_rows), min(num_modifications, total_rows))

        for row in modified_rows:
            # 随机选择要修改的列
            col_idx = random.randint(0, 18)
            col_name = STANDARD_COLUMNS[col_idx]

            mod = {
                "row": row,
                "column": col_name,
                "old_value": f"原值_{row}_{col_idx}",
                "new_value": f"新值_{row}_{col_idx}",
                "change_type": random.choice(["修改", "新增", "删除"])
            }
            modifications.append(mod)

        # 按列分组
        column_modifications = {}
        for col in STANDARD_COLUMNS:
            column_modifications[col] = [m for m in modifications if m['column'] == col]

        # 创建对比结果
        comparison_data = {
            "file_info": {
                "table_name": table_name,
                "previous_file": f"previous_{table_name}.csv",
                "current_file": f"current_{table_name}.csv",
                "comparison_time": datetime.now().isoformat()
            },
            "summary": {
                "total_rows": total_rows,
                "total_modifications": len(modifications),
                "modification_rate": len(modifications) / total_rows
            },
            "modifications": modifications,
            "column_modifications": column_modifications,
            "differences": {
                "added_rows": [],
                "deleted_rows": [],
                "modified_rows": modified_rows
            }
        }

        # 保存文件
        filename = f"/root/projects/tencent-doc-manager/csv_security_results/{table_name.replace('-', '_')}_comparison.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(comparison_data, f, ensure_ascii=False, indent=2)

        print(f"✅ 生成对比文件: {filename}")
        print(f"   - 总行数: {total_rows}")
        print(f"   - 修改数: {len(modifications)}")

        all_comparison_files.append(filename)

    return all_comparison_files

def generate_comprehensive_score_with_real_data(comparison_files):
    """使用真实数据生成综合打分"""
    import sys
    sys.path.append('/root/projects/tencent-doc-manager')

    from production.core_modules.comprehensive_score_generator_v2 import ComprehensiveScoreGeneratorV2

    # URL映射
    excel_urls = {
        '副本_测试版本_出国销售计划表': 'https://docs.qq.com/sheet/DWEFNU25TemFnZXJN',
        '副本_测试版本_回国销售计划表': 'https://docs.qq.com/sheet/DWGZDZkxpaGVQaURr',
        '测试版本_小红书部门': 'https://docs.qq.com/sheet/DWFJzdWNwd0RGbU5R'
    }

    generator = ComprehensiveScoreGeneratorV2()
    filepath = generator.generate('39', comparison_files=comparison_files, excel_urls=excel_urls)

    print(f"\n✅ 生成综合打分文件: {filepath}")

    # 验证数据
    with open(filepath, 'r') as f:
        data = json.load(f)
        matrix = data.get('heatmap_data', {}).get('matrix', [])
        if matrix:
            non_default = sum(1 for row in matrix for v in row if v != 0.05)
            total = len(matrix) * (len(matrix[0]) if matrix else 0)
            print(f"📊 矩阵统计:")
            print(f"   - 大小: {len(matrix)}×{len(matrix[0]) if matrix else 0}")
            print(f"   - 非默认值: {non_default}/{total} ({non_default*100//total if total else 0}%)")

        hover = data.get('hover_data', {})
        if hover and hover.get('data'):
            print(f"📊 悬浮数据:")
            print(f"   - 版本: {hover.get('version', '1.0')}")
            for i, table_hover in enumerate(hover['data'][:3]):
                if 'column_details' in table_hover:
                    total_mods = sum(len(col.get('modification_details', []))
                                   for col in table_hover['column_details'])
                    print(f"   - 表格{i+1}: {total_mods}个详细修改")

if __name__ == "__main__":
    print("🔄 开始生成真实测试数据...")
    comparison_files = generate_test_comparison_data()
    print(f"\n🔄 生成综合打分文件...")
    generate_comprehensive_score_with_real_data(comparison_files)