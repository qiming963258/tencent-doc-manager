#!/usr/bin/env python3
"""
测试8089 UI悬浮窗是否正确显示列修改数
"""

import time
import requests
import json

# 等待服务启动
time.sleep(3)

print("测试8089 UI悬浮窗显示")
print("=" * 50)

# 1. 测试API是否返回正确数据
try:
    response = requests.get('http://localhost:8089/api/comprehensive-score')
    data = response.json()

    if data.get('success'):
        score_data = data.get('data', {})

        # 检查column_modifications_by_table
        col_mods_by_table = score_data.get('column_modifications_by_table', {})

        if col_mods_by_table:
            print("✅ API返回了column_modifications_by_table")

            # 检查测试表格
            test_table = col_mods_by_table.get('测试表格', {})
            if test_table:
                col_mods = test_table.get('column_modifications', {})

                # 检查预计完成时间列
                预计完成 = col_mods.get('预计完成时间', {})
                if 预计完成:
                    mod_count = 预计完成.get('modification_count', 0)
                    mod_rows = 预计完成.get('modified_rows', [])
                    print(f"✅ 预计完成时间列:")
                    print(f"   - 该列修改: {mod_count}处")
                    print(f"   - 修改行号: {mod_rows}")

                    if mod_count == 2:
                        print("\n🎉 测试成功！悬浮窗应该显示'该列修改: 2处'")
                    else:
                        print(f"\n⚠️ 修改数不正确，期望2，实际{mod_count}")
                else:
                    print("❌ 找不到预计完成时间列数据")
            else:
                print("❌ 找不到测试表格数据")
        else:
            print("❌ API未返回column_modifications_by_table")
    else:
        print("❌ API返回失败")

except Exception as e:
    print(f"❌ 请求失败: {e}")

print("\n" + "=" * 50)
print("访问 http://202.140.143.88:8089/ 查看UI")
print("将鼠标悬停在第1行(测试表格)第13列(预计完成时间)的单元格上")
print("应该看到悬浮窗显示'该列修改: 2处'")