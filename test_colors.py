#!/usr/bin/env python3
"""测试颜色映射函数"""

import math

def get_scientific_heat_color(value):
    """模拟JavaScript颜色映射函数"""
    v = max(0, min(1, value))

    if v <= 0.2:
        # 深蓝色到浅蓝色 (0.0-0.2)
        t = v / 0.2
        r = math.floor(8 + t * 42)     # 8→50
        g = math.floor(48 + t * 102)   # 48→150
        b = math.floor(107 + t * 98)   # 107→205
        return f"rgb({r}, {g}, {b})"
    elif v <= 0.4:
        # 浅蓝色到青绿色 (0.2-0.4)
        t = (v - 0.2) / 0.2
        r = math.floor(50 + t * 0)    # 50→50
        g = math.floor(150 + t * 55)  # 150→205
        b = math.floor(205 - t * 55)  # 205→150
        return f"rgb({r}, {g}, {b})"
    elif v <= 0.6:
        # 青绿色到绿色 (0.4-0.6)
        t = (v - 0.4) / 0.2
        r = math.floor(50 + t * 70)   # 50→120
        g = math.floor(205 - t * 25)  # 205→180
        b = math.floor(150 - t * 100) # 150→50
        return f"rgb({r}, {g}, {b})"
    elif v <= 0.8:
        # 绿色到黄色 (0.6-0.8)
        t = (v - 0.6) / 0.2
        r = math.floor(120 + t * 135) # 120→255
        g = math.floor(180 + t * 75)  # 180→255
        b = math.floor(50 - t * 50)   # 50→0
        return f"rgb({r}, {g}, {b})"
    else:
        # 橙红到深红 (0.8-1.0) - 增强警示效果
        t = (v - 0.8) / 0.2
        r = math.floor(255 - t * 102) # 255→153 深红
        g = math.floor(85 - t * 58)   # 85→27 深红
        b = math.floor(0 + t * 27)    # 0→27 深红
        return f"rgb({r}, {g}, {b})"

# 测试高风险值
test_values = [0.75, 0.8, 0.85, 0.9, 0.95, 0.99, 1.0]
print("测试颜色映射函数（修改后）：")
print("-" * 50)
for val in test_values:
    color = get_scientific_heat_color(val)
    print(f"值 {val:.2f} -> {color}")

print("\n期望结果：")
print("0.75 -> 黄色区域")
print("0.80 -> 开始橙红 rgb(255, 85, 0)")
print("0.85 -> 深橙红")
print("0.90 -> 偏深红")
print("0.95 -> 接近深红")
print("1.00 -> 深红 rgb(153, 27, 27)")

# 测试API返回的数据
import requests
try:
    response = requests.get("http://localhost:8089/api/data", timeout=2)
    if response.status_code == 200:
        data = response.json()
        matrix = data['data']['heatmap_data']['matrix']
        print(f"\nAPI数据分析：")
        print(f"矩阵大小: {len(matrix)}行 × {len(matrix[0]) if matrix else 0}列")

        # 统计高值数量
        high_values = []
        for row in matrix:
            for val in row:
                if val > 0.8:
                    high_values.append(val)

        print(f"值>0.8的数量: {len(high_values)}")
        if high_values:
            print(f"高值样本: {high_values[:5]}")
            print("这些值应该显示为橙红到深红色")
except:
    print("\n⚠️ 无法连接到服务器")