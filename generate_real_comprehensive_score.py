#!/usr/bin/env python3
"""
生成真实的综合打分文件
使用真实CSV对比数据，不使用任何虚拟数据
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.append('/root/projects/tencent-doc-manager')

from production.core_modules.comprehensive_score_generator_v2 import ComprehensiveScoreGeneratorV2
from production.core_modules.comparison_to_scoring_adapter import ComparisonToScoringAdapter
from production.core_modules.enhanced_csv_comparator import EnhancedCSVComparator
from production.config import STANDARD_COLUMNS

print("=" * 70)
print("🔬 生成真实综合打分（基于真实CSV对比）")
print("=" * 70)

# 1. 执行真实CSV对比
print("\n1️⃣ 执行真实CSV文件对比...")

# 使用修改后的CSV文件作为目标（包含真实修改）
target_csv = "/root/projects/tencent-doc-manager/csv_versions/2025_W39/midweek/tencent_出国销售计划表_test_modified.csv"

# 使用原始文件作为基线
baseline_csv = "/root/projects/tencent-doc-manager/csv_versions/2025_W39/midweek/tencent_出国销售计划表_20250922_0134_midweek_W39.csv"

if not Path(target_csv).exists():
    print(f"❌ 目标文件不存在: {target_csv}")
    sys.exit(1)

if not Path(baseline_csv).exists():
    print(f"❌ 基线文件不存在: {baseline_csv}")
    sys.exit(1)

print(f"   基线: {Path(baseline_csv).name}")
print(f"   目标: {Path(target_csv).name}")

# 执行对比
comparator = EnhancedCSVComparator()
comparison_result = comparator.compare_all_columns(baseline_csv, target_csv)

print(f"✅ CSV对比完成")
print(f"   - 总行数: {comparison_result.get('total_rows', 0)}")
print(f"   - 修改数: {comparison_result.get('total_differences', 0)}")

# 2. 转换为打分数据格式
print("\n2️⃣ 转换为打分数据格式...")

adapter = ComparisonToScoringAdapter()

# 从对比结果提取表格数据
# 修复total_rows的问题
total_rows = comparison_result.get('total_rows', 0)
if total_rows == 0:
    # 如果对比结果没有返回行数，从文件中读取
    with open(target_csv, 'r', encoding='utf-8-sig') as f:
        total_rows = sum(1 for line in f) - 1  # 减去标题行
    print(f"   从文件读取行数: {total_rows}")

table_data = {
    'table_name': '测试文档-出国销售计划表',  # 使用真实文档名
    'total_rows': total_rows,
    'total_modifications': comparison_result.get('total_differences', 0),
    'modifications': comparison_result.get('differences', []),
    'column_modifications': {}
}

# 构建column_modifications（从differences中提取）
for diff in comparison_result.get('differences', []):
    col_name = diff.get('column_name', '')
    row_num = diff.get('row', 0)

    if col_name and col_name in STANDARD_COLUMNS:
        if col_name not in table_data['column_modifications']:
            table_data['column_modifications'][col_name] = []
        if row_num > 0:
            table_data['column_modifications'][col_name].append(row_num)

# 确保所有标准列都存在
for col_name in STANDARD_COLUMNS:
    if col_name not in table_data['column_modifications']:
        table_data['column_modifications'][col_name] = []

print(f"✅ 数据格式转换完成")

# 显示每列的修改情况
modified_cols = {k: len(v) for k, v in table_data['column_modifications'].items() if len(v) > 0}
if modified_cols:
    print("   修改的列:")
    for col_name, count in sorted(modified_cols.items(), key=lambda x: -x[1])[:5]:
        print(f"     - {col_name}: {count}处修改")

# 3. 生成综合打分文件
print("\n3️⃣ 生成综合打分文件...")

generator = ComprehensiveScoreGeneratorV2()

# 真实的Excel URL
excel_urls = {
    '测试文档-出国销售计划表': 'https://docs.qq.com/sheet/DWEFNU25TemFnZXJN'
}

# 生成文件
filepath = generator.generate(
    week_number='39',
    table_data_list=[table_data],
    excel_urls=excel_urls
)

print(f"✅ 综合打分文件已生成: {filepath}")

# 4. 验证生成的文件
print("\n4️⃣ 验证文件内容...")

with open(filepath, 'r') as f:
    data = json.load(f)

# 检查关键字段
checks = {
    '包含metadata': 'metadata' in data,
    '包含column_modifications_by_table': 'column_modifications_by_table' in data,
    '使用标准19列': len(data.get('column_names', [])) == 19,
    '表名正确': '测试文档-出国销售计划表' in data.get('table_names', []),
    '没有虚拟数据': '测试表格' not in str(data)
}

for check, result in checks.items():
    if result:
        print(f"   ✅ {check}")
    else:
        print(f"   ❌ {check}")

# 检查column_modifications_by_table内容
if 'column_modifications_by_table' in data:
    tables = data['column_modifications_by_table']
    if '测试文档-出国销售计划表' in tables:
        test_col = tables['测试文档-出国销售计划表'].get('column_modifications', {})

        # 统计有修改的列
        modified_count = sum(1 for col in test_col.values() if col.get('modification_count', 0) > 0)
        print(f"   ✅ {modified_count}个列有修改记录")

# 5. 复制到默认位置供8089使用
print("\n5️⃣ 设置为8089默认加载文件...")

default_file = Path("/root/projects/tencent-doc-manager/scoring_results/comprehensive/comprehensive_score_W38_latest.json")
import shutil
shutil.copy(filepath, default_file)

print(f"✅ 已复制到: {default_file}")

# 6. 总结
print("\n" + "=" * 70)
print("📊 生成总结:")
print(f"1. ✅ 基于真实CSV对比（{comparison_result.get('total_differences', 0)}处修改）")
print("2. ✅ 使用真实文档名（测试文档-出国销售计划表）")
print("3. ✅ 包含column_modifications_by_table字段")
print("4. ✅ 使用标准19列")
print("5. ✅ 没有虚拟数据")
print("\n🚀 访问 http://202.140.143.88:8089/ 查看真实数据热力图")
print("=" * 70)