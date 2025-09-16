#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试8094系统的命名功能
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, '/root/projects/tencent-doc-manager')
sys.path.insert(0, '/root/projects/tencent-doc-manager/production/core_modules')

print("="*60)
print("测试8094命名系统")
print("="*60)

# 测试1: ShareLinkParser是否能导入
print("\n1. 测试ShareLinkParser导入:")
try:
    from production.core_modules.share_link_parser import ShareLinkParser, FileNamingService
    print("✅ ShareLinkParser导入成功")
    HAS_SHARE_PARSER = True
except ImportError as e:
    print(f"❌ ShareLinkParser导入失败: {e}")
    HAS_SHARE_PARSER = False

# 测试2: 如果导入成功，测试解析功能
if HAS_SHARE_PARSER:
    print("\n2. 测试URL解析:")
    parser = ShareLinkParser()
    
    # 测试纯URL
    test_url = "https://docs.qq.com/sheet/DWEFNU25TemFnZXJN?tab=BB08J2"
    print(f"输入URL: {test_url}")
    try:
        result = parser.parse_share_link(test_url)
        print(f"解析结果: {result}")
    except Exception as e:
        print(f"解析失败: {e}")
    
    # 测试分享链接格式
    test_share = """【腾讯文档】副本-测试版本-出国销售计划表
https://docs.qq.com/sheet/DWEFNU25TemFnZXJN?tab=BB08J2"""
    print(f"\n输入分享链接:\n{test_share}")
    try:
        result = parser.parse_share_link(test_share)
        print(f"解析结果: {result}")
    except Exception as e:
        print(f"解析失败: {e}")

# 测试3: 测试save_result的逻辑
print("\n3. 测试save_result逻辑:")
print(f"HAS_SHARE_PARSER = {HAS_SHARE_PARSER}")

# 模拟metadata
metadata = {
    'baseline_doc_name': '副本-测试版本-出国销售计划表',
    'target_doc_name': '副本-副本-测试版本-出国销售计划表'
}

result = {'metadata': metadata}

# 模拟save_result的逻辑
baseline_doc_name = result['metadata'].get('baseline_doc_name')
target_doc_name = result['metadata'].get('target_doc_name')

print(f"baseline_doc_name = {baseline_doc_name}")
print(f"target_doc_name = {target_doc_name}")

if HAS_SHARE_PARSER and baseline_doc_name and target_doc_name:
    print("条件满足，将使用语义化命名")
    naming_service = FileNamingService()
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = naming_service.generate_comparison_filename(
        baseline_doc_name,
        target_doc_name,
        timestamp
    )
    print(f"生成的文件名: {filename}")
else:
    print("条件不满足，将使用默认命名")
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"simplified_comparison_{timestamp}.json"
    print(f"默认文件名: {filename}")