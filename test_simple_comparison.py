#!/usr/bin/env python3
"""简单对比测试：9月15日基线 vs 9月25日文档"""

import os

def test_comparison():
    """测试对比旧基线与新文档的差异"""

    comparisons = [
        {
            'name': '出国销售计划表',
            'baseline': '/root/projects/tencent-doc-manager/csv_versions/2025_W39/baseline/tencent_出国销售计划表_20250915_0145_baseline_W39.csv',
            'target': '/root/projects/tencent-doc-manager/csv_versions/2025_W39/midweek/tencent_出国销售计划表_20250925_1956_midweek_W39.csv'
        },
        {
            'name': '小红书部门',
            'baseline': '/root/projects/tencent-doc-manager/csv_versions/2025_W39/baseline/tencent_小红书部门_20250915_0146_baseline_W39.csv',
            'target': '/root/projects/tencent-doc-manager/csv_versions/2025_W39/midweek/tencent_小红书部门_20250925_1959_midweek_W39.csv'
        }
    ]

    print("=" * 60)
    print("🔍 对比9月15日基线 vs 9月25日文档")
    print("=" * 60)

    has_any_changes = False

    for comp in comparisons:
        print(f"\n📄 {comp['name']}")

        if not os.path.exists(comp['baseline']):
            print(f"  ❌ 基线文件不存在")
            continue

        if not os.path.exists(comp['target']):
            print(f"  ❌ 目标文件不存在")
            continue

        # 读取文件内容
        with open(comp['baseline'], 'r', encoding='utf-8') as f:
            baseline_lines = f.readlines()

        with open(comp['target'], 'r', encoding='utf-8') as f:
            target_lines = f.readlines()

        # 对比差异
        baseline_size = os.path.getsize(comp['baseline'])
        target_size = os.path.getsize(comp['target'])

        size_diff = target_size - baseline_size
        line_diff = len(target_lines) - len(baseline_lines)

        print(f"  📅 基线: 2025-09-15 (行数: {len(baseline_lines)})")
        print(f"  📅 目标: 2025-09-25 (行数: {len(target_lines)})")
        print(f"  📏 文件大小差异: {size_diff:+d} 字节")
        print(f"  📝 行数差异: {line_diff:+d} 行")

        # 统计实际内容差异
        changed_lines = 0
        for i in range(min(len(baseline_lines), len(target_lines))):
            if baseline_lines[i] != target_lines[i]:
                changed_lines += 1

        if changed_lines > 0 or line_diff != 0:
            print(f"  ✅ 检测到实际差异！修改行数: {changed_lines}, 新增/删除行数: {abs(line_diff)}")
            has_any_changes = True
        else:
            print(f"  ⚠️ 文件内容完全相同")

    print("\n" + "=" * 60)
    if has_any_changes:
        print("🎯 总结：检测到文档有实际变化！")
        print("⚠️ 但UI显示全蓝色，说明系统使用了相同文件进行对比")
        print("💡 解决方案：需要运行批处理时指定使用9月15日的基线文件")
    else:
        print("⚠️ 9月15日和9月25日的文档完全相同")

if __name__ == "__main__":
    test_comparison()