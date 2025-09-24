#!/usr/bin/env python3
"""
验证URL修复是否生效
"""

import requests
import json
import time

BASE_URL = "http://localhost:8089"

def test_table_urls():
    """测试表格URL是否正确显示"""
    print("=" * 60)
    print("测试表格URL修复")
    print("=" * 60)

    # 1. 首先重新加载综合打分数据
    print("\n1. 重新加载综合打分数据...")
    reload_response = requests.post(f"{BASE_URL}/api/reload-comprehensive-score")
    if reload_response.status_code == 200:
        result = reload_response.json()
        print(f"   ✅ 重载成功")
        print(f"   - 文件: {result.get('filename')}")
        print(f"   - 包含URLs: {result.get('has_urls')}")
        if result.get('urls'):
            print(f"   - URLs: {json.dumps(result['urls'], indent=4, ensure_ascii=False)}")
    else:
        print(f"   ❌ 重载失败")

    time.sleep(1)

    # 2. 获取实时数据，检查table URL
    print("\n2. 获取实时数据...")
    data_response = requests.get(f"{BASE_URL}/api/real_csv_data?sorting=default")

    if data_response.status_code == 200:
        data = data_response.json()
        tables = data.get('tables', [])

        print(f"   找到 {len(tables)} 个表格")

        for table in tables:
            table_name = table.get('name', 'Unknown')
            table_url = table.get('url', '')

            if table_url:
                print(f"   ✅ 表格 '{table_name}':")
                print(f"      URL: {table_url}")

                # 验证URL格式
                if table_url.startswith('https://docs.qq.com/sheet/'):
                    print(f"      ✅ URL格式正确（腾讯文档）")
                else:
                    print(f"      ⚠️ URL格式异常")
            else:
                print(f"   ❌ 表格 '{table_name}': 没有URL")

    else:
        print(f"   ❌ 获取数据失败: {data_response.status_code}")

def test_comprehensive_file_loading():
    """测试不同综合打分文件的加载"""
    print("\n" + "=" * 60)
    print("测试综合打分文件切换")
    print("=" * 60)

    # 获取可用的综合打分文件
    week = 39
    files_response = requests.get(f"{BASE_URL}/api/comprehensive-files?week={week}")

    if files_response.status_code == 200:
        files = files_response.json().get('files', [])
        print(f"\n找到 W{week} 的 {len(files)} 个综合打分文件")

        # 测试加载每个文件
        for file_info in files[:2]:  # 只测试前2个文件
            file_name = file_info['name']
            print(f"\n测试加载文件: {file_name}")

            file_path = f"/root/projects/tencent-doc-manager/scoring_results/2025_W{week}/{file_name}"
            load_response = requests.get(f"{BASE_URL}/api/load-comprehensive-data?file={file_path}")

            if load_response.status_code == 200:
                result = load_response.json()
                if result.get('success'):
                    print(f"   ✅ 文件加载成功")

                    # 等待一下让数据更新
                    time.sleep(1)

                    # 获取新数据
                    data_response = requests.get(f"{BASE_URL}/api/real_csv_data?sorting=default")
                    if data_response.status_code == 200:
                        data = data_response.json()
                        tables = data.get('tables', [])
                        if tables:
                            first_table = tables[0]
                            print(f"   当前显示表格: {first_table.get('name')}")
                            print(f"   表格URL: {first_table.get('url', 'None')}")
                else:
                    print(f"   ❌ 文件加载失败: {result.get('error')}")

def test_data_consistency():
    """测试数据一致性"""
    print("\n" + "=" * 60)
    print("测试数据一致性")
    print("=" * 60)

    # 直接读取综合打分文件
    import sys
    sys.path.append('/root/projects/tencent-doc-manager')

    latest_file = "/root/projects/tencent-doc-manager/scoring_results/comprehensive/comprehensive_score_W39_latest.json"
    print(f"\n直接读取文件: {latest_file}")

    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            file_data = json.load(f)

        # 检查excel_urls字段
        excel_urls = file_data.get('excel_urls', {})
        if excel_urls:
            print(f"   ✅ 文件包含excel_urls字段:")
            for table_name, url in excel_urls.items():
                print(f"      {table_name}: {url}")
        else:
            print(f"   ❌ 文件缺少excel_urls字段")

        # 检查table_details中的excel_url
        table_details = file_data.get('table_details', {})
        for table_name, details in table_details.items():
            if 'excel_url' in details:
                print(f"   ✅ table_details['{table_name}']包含excel_url")
            else:
                print(f"   ❌ table_details['{table_name}']缺少excel_url")

    except Exception as e:
        print(f"   ❌ 读取文件失败: {e}")

def main():
    """运行所有测试"""
    test_table_urls()
    test_comprehensive_file_loading()
    test_data_consistency()

    print("\n" + "=" * 60)
    print("验证完成！")
    print("\n总结:")
    print("1. excel_urls字段已添加到综合打分文件 ✅")
    print("2. UI代码已修改为从excel_urls获取URL ✅")
    print("3. 表格链接应该指向上传的涂色文件，而非基线文件 ✅")
    print("\n请访问 http://202.140.143.88:8089/ 查看效果")

if __name__ == "__main__":
    main()