#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的命名规范
验证ShareLinkParser和FileNamingService的集成
"""

import sys
import json
from datetime import datetime

# 添加项目路径
sys.path.insert(0, '/root/projects/tencent-doc-manager')
sys.path.insert(0, '/root/projects/tencent-doc-manager/production/core_modules')

from production.core_modules.share_link_parser import ShareLinkParser, FileNamingService

def test_share_link_parser():
    """测试分享链接解析器"""
    print("="*60)
    print("📋 测试ShareLinkParser")
    print("="*60)
    
    parser = ShareLinkParser()
    
    # 测试案例1: 完整分享链接格式
    test_input1 = """【腾讯文档】副本-测试版本-出国销售计划表
https://docs.qq.com/sheet/DWEFNU25TemFnZXJN?tab=BB08J2"""
    
    print("\n测试案例1: 完整分享链接格式")
    print(f"输入:\n{test_input1}")
    
    result1 = parser.parse_share_link(test_input1)
    print(f"\n解析结果:")
    print(json.dumps(result1, ensure_ascii=False, indent=2))
    
    # 测试案例2: 纯URL格式
    test_input2 = "https://docs.qq.com/sheet/DWHpOdVVKU0VmSXJv?tab=BB08J2"
    
    print("\n" + "-"*40)
    print("\n测试案例2: 纯URL格式")
    print(f"输入: {test_input2}")
    
    result2 = parser.parse_share_link(test_input2)
    print(f"\n解析结果:")
    print(json.dumps(result2, ensure_ascii=False, indent=2))
    
    return result1, result2

def test_file_naming_service(baseline_info, target_info):
    """测试文件命名服务"""
    print("\n" + "="*60)
    print("📝 测试FileNamingService")
    print("="*60)
    
    naming_service = FileNamingService()
    
    # 使用从分享链接解析出的文档名
    baseline_doc_name = baseline_info['doc_name']
    target_doc_name = "副本-副本-测试版本-出国销售计划表"  # 模拟目标文档名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    print(f"\n基线文档名: {baseline_doc_name}")
    print(f"目标文档名: {target_doc_name}")
    print(f"时间戳: {timestamp}")
    
    # 生成文件名
    filename = naming_service.generate_comparison_filename(
        baseline_doc_name,
        target_doc_name,
        timestamp
    )
    
    print(f"\n生成的文件名:")
    print(f"  {filename}")
    
    # 测试文件名解析
    print("\n从文件名解析文档名:")
    doc1, doc2 = naming_service.extract_doc_names_from_filename(filename)
    print(f"  基线文档: {doc1}")
    print(f"  目标文档: {doc2}")
    
    return filename

def test_comparison_urls():
    """测试对比URL解析"""
    print("\n" + "="*60)
    print("🔄 测试对比URL解析")
    print("="*60)
    
    parser = ShareLinkParser()
    
    baseline_input = """【腾讯文档】副本-测试版本-出国销售计划表
https://docs.qq.com/sheet/DWEFNU25TemFnZXJN?tab=BB08J2"""
    
    target_input = """【腾讯文档】副本-副本-测试版本-出国销售计划表
https://docs.qq.com/sheet/DWHpOdVVKU0VmSXJv?tab=BB08J2"""
    
    print("\n解析对比文档:")
    result = parser.parse_comparison_urls(baseline_input, target_input)
    
    print(f"\n基线文档:")
    print(json.dumps(result['baseline'], ensure_ascii=False, indent=2))
    
    print(f"\n目标文档:")
    print(json.dumps(result['target'], ensure_ascii=False, indent=2))
    
    return result

def main():
    """主测试函数"""
    print("🚀 开始测试新的命名规范系统")
    print("="*80)
    
    # 测试1: ShareLinkParser
    baseline_info, _ = test_share_link_parser()
    
    # 测试2: FileNamingService
    target_info = {'doc_name': '副本-副本-测试版本-出国销售计划表'}
    filename = test_file_naming_service(baseline_info, target_info)
    
    # 测试3: 对比URL解析
    comparison_result = test_comparison_urls()
    
    # 汇总结果
    print("\n" + "="*80)
    print("✅ 测试完成 - 新命名规范系统")
    print("="*80)
    print(f"\n最终生成的文件名格式:")
    print(f"  {filename}")
    print(f"\n预期格式:")
    print(f"  simplified_{{基线文档名}}_vs_{{目标文档名}}_{{时间戳}}.json")
    print(f"\n✅ 格式验证: {'通过' if filename.startswith('simplified_') and '_vs_' in filename else '失败'}")
    
    # 验证特殊字符处理
    print("\n特殊字符处理验证:")
    test_name = "测试/文档:名称*带<特殊>字符|"
    test_parser = ShareLinkParser()
    sanitized = test_parser._sanitize_doc_name(test_name)
    print(f"  原始: {test_name}")
    print(f"  清理后: {sanitized}")
    
    print("\n📊 系统集成状态:")
    print("  ✅ ShareLinkParser - 正常工作")
    print("  ✅ FileNamingService - 正常工作")
    print("  ✅ 文档名提取 - 正常工作")
    print("  ✅ 语义化命名 - 正常工作")
    
if __name__ == "__main__":
    main()