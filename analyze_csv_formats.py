#!/usr/bin/env python3
"""分析CSV文件格式差异"""

import csv
import json

def analyze_csv_column(file_path, column_name='重要程度'):
    """分析CSV文件中指定列的内容"""
    print(f"\n📁 分析文件: {file_path.split('/')[-1]}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            # 跳过前面的空行
            for _ in range(2):
                next(reader)

            # 重新读取带有正确header的CSV
            f.seek(0)
            lines = f.readlines()

            # 找到实际的header行（通常是第3行）
            header_line = None
            for i, line in enumerate(lines[:5]):
                if '项目类型' in line and '重要程度' in line:
                    header_line = i
                    break

            if header_line is None:
                print("  ❌ 找不到标题行")
                return None

            # 重新解析CSV
            f.seek(0)
            for _ in range(header_line):
                f.readline()

            reader = csv.DictReader(f)

            # 分析前20行数据
            column_values = []
            unique_formats = set()

            for i, row in enumerate(reader):
                if i >= 20:  # 只分析前20行
                    break

                if column_name in row:
                    value = row[column_name]
                    if value and value.strip():
                        column_values.append(value)

                        # 检测格式类型
                        if '★' in value:
                            unique_formats.add('stars')
                        elif value.isdigit():
                            unique_formats.add('numbers')
                        else:
                            unique_formats.add('other')

            print(f"  ✅ 找到 {len(column_values)} 个非空值")
            print(f"  📊 格式类型: {', '.join(unique_formats) if unique_formats else '无数据'}")

            # 显示前5个样本
            print(f"  📋 前5个样本:")
            for j, val in enumerate(column_values[:5], 1):
                # 显示原始字符和它们的Unicode编码
                print(f"     {j}. '{val}' (长度: {len(val)})")
                if '★' in val:
                    star_count = val.count('★')
                    empty_star_count = val.count('☆')
                    print(f"        → {star_count} 个实心星 + {empty_star_count} 个空心星")

            return {
                'format_types': list(unique_formats),
                'sample_values': column_values[:5],
                'total_values': len(column_values)
            }

    except Exception as e:
        print(f"  ❌ 错误: {e}")
        return None

# 分析两个文件
baseline_file = '/root/projects/tencent-doc-manager/csv_versions/2025_W39/baseline/tencent_出国销售计划表_20250915_0145_baseline_W39.csv'
target_file = '/root/projects/tencent-doc-manager/csv_versions/2025_W39/midweek/tencent_出国销售计划表_20250925_1956_midweek_W39.csv'

print("=" * 60)
print("🔍 CSV格式差异分析")
print("=" * 60)

baseline_result = analyze_csv_column(baseline_file)
target_result = analyze_csv_column(target_file)

print("\n" + "=" * 60)
print("📊 分析结果总结")
print("=" * 60)

if baseline_result and target_result:
    print(f"\n✅ 基线文件格式: {baseline_result['format_types']}")
    print(f"✅ 目标文件格式: {target_result['format_types']}")

    if baseline_result['format_types'] != target_result['format_types']:
        print("\n⚠️ 格式不一致！")
        print("🔧 原因分析:")
        print("  1. 腾讯文档在9月15日到9月25日期间更改了导出设置")
        print("  2. 可能有人手动编辑了其中一个文件")
        print("  3. 不同的导出方式（网页版 vs 客户端）")
        print("\n💡 解决方案:")
        print("  需要在对比前进行格式标准化处理")
        print("  将星级(★★★★★)转换为数字(5)进行统一比较")
    else:
        print("\n✅ 格式一致")