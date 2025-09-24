#!/usr/bin/env python3
"""测试带格式标准化的CSV对比"""

from unified_csv_comparator import UnifiedCSVComparator
import json

# 创建对比器实例
comparator = UnifiedCSVComparator()

print("=" * 60)
print("🔍 测试带格式标准化的CSV对比")
print("=" * 60)

# 对比文件
baseline = '/root/projects/tencent-doc-manager/csv_versions/2025_W39/baseline/tencent_出国销售计划表_20250915_0145_baseline_W39.csv'
target = '/root/projects/tencent-doc-manager/csv_versions/2025_W39/midweek/tencent_出国销售计划表_20250925_1956_midweek_W39.csv'

print(f"\n📁 基线文件: {baseline.split('/')[-1]}")
print(f"📁 目标文件: {target.split('/')[-1]}")

# 执行对比
result = comparator.compare(baseline, target)

print(f"\n📊 对比结果:")
print(f"  • 星级标准化: {'启用' if result.get('star_normalization') else '禁用'}")

if 'statistics' in result:
    stats = result['statistics']
    print(f"\n📈 统计信息:")

    if 'original_total' in stats:
        print(f"  • 原始变更数: {stats.get('original_total', 0)} 处")
        print(f"  • 格式变更数: {stats.get('format_only_changes', 0)} 处")
        print(f"  • 真实变更数: {stats.get('total_modifications', 0)} 处")
        print(f"  • 相似度: {stats.get('similarity', 0):.1%}")
    else:
        print(f"  • 总变更数: {stats.get('total_modifications', 0)} 处")
        print(f"  • 相似度: {stats.get('similarity', 0):.1%}")

# 显示真实变更
real_mods = result.get('modifications', [])
if len(real_mods) > 0:
    print(f"\n⚠️ 发现 {len(real_mods)} 处真实内容变更:")
    for i, mod in enumerate(real_mods[:5], 1):
        print(f"  {i}. {mod['cell']}: '{mod.get('old', '')}' → '{mod.get('new', '')}'")
    if len(real_mods) > 5:
        print(f"  ... 还有 {len(real_mods) - 5} 处变更")
else:
    print("\n✅ 没有发现真实的内容变更！")

# 显示格式变更信息
format_only = result.get('format_only_changes', [])
if len(format_only) > 0:
    print(f"\n💡 过滤掉了 {len(format_only)} 处仅格式差异:")
    print("  例如: ★★★★★ → 5 (语义相同)")

# 保存详细结果
output_file = 'comparison_results/normalized_comparison_test.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"\n📝 详细结果已保存到: {output_file}")
print("=" * 60)