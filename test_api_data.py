#!/usr/bin/env python3
"""测试API返回的实际数据"""

import requests
import json
import time

# 等待服务器启动
print("⏳ 等待服务器启动...")
time.sleep(2)

try:
    # 1. 测试主数据API
    print("\n📊 测试 /api/data 接口:")
    response = requests.get("http://localhost:8089/api/data", timeout=5)
    if response.status_code == 200:
        data = response.json()
        if 'data' in data and 'heatmap_data' in data['data']:
            matrix = data['data']['heatmap_data'].get('matrix', [])
            print(f"  - 热力图矩阵大小: {len(matrix)}行 × {len(matrix[0]) if matrix else 0}列")

            # 查找高值
            high_values = []
            for row in matrix:
                for val in row:
                    if val > 0.8:
                        high_values.append(val)
            print(f"  - 值>0.8的数量: {len(high_values)}")
            if high_values:
                print(f"  - 高值样本: {high_values[:5]}")

    # 2. 测试详细分数API（检查total_rows）
    print("\n📊 测试 /api/detailed_scores 接口:")
    test_tables = [
        "副本-测试版本-出国销售计划表",
        "副本-测试版本-回国销售计划表",
        "测试版本-小红书部门"
    ]

    for table_name in test_tables:
        url = f"http://localhost:8089/api/detailed_scores/{table_name}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                total_rows = data['data'].get('total_rows', 'N/A')
                print(f"  - {table_name}: total_rows = {total_rows}")
        else:
            print(f"  - {table_name}: 请求失败 ({response.status_code})")

    # 3. 测试真实CSV数据API
    print("\n📊 测试 /api/real_csv_data 接口:")
    response = requests.get("http://localhost:8089/api/real_csv_data", timeout=5)
    if response.status_code == 200:
        data = response.json()
        if 'success' in data and data['success']:
            tables = data.get('tables', [])
            for table in tables:
                name = table.get('name', 'Unknown')
                total_rows = table.get('total_rows', 'N/A')
                print(f"  - {name}: total_rows = {total_rows}")

except requests.exceptions.RequestException as e:
    print(f"\n❌ 服务器连接失败: {e}")
    print("请确保服务器正在运行在端口8089")
except Exception as e:
    print(f"\n❌ 错误: {e}")