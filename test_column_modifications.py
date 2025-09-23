#!/usr/bin/env python3
"""
测试column_modifications是否正确传递到UI
"""

import sys
import json
from pathlib import Path

# 添加项目路径
sys.path.append('/root/projects/tencent-doc-manager')

# 导入生成器
from production.core_modules.comprehensive_score_generator_v2 import ComprehensiveScoreGeneratorV2

# 创建测试数据
# 构建正确格式的modifications列表（包含所有列的修改详情）
modifications = []
column_modifications = {
    '序号': [5, 10, 15],
    '项目类型': [20, 25],
    '来源': [30],
    '任务发起时间': [],
    '目标对齐': [40, 45, 50, 55],
    '关键KR对齐': [60],
    '具体计划内容': [65, 70],
    '邓总指导登记': [],
    '负责人': [75],
    '协助人': [],
    '监督人': [80, 85],
    '重要程度': [],
    '预计完成时间': [90, 95],  # 这是第13列，应该显示2处修改
    '完成进度': [],
    '完成链接': [],
    '经理分析复盘': [],
    '最新复盘时间': [],
    '对上汇报': [],
    '应用情况': []
}

# 将column_modifications转换为modifications格式
for col_name, row_list in column_modifications.items():
    for row_num in row_list:
        modifications.append({
            'row': row_num,
            'column': col_name,
            'old_value': f'旧值{row_num}',
            'new_value': f'新值{row_num}',
            'change_type': 'modified'
        })

table_data = [{
    'table_name': '测试表格',
    'total_rows': 100,
    'total_modifications': len(modifications),
    'modifications': modifications,
    'column_modifications': column_modifications
}]

# 生成综合打分
generator = ComprehensiveScoreGeneratorV2()

# 生成文件
filepath = generator.generate(
    week_number='39',
    table_data_list=table_data,
    excel_urls={'测试表格': 'https://docs.qq.com/sheet/test'}
)

print(f"✅ 生成测试文件: {filepath}")

# 读取并验证
with open(filepath, 'r') as f:
    data = json.load(f)

# 检查column_modifications_by_table
if 'column_modifications_by_table' in data:
    print("✅ column_modifications_by_table字段存在")

    test_table = data['column_modifications_by_table'].get('测试表格', {})
    if test_table:
        col_mods = test_table.get('column_modifications', {})

        # 检查预计完成时间列
        预计完成时间 = col_mods.get('预计完成时间', {})

        print(f"📊 预计完成时间列的修改信息:")
        print(f"   - modified_rows: {预计完成时间.get('modified_rows', [])}")
        print(f"   - modification_count: {预计完成时间.get('modification_count', 0)}")

        if 预计完成时间.get('modification_count') == 2:
            print("✅ 该列修改数量正确：2处")
        else:
            print(f"❌ 该列修改数量错误：期望2，实际{预计完成时间.get('modification_count', 0)}")
else:
    print("❌ column_modifications_by_table字段缺失！")

print(f"\n文件路径: {filepath}")
print("请在8089 UI中加载此文件测试悬浮窗是否正确显示'该列修改: 2处'")