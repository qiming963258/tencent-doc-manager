#!/usr/bin/env python3
"""
测试excel_url为什么没有被添加到综合打分文件
"""

import json
import sys
sys.path.append('/root/projects/tencent-doc-manager')

from production.core_modules.auto_comprehensive_generator import AutoComprehensiveGenerator

def test_excel_url_generation():
    """测试excel_url是否正确添加到综合打分"""

    print("=" * 60)
    print("测试Excel URL添加功能")
    print("=" * 60)

    # 创建生成器实例
    generator = AutoComprehensiveGenerator()

    # 测试用的URL
    test_url = "https://docs.qq.com/sheet/DWE1yRmp0WVBGb29p"
    print(f"\n测试URL: {test_url}")

    try:
        # 调用生成函数
        print("\n调用 generate_from_latest_results...")
        result_file = generator.generate_from_latest_results(excel_url=test_url)
        print(f"✅ 生成文件: {result_file}")

        # 读取生成的文件
        with open(result_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 检查excel_urls字段
        print("\n检查生成的文件内容:")
        if 'excel_urls' in data:
            print(f"✅ 找到excel_urls字段: {data['excel_urls']}")
        else:
            print("❌ 未找到excel_urls字段")
            print("文件包含的顶级字段:", list(data.keys()))

        # 检查table_details中的excel_url
        if 'table_details' in data:
            for table_name, details in data['table_details'].items():
                if 'excel_url' in details:
                    print(f"✅ 表格'{table_name}'包含excel_url: {details['excel_url']}")
                else:
                    print(f"❌ 表格'{table_name}'缺少excel_url字段")
                    print(f"   表格详情字段: {list(details.keys())}")

        # 显示metadata
        print(f"\n文件metadata: {data.get('metadata', {})}")

    except Exception as e:
        print(f"❌ 生成失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_excel_url_generation()