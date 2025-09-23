#!/usr/bin/env python3
"""
测试API聚类响应
"""

import requests
import json

def test_api():
    """测试API的聚类响应"""

    # 测试默认排序
    print("📊 测试默认排序...")
    response = requests.get("http://127.0.0.1:8089/api/data?sorting=default")
    data_default = response.json()
    cols_default = data_default['data']['column_names']
    print(f"默认排序前5列: {cols_default[:5]}")

    # 测试智能聚类
    print("\n🔄 测试智能聚类...")
    response = requests.get("http://127.0.0.1:8089/api/data?sorting=intelligent")
    data_intelligent = response.json()
    cols_intelligent = data_intelligent['data']['column_names']
    print(f"智能聚类前5列: {cols_intelligent[:5]}")

    # 比较结果
    if cols_default != cols_intelligent:
        print("\n✅ API聚类功能正常 - 列顺序已改变")
        print(f"   变化: {cols_default[:5]} -> {cols_intelligent[:5]}")
    else:
        print("\n❌ API聚类功能异常 - 列顺序未改变")

    # 检查热力图矩阵
    matrix_default = data_default['data']['heatmap_data']['matrix'][0] if data_default['data']['heatmap_data']['matrix'] else []
    matrix_intelligent = data_intelligent['data']['heatmap_data']['matrix'][0] if data_intelligent['data']['heatmap_data']['matrix'] else []

    if matrix_default and matrix_intelligent:
        print(f"\n热力图数据:")
        print(f"  默认排序前5个值: {matrix_default[:5]}")
        print(f"  智能聚类前5个值: {matrix_intelligent[:5]}")

        if matrix_default[:5] != matrix_intelligent[:5]:
            print("  ✅ 热力图数据已重排")
        else:
            print("  ❌ 热力图数据未重排")

if __name__ == "__main__":
    test_api()