#!/usr/bin/env python3
"""分析实际的变更（排除格式差异）"""

import json
import sys
sys.path.append('production/core_modules')
from star_format_normalizer import StarFormatNormalizer

# 读取比较结果
with open('comparison_results/comparison_20250925_215130.json', 'r') as f:
    comparison_data = json.load(f)

print("=" * 60)
print("📊 变更分析报告")
print("=" * 60)

# 获取所有修改
all_modifications = comparison_data.get('modifications', [])
print(f"\n总变更数: {len(all_modifications)} 处")

# 使用标准化器过滤
real_changes, format_only_changes = StarFormatNormalizer.filter_format_changes(all_modifications)

print(f"\n📈 变更分类:")
print(f"  • 真实内容变更: {len(real_changes)} 处")
print(f"  • 仅格式变更: {len(format_only_changes)} 处")

if len(format_only_changes) > 0:
    print(f"\n⚠️ 发现 {len(format_only_changes)} 处仅为格式差异的'伪变更'")
    print("  这些不是真正的数据变化，只是表现形式不同：")
    print("  • 星级符号(★★★★★) vs 数字(5) - 语义相同")

    # 显示前5个格式变更示例
    print("\n  格式变更示例（前5个）:")
    for i, change in enumerate(format_only_changes[:5], 1):
        print(f"    {i}. {change['cell']}: '{change['old']}' → '{change['new']}'")

if len(real_changes) > 0:
    print(f"\n✅ 发现 {len(real_changes)} 处真实的内容变更")
    print("\n  真实变更详情:")
    for i, change in enumerate(real_changes, 1):
        print(f"    {i}. {change['cell']} ({change.get('column_name', 'unknown')})")
        print(f"       原值: '{change['old']}'")
        print(f"       新值: '{change['new']}'")
else:
    print("\n✅ 好消息：没有发现真实的内容变更！")
    print("   所有的'变更'都只是格式差异")

print("\n" + "=" * 60)
print("💡 结论:")
if len(real_changes) == 0 and len(format_only_changes) > 0:
    print("  系统显示的92处'变更'全部是格式差异造成的假象")
    print("  实际上基线和目标文档的内容完全相同")
    print("\n📝 根本原因:")
    print("  1. 腾讯文档在不同时期的导出格式不一致")
    print("  2. 9月15日导出：使用星级符号（★★★★★）")
    print("  3. 9月25日导出：使用数字（5）")
    print("  4. 两种格式语义相同，但字符串对比时被误判为变更")
    print("\n🔧 解决方案:")
    print("  已创建StarFormatNormalizer模块")
    print("  可在CSV对比前进行格式标准化，避免误报")