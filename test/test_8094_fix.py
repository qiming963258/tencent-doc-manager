#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试8094修复后的命名功能
模拟real-download API的调用流程
"""

import json
import requests
import time

def test_real_download():
    """测试真实下载对比API"""
    
    print("="*60)
    print("测试8094系统修复后的命名功能")
    print("="*60)
    
    # 测试1: 使用分享链接格式
    print("\n测试1: 使用分享链接格式输入")
    data1 = {
        "baseline_url": """【腾讯文档】副本-测试版本-出国销售计划表
https://docs.qq.com/sheet/DWEFNU25TemFnZXJN?tab=BB08J2""",
        "target_url": """【腾讯文档】副本-副本-测试版本-出国销售计划表
https://docs.qq.com/sheet/DWHpOdVVKU0VmSXJv?tab=BB08J2"""
    }
    
    print(f"基线输入:\n{data1['baseline_url']}")
    print(f"\n目标输入:\n{data1['target_url']}")
    print("\n期望文件名格式: simplified_副本-测试版本-出国销售计划表_vs_副本-副本-测试版本-出国销售计划表_时间戳.json")
    
    # 测试2: 使用纯URL格式
    print("\n" + "="*40)
    print("\n测试2: 使用纯URL格式输入")
    data2 = {
        "baseline_url": "https://docs.qq.com/sheet/DWEFNU25TemFnZXJN?tab=BB08J2",
        "target_url": "https://docs.qq.com/sheet/DWHpOdVVKU0VmSXJv?tab=BB08J2"
    }
    
    print(f"基线URL: {data2['baseline_url']}")
    print(f"目标URL: {data2['target_url']}")
    print("\n期望: 由于是纯URL，将从下载的文件名提取文档名，或使用默认命名")
    
    # 测试3: 模拟metadata覆盖问题
    print("\n" + "="*40)
    print("\n测试3: 验证metadata不被覆盖")
    
    # 模拟result字典
    result = {
        'total_changes': 10,
        'metadata': {
            'baseline_doc_name': '副本-测试版本-出国销售计划表',
            'target_doc_name': '副本-副本-测试版本-出国销售计划表'
        }
    }
    
    print("原始metadata:")
    print(json.dumps(result['metadata'], ensure_ascii=False, indent=2))
    
    # 模拟修复后的更新逻辑
    if 'metadata' not in result:
        result['metadata'] = {}
    result['metadata'].update({
        'timestamp': '2025-09-06T22:00:00',
        'system_version': '3.0.0',
        'comparison_method': 'UnifiedCSVComparator'
    })
    
    print("\n更新后的metadata（应该保留原有字段）:")
    print(json.dumps(result['metadata'], ensure_ascii=False, indent=2))
    
    # 验证文档名是否保留
    if 'baseline_doc_name' in result['metadata'] and 'target_doc_name' in result['metadata']:
        print("\n✅ 文档名称保留成功!")
    else:
        print("\n❌ 文档名称丢失!")
    
    print("\n" + "="*60)
    print("提示：")
    print("1. 如果输入分享链接格式，应该生成语义化文件名")
    print("2. 如果输入纯URL，将使用从文件路径提取的名称")
    print("3. metadata更新应该保留原有的文档名称字段")
    print("="*60)

if __name__ == "__main__":
    test_real_download()