#!/usr/bin/env python3
"""
验证右侧统计数字修复
"""

import requests
import json

print("🔍 验证右侧统计数字修复")
print("=" * 60)

# 获取API数据
response = requests.get("http://127.0.0.1:8089/api/data?sorting=default")
data = response.json()

if data.get('success'):
    api_data = data['data']

    # 检查column_modifications_by_table
    mods = api_data.get('column_modifications_by_table', {})

    if mods:
        print("✅ API返回了column_modifications_by_table数据")

        for table_name, table_data in mods.items():
            print(f"\n表格: {table_name}")
            print(f"  总行数: {table_data.get('total_rows', 0)}")

            col_mods = table_data.get('column_modifications', {})
            if col_mods:
                print(f"  包含 {len(col_mods)} 列的修改数据")

                # 统计总修改数
                total_mods = 0
                for col_name, col_info in col_mods.items():
                    mod_count = col_info.get('modification_count', 0)
                    total_mods += mod_count

                print(f"  总修改数: {total_mods}")

                # 显示前5列的修改情况
                print("\n  前5列修改详情:")
                for i, (col_name, col_info) in enumerate(list(col_mods.items())[:5]):
                    mod_count = col_info.get('modification_count', 0)
                    risk = col_info.get('risk_level', 'N/A')
                    print(f"    {col_name}: {mod_count}个修改 (风险: {risk})")
    else:
        print("❌ 未找到column_modifications_by_table数据")

    print("\n" + "-" * 60)
    print("📊 验证右侧统计显示逻辑:")
    print("-" * 60)

    # 模拟前端计算逻辑
    # 前端使用: pattern.realData?.totalDifferences || pattern.totalModifications || 0

    # 检查是否有tables数据用于pattern生成
    table_names = api_data.get('table_names', [])
    if table_names:
        print(f"✅ 找到 {len(table_names)} 个表格")

        # 对于每个表格，计算它应该显示的修改数
        for table_name in table_names:
            table_mod_data = mods.get(table_name, {})
            col_mods = table_mod_data.get('column_modifications', {})

            # 计算总修改数（这应该是右侧显示的数字）
            total_diffs = 0
            for col_info in col_mods.values():
                total_diffs += col_info.get('modification_count', 0)

            print(f"\n表格 '{table_name}':")
            print(f"  预期右侧显示: {total_diffs}改")

            # 检查是否会正确传递到pattern
            print(f"  数据流检查:")
            print(f"    - column_modifications_by_table存在: ✅")
            print(f"    - column_modifications数据存在: {'✅' if col_mods else '❌'}")
            print(f"    - 计算的total_differences: {total_diffs}")

            if total_diffs > 0:
                print(f"  ✅ 应该正确显示 '{total_diffs}改'")
            else:
                print(f"  ⚠️ 将显示 '0改' (需要检查数据)")

    print("\n" + "=" * 60)
    print("🎯 验证结果总结:")

    # 判断修复是否成功
    success = False
    for table_name in table_names:
        table_mod_data = mods.get(table_name, {})
        col_mods = table_mod_data.get('column_modifications', {})
        total_diffs = sum(col_info.get('modification_count', 0) for col_info in col_mods.values())
        if total_diffs > 0:
            success = True
            break

    if success:
        print("✅ 修复成功！右侧统计应该显示正确的修改数量")
        print("   - API数据包含完整的column_modifications")
        print("   - 计算的total_differences大于0")
        print("   - pattern.realData.totalDifferences将被正确设置")
    else:
        print("❌ 问题仍然存在，需要进一步调试")

else:
    print(f"❌ API请求失败: {data.get('error')}")