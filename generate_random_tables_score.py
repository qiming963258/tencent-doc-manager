#!/usr/bin/env python3
"""
使用正式的综合打分生成器生成随机数量表格的综合打分文件
"""

import json
import random
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, '/root/projects/tencent-doc-manager')

from production.core_modules.comprehensive_score_generator_v2 import ComprehensiveScoreGeneratorV2
from production.core_modules.comparison_to_scoring_adapter import ComparisonToScoringAdapter

def generate_random_tables_data():
    """生成随机数量的表格数据"""
    # 随机生成5-15个表格
    num_tables = random.randint(5, 15)
    print(f"📊 生成 {num_tables} 个表格的数据...")

    # 表格名称模板
    table_templates = [
        "出国销售计划表", "回国销售计划表", "小红书部门", "抖音运营部",
        "微博推广组", "知乎内容组", "B站创作组", "淘宝直播组",
        "京东商城部", "拼多多团购", "美团外卖组", "饿了么配送",
        "滴滴出行部", "高德地图组", "百度搜索部", "腾讯视频组",
        "爱奇艺内容", "优酷土豆部", "网易云音乐", "QQ音乐组"
    ]

    # 随机选择表格名称
    selected_tables = random.sample(table_templates, min(num_tables, len(table_templates)))

    # 标准列名（从生成器复制）
    STANDARD_COLUMNS = [
        "序号", "项目类型", "来源", "任务发起时间", "目标对齐",
        "关键KR对齐", "具体计划内容", "邓总指导登记", "负责人",
        "协助人", "监督人", "重要程度", "预计完成时间", "完成进度",
        "完成链接", "经理分析复盘", "最新复盘时间", "对上汇报", "应用情况"
    ]

    # L1/L2/L3列分类
    L1_COLUMNS = ["关键KR对齐", "重要程度", "预计完成时间", "完成进度"]
    L2_COLUMNS = ["项目类型", "负责人", "具体计划内容"]

    # 生成每个表格的数据
    table_data_list = []
    excel_urls = {}

    for idx, table_name in enumerate(selected_tables):
        full_name = f"副本-测试版本-{table_name}"

        # 随机生成行数和修改数
        total_rows = random.randint(50, 300)
        total_modifications = random.randint(5, min(50, total_rows // 2))

        # 生成列修改数据
        # column_modifications应该包含完整的修改信息（字典列表）
        column_modifications = {}
        modifications = []

        for col_name in STANDARD_COLUMNS:
            # 根据列的风险等级决定修改概率
            if col_name in L1_COLUMNS:
                mod_prob = 0.7  # L1列更容易有修改
            elif col_name in L2_COLUMNS:
                mod_prob = 0.5  # L2列中等概率
            else:
                mod_prob = 0.2  # L3列较少修改

            column_mods = []  # 该列的修改信息列表

            if random.random() < mod_prob:
                # 该列有修改
                num_mods = random.randint(1, min(5, total_modifications))
                for _ in range(num_mods):
                    row_num = random.randint(1, total_rows)

                    # 完整修改信息
                    mod = {
                        'row': row_num,
                        'column': col_name,
                        'old_value': f"原值_{row_num}_{col_name[:2]}",
                        'new_value': f"新值_{row_num}_{col_name[:2]}",
                        'change_type': random.choice(['修改', '新增', '删除'])
                    }

                    column_mods.append(mod)
                    modifications.append(mod)

            column_modifications[col_name] = column_mods  # 存储该列的所有修改

        # 构建表格数据
        table_data = {
            'table_name': full_name,
            'total_rows': total_rows,
            'total_modifications': len(modifications),
            'modifications': modifications,
            'column_modifications': column_modifications
        }

        table_data_list.append(table_data)

        # 生成Excel URL
        excel_urls[full_name] = f"https://docs.qq.com/sheet/test_{idx:03d}"

    return table_data_list, excel_urls

def main():
    """主函数"""
    print("🔄 开始生成随机表格数量的综合打分文件...")

    # 生成随机表格数据
    table_data_list, excel_urls = generate_random_tables_data()

    # 获取当前周数
    week_number = datetime.now().isocalendar()[1]

    # 创建生成器实例
    generator = ComprehensiveScoreGeneratorV2()

    # 生成综合打分文件
    filepath = generator.generate(
        week_number=str(week_number),
        table_data_list=table_data_list,
        excel_urls=excel_urls
    )

    print(f"\n✅ 综合打分文件生成成功！")
    print(f"📁 文件路径: {filepath}")

    # 验证生成的文件
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"\n📊 文件统计:")
    print(f"  - 表格数量: {len(data.get('table_names', []))}")
    print(f"  - 总修改数: {data.get('metadata', {}).get('total_params', 0)}")

    if 'heatmap_data' in data:
        matrix = data['heatmap_data'].get('matrix', [])
        if matrix:
            print(f"  - 矩阵大小: {len(matrix)}×{len(matrix[0]) if matrix else 0}")

    print(f"  - 数据版本: {data.get('metadata', {}).get('version', 'unknown')}")

    return filepath

if __name__ == "__main__":
    filepath = main()