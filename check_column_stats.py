#!/usr/bin/env python3
"""检查列修改统计数据"""

import requests
import json

# 获取API数据
response = requests.get("http://127.0.0.1:8089/api/data?sorting=default")
data = response.json()

if data.get('success'):
    api_data = data['data']

    # 检查column_modifications_by_table
    mods = api_data.get('column_modifications_by_table', {})

    if mods:
        print("📊 API返回的列修改统计数据:")
        print("=" * 60)

        for table_name, table_data in mods.items():
            print(f"\n表格: {table_name}")
            col_mods = table_data.get('column_modifications', {})

            if col_mods:
                print(f"  找到 {len(col_mods)} 列的修改数据:")
                for i, (col_name, col_info) in enumerate(col_mods.items()):
                    mod_count = col_info.get('modification_count', 0)
                    modified_rows = col_info.get('modified_rows', [])
                    risk_level = col_info.get('risk_level', 'N/A')

                    if mod_count > 0:
                        print(f"    ✅ {col_name}: {mod_count}个修改 (风险级别: {risk_level}, 行: {modified_rows})")
                    else:
                        print(f"    ❌ {col_name}: 0个修改")

            else:
                print("  ❌ 没有column_modifications数据")
    else:
        print("❌ API未返回column_modifications_by_table数据")

    # 检查列名列表
    columns = api_data.get('column_names', [])
    print(f"\n📋 列名列表 ({len(columns)}列):")
    print(f"  前5列: {columns[:5]}")

    # 检查热力图数据
    heatmap_matrix = api_data.get('heatmap_data', {}).get('matrix', [])
    if heatmap_matrix:
        print(f"\n🔥 热力图矩阵:")
        print(f"  尺寸: {len(heatmap_matrix)}x{len(heatmap_matrix[0]) if heatmap_matrix else 0}")
        print(f"  第一行前5个值: {heatmap_matrix[0][:5] if heatmap_matrix else []}")
else:
    print(f"❌ API请求失败: {data.get('error')}")