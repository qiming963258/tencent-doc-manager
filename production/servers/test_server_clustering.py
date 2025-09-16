#!/usr/bin/env python3
"""
测试服务器使用的聚类算法
"""

import requests
import json

def test_server_clustering():
    """测试服务器的热力图聚类功能"""
    try:
        # 请求热力图数据
        response = requests.get('http://localhost:8089/api/heatmap-data', timeout=10)

        if response.status_code == 200:
            data = response.json()

            if 'matrix' in data:
                matrix = data['matrix']
                print(f"✅ 成功获取热力图数据")
                print(f"   矩阵尺寸: {len(matrix)}x{len(matrix[0]) if matrix else 0}")

                # 检查热团聚集程度
                if matrix and len(matrix) > 10:
                    # 计算左上角区域的平均值
                    top_left_sum = 0
                    count = 0
                    for i in range(min(10, len(matrix))):
                        for j in range(min(10, len(matrix[0]))):
                            top_left_sum += matrix[i][j]
                            count += 1
                    top_left_avg = top_left_sum / count if count > 0 else 0

                    # 计算右下角区域的平均值
                    bottom_right_sum = 0
                    count = 0
                    start_row = max(0, len(matrix) - 10)
                    start_col = max(0, len(matrix[0]) - 10)
                    for i in range(start_row, len(matrix)):
                        for j in range(start_col, len(matrix[0])):
                            bottom_right_sum += matrix[i][j]
                            count += 1
                    bottom_right_avg = bottom_right_sum / count if count > 0 else 0

                    print(f"\n📊 聚类效果分析:")
                    print(f"   左上角平均值: {top_left_avg:.3f}")
                    print(f"   右下角平均值: {bottom_right_avg:.3f}")
                    print(f"   对比度: {(top_left_avg - bottom_right_avg):.3f}")

                    if top_left_avg > bottom_right_avg * 1.5:
                        print(f"   ✅ 热团聚集效果良好！")
                    else:
                        print(f"   ⚠️ 热团聚集效果可以改进")

            else:
                print("⚠️ 服务器响应中没有矩阵数据")

        else:
            print(f"❌ 服务器响应错误: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"❌ 无法连接到服务器: {e}")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    print("🧪 测试服务器热力图聚类算法")
    test_server_clustering()