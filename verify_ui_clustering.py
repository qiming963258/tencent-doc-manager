#!/usr/bin/env python3
"""
验证UI聚类切换功能
"""

import requests
import json

print("🎯 验证UI聚类切换功能完整性测试")
print("=" * 60)

# 测试两种排序模式
modes = ['default', 'intelligent']
results = {}

for mode in modes:
    url = f"http://127.0.0.1:8089/api/data?sorting={mode}"
    response = requests.get(url)
    data = response.json()

    if data.get('success'):
        results[mode] = {
            'columns': data['data']['column_names'],
            'matrix_sample': data['data']['heatmap_data']['matrix'][0][:10] if data['data']['heatmap_data']['matrix'] else [],
            'clustering_applied': data['data'].get('clustering_applied', False)
        }

# 分析结果
print("\n📊 排序模式对比:")
print("-" * 60)

print("\n1️⃣ 默认排序（按原始顺序）:")
print(f"   前5列: {results['default']['columns'][:5]}")
print(f"   热力值: {[round(v, 2) for v in results['default']['matrix_sample'][:5]]}")
print(f"   聚类应用: {results['default']['clustering_applied']}")

print("\n2️⃣ 智能聚类（按风险等级分组）:")
print(f"   前5列: {results['intelligent']['columns'][:5]}")
print(f"   热力值: {[round(v, 2) for v in results['intelligent']['matrix_sample'][:5]]}")
print(f"   聚类应用: {results['intelligent']['clustering_applied']}")

# 验证变化
print("\n✅ 验证结果:")
print("-" * 60)

columns_changed = results['default']['columns'] != results['intelligent']['columns']
matrix_changed = results['default']['matrix_sample'] != results['intelligent']['matrix_sample']

if columns_changed:
    print("✅ 列顺序已改变 - 聚类功能正常")

    # 显示具体变化
    print("\n📋 列重排详情:")
    for i in range(min(10, len(results['default']['columns']))):
        default_col = results['default']['columns'][i]
        intelligent_col = results['intelligent']['columns'][i]
        if default_col != intelligent_col:
            print(f"   位置{i}: {default_col} → {intelligent_col}")
else:
    print("❌ 列顺序未改变 - 聚类可能未生效")

if matrix_changed:
    print("\n✅ 热力图矩阵已重排 - 数据同步正常")
else:
    print("\n⚠️ 热力图矩阵未重排")

# 分析聚类效果
print("\n🔥 聚类效果分析:")
print("-" * 60)

# 分析智能聚类后的热力值分布
intelligent_values = results['intelligent']['matrix_sample']
if intelligent_values:
    high_risk = [v for v in intelligent_values if v >= 0.7]
    medium_risk = [v for v in intelligent_values if 0.3 <= v < 0.7]
    low_risk = [v for v in intelligent_values if v < 0.3]

    print(f"前10个值的风险分布:")
    print(f"  🔴 高风险(≥0.7): {len(high_risk)}个")
    print(f"  🟠 中风险(0.3-0.7): {len(medium_risk)}个")
    print(f"  🟢 低风险(<0.3): {len(low_risk)}个")

    # 检查是否形成了聚类
    if intelligent_values[:5].count(0.9) >= 3:
        print("\n✅ 高风险列成功聚集在前部")
    elif intelligent_values[-5:].count(0.05) >= 3:
        print("\n✅ 低风险列成功聚集在后部")

print("\n" + "=" * 60)
print("🎉 UI聚类切换功能验证完成！")
print("\n💡 使用说明:")
print("1. 在UI中点击'默认排序'按钮 - 显示原始列顺序")
print("2. 在UI中点击'智能聚类'按钮 - 显示风险聚类顺序")
print("3. 高风险列（红色）会聚集在一起")
print("4. 低风险列（蓝色）会聚集在一起")