#!/usr/bin/env python3
"""
测试前端是否能正确处理热力图数据格式
验证 heatData.forEach 错误是否已修复
"""

import requests
import json

def test_api_response():
    """测试API响应格式"""

    url = "http://localhost:8089/api/data"

    try:
        response = requests.get(url)
        data = response.json()

        print("🔍 API响应检查")
        print("=" * 50)

        # 检查顶层结构
        if 'data' in data:
            inner_data = data['data']
            print("✅ 包含'data'字段")

            # 检查heatmap_data
            if 'heatmap_data' in inner_data:
                heatmap = inner_data['heatmap_data']

                # 关键检查：heatmap_data应该包含matrix字段
                if isinstance(heatmap, dict) and 'matrix' in heatmap:
                    matrix = heatmap['matrix']
                    print(f"✅ heatmap_data是对象，包含matrix字段")
                    print(f"   matrix类型: {type(matrix).__name__}")
                    print(f"   matrix是数组: {isinstance(matrix, list)}")

                    if isinstance(matrix, list) and len(matrix) > 0:
                        print(f"   矩阵大小: {len(matrix)}×{len(matrix[0]) if matrix[0] else 0}")

                        # 验证是否可以使用forEach
                        print("\n📊 验证forEach兼容性:")
                        print(f"   matrix可以forEach: {isinstance(matrix, list)}")
                        print(f"   第一行可以forEach: {isinstance(matrix[0], list) if matrix else False}")

                        # 测试数据结构
                        all_values_numeric = all(
                            isinstance(val, (int, float))
                            for row in matrix
                            for val in row
                        )
                        print(f"   所有值都是数字: {all_values_numeric}")

                        return True
                    else:
                        print("❌ matrix不是有效的数组")
                        return False

                elif isinstance(heatmap, list):
                    print("⚠️ heatmap_data直接是数组（应该是对象）")
                    print(f"   类型: {type(heatmap).__name__}")
                    return False
                else:
                    print(f"❌ heatmap_data格式错误: {type(heatmap).__name__}")
                    return False
            else:
                print("❌ 缺少'heatmap_data'字段")
                return False
        else:
            print("❌ 缺少'data'字段")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def simulate_frontend_processing():
    """模拟前端的数据处理逻辑"""

    print("\n🖥️ 模拟前端处理")
    print("=" * 50)

    url = "http://localhost:8089/api/data"
    response = requests.get(url)
    apiData = response.json().get('data')

    if not apiData:
        print("❌ 没有API数据")
        return

    # 模拟前端代码的逻辑
    if apiData and 'heatmap_data' in apiData:
        print("📍 执行前端代码逻辑:")
        print("   const rawMatrix = apiData.heatmap_data.matrix || apiData.heatmap_data;")

        heatmap_data = apiData['heatmap_data']

        # 修复后的逻辑
        if isinstance(heatmap_data, dict) and 'matrix' in heatmap_data:
            rawMatrix = heatmap_data['matrix']
            print(f"   ✅ 提取matrix字段: 得到{len(rawMatrix)}行数组")
        else:
            rawMatrix = heatmap_data
            print(f"   ⚠️ 直接使用heatmap_data: {type(heatmap_data).__name__}")

        # 验证是否可以forEach
        if isinstance(rawMatrix, list):
            print(f"   ✅ rawMatrix可以使用forEach")

            # 模拟forEach
            count = 0
            for row in rawMatrix:
                if isinstance(row, list):
                    count += len(row)
            print(f"   ✅ 成功遍历{len(rawMatrix)}行，共{count}个单元格")
        else:
            print(f"   ❌ rawMatrix不能使用forEach: {type(rawMatrix).__name__}")

if __name__ == "__main__":
    print("🧪 热力图数据格式测试")
    print("=" * 50)

    # 测试1: API格式验证
    if test_api_response():
        print("\n✅ API格式测试通过！")

        # 测试2: 模拟前端处理
        simulate_frontend_processing()

        print("\n🎉 修复验证完成！")
        print("heatData.forEach错误应该已经解决")
    else:
        print("\n❌ API格式仍有问题，需要进一步修复")