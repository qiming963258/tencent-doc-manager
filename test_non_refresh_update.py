#!/usr/bin/env python3
"""
测试8089热力图UI的无刷新更新功能
"""
import requests
import json
import time

BASE_URL = "http://localhost:8089"

def test_reload_comprehensive_score():
    """测试重新加载综合打分数据的API"""
    print("\n=== 测试重新加载综合打分数据 ===")

    # 调用重新加载API
    response = requests.post(f"{BASE_URL}/api/reload-comprehensive-score")

    if response.status_code == 200:
        result = response.json()
        print(f"✅ 成功加载最新综合打分文件")
        print(f"   文件名: {result.get('filename', 'N/A')}")
        print(f"   表格数: {result.get('table_count', 0)}")
        print(f"   修改总数: {result.get('total_modifications', 0)}")
        print(f"   消息: {result.get('message', '')}")
        return True
    else:
        print(f"❌ 加载失败: {response.status_code}")
        try:
            error = response.json()
            print(f"   错误: {error.get('error', 'Unknown error')}")
        except:
            print(f"   响应: {response.text[:200]}")
        return False

def test_load_specific_comprehensive_file():
    """测试加载特定的综合打分文件"""
    print("\n=== 测试加载特定综合打分文件 ===")

    # 首先获取可用的综合打分文件列表
    week = 39  # 测试W39
    response = requests.get(f"{BASE_URL}/api/comprehensive-files?week={week}")

    if response.status_code != 200:
        print(f"❌ 无法获取W{week}的文件列表")
        return False

    files = response.json().get('files', [])
    if not files:
        print(f"❌ W{week}没有可用的综合打分文件")
        return False

    # 选择第一个文件进行测试
    test_file = files[0]
    print(f"   测试文件: {test_file['name']}")

    # 加载特定文件
    file_path = f"/root/projects/tencent-doc-manager/scoring_results/2025_W{week}/{test_file['name']}"
    response = requests.get(f"{BASE_URL}/api/load-comprehensive-data?file={file_path}")

    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print(f"✅ 成功加载文件: {test_file['name']}")
            print(f"   消息: {result.get('message', '')}")
            return True
        else:
            print(f"❌ 加载失败: {result.get('error', 'Unknown error')}")
            return False
    else:
        print(f"❌ API调用失败: {response.status_code}")
        return False

def test_data_source_status():
    """测试数据源状态"""
    print("\n=== 测试数据源状态 ===")

    response = requests.get(f"{BASE_URL}/api/get_data_source")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 当前数据源: {result.get('data_source', 'unknown')}")
        print(f"   消息: {result.get('message', '')}")
        return result.get('data_source') == 'comprehensive'
    else:
        print(f"❌ 无法获取数据源状态")
        return False

def test_comprehensive_data_api():
    """测试综合打分数据API"""
    print("\n=== 测试综合打分数据API ===")

    # 测试不同的排序模式
    sorting_modes = ['default', 'intelligent']

    for mode in sorting_modes:
        response = requests.get(f"{BASE_URL}/api/real_csv_data?sorting={mode}")
        if response.status_code == 200:
            data = response.json()
            table_count = len(data.get('tables', []))
            print(f"✅ 排序模式 '{mode}': 获取到 {table_count} 个表格数据")

            # 检查数据结构
            if table_count > 0:
                first_table = data['tables'][0]
                has_modifications = 'column_modifications' in first_table
                has_row_data = 'row_level_data' in first_table
                print(f"   数据结构检查:")
                print(f"   - column_modifications: {'✅' if has_modifications else '❌'}")
                print(f"   - row_level_data: {'✅' if has_row_data else '❌'}")
        else:
            print(f"❌ 排序模式 '{mode}' 失败: {response.status_code}")

def main():
    """运行所有测试"""
    print("=" * 60)
    print("8089热力图UI无刷新更新功能测试")
    print("=" * 60)

    # 运行测试
    test_data_source_status()
    test_reload_comprehensive_score()
    test_load_specific_comprehensive_file()
    test_comprehensive_data_api()

    print("\n" + "=" * 60)
    print("测试完成！")
    print("\n说明:")
    print("1. '立即显示最新数据'按钮会调用 /api/reload-comprehensive-score")
    print("2. '展示'按钮会调用 /api/load-comprehensive-data 并自动更新UI")
    print("3. 两个按钮都不再需要手动刷新页面（F5）")
    print("4. 如果无刷新更新失败，会自动降级到提示手动刷新")

if __name__ == "__main__":
    main()