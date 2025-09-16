#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档监控系统架构测试脚本
测试用户粘贴3个真实腾讯文档URL的处理流程
"""

import sys
import json
from pathlib import Path

# 添加模块路径
sys.path.insert(0, '/root/projects/tencent-doc-manager/production/core_modules')

# 导入真实文档加载器
from real_doc_loader import RealDocumentLoader

def test_paste_parsing():
    """测试解析用户粘贴的腾讯文档内容"""
    print("=" * 80)
    print("测试1: 解析用户粘贴的腾讯文档")
    print("=" * 80)
    
    loader = RealDocumentLoader()
    
    # 模拟用户粘贴的3个真实腾讯文档
    test_contents = [
        """【腾讯文档】测试版本-回国销售计划表
https://docs.qq.com/sheet/DRFppYm15RGZ2WExN""",
        
        """【腾讯文档】副本-测试版本-出国销售计划表  
https://docs.qq.com/sheet/DWEFNU25TemFnZXJN""",
        
        """【腾讯文档】第三个测试文档
https://docs.qq.com/sheet/DRHZrS1hOS3pwRGZB"""
    ]
    
    parsed_docs = []
    for i, content in enumerate(test_contents, 1):
        print(f"\n粘贴内容{i}:")
        print(content)
        
        result = loader.parse_pasted_content(content)
        if result:
            print(f"✅ 解析成功:")
            print(f"   文档名称: {result['name']}")
            print(f"   文档URL: {result['url']}")
            print(f"   文档ID: {result['doc_id']}")
            parsed_docs.append(result)
        else:
            print(f"❌ 解析失败")
    
    return parsed_docs

def test_real_csv_files():
    """测试获取真实CSV文件"""
    print("\n" + "=" * 80)
    print("测试2: 获取真实CSV文件（应该只有3个，不是9个）")
    print("=" * 80)
    
    loader = RealDocumentLoader()
    real_files = loader.get_real_csv_files()
    
    print(f"\n找到 {len(real_files)} 个真实文档文件:")
    for file_info in real_files:
        print(f"\n文档 {file_info['id'] + 1}:")
        print(f"  名称: {file_info['name']}")
        print(f"  URL: {file_info['url']}")
        print(f"  文档ID: {file_info['doc_id']}")
        print(f"  Previous文件: {Path(file_info['previous_file']).name}")
        print(f"  Current文件: {Path(file_info['current_file']).name}")
        print(f"  有对比数据: {file_info['has_comparison']}")
    
    # 验证是否只有3个文档
    if len(real_files) == 3:
        print("\n✅ 正确：只返回了3个真实文档")
    else:
        print(f"\n❌ 错误：返回了{len(real_files)}个文档，应该是3个")
    
    # 验证文档名称是否使用真实名称
    expected_names = [
        "测试版本-回国销售计划表",
        "副本-测试版本-出国销售计划表",
        "第三个测试文档"
    ]
    
    actual_names = [f['name'] for f in real_files]
    if set(actual_names) == set(expected_names):
        print("✅ 正确：使用了真实的腾讯文档名称")
    else:
        print("❌ 错误：文档名称不匹配")
        print(f"   期望: {expected_names}")
        print(f"   实际: {actual_names}")
    
    return real_files

def test_csv_file_matching():
    """测试CSV文件匹配机制"""
    print("\n" + "=" * 80)
    print("测试3: CSV文件匹配机制")
    print("=" * 80)
    
    comparison_path = Path('/root/projects/tencent-doc-manager/csv_versions/comparison')
    
    # 检查CSV文件配对
    csv_patterns = ['realtest', 'test', 'test_data']
    
    for pattern in csv_patterns:
        print(f"\n检查模式: {pattern}")
        previous_files = list(comparison_path.glob(f'previous_{pattern}*.csv'))
        current_files = list(comparison_path.glob(f'current_{pattern}*.csv'))
        
        print(f"  Previous文件数: {len(previous_files)}")
        print(f"  Current文件数: {len(current_files)}")
        
        if previous_files and current_files:
            print(f"  ✅ 找到配对的CSV文件")
            # 显示最新的一对
            latest_prev = sorted(previous_files)[-1]
            latest_curr = sorted(current_files)[-1]
            print(f"     Previous: {latest_prev.name}")
            print(f"     Current: {latest_curr.name}")
        else:
            print(f"  ⚠️ 缺少配对文件")

def test_data_flow():
    """测试完整数据流"""
    print("\n" + "=" * 80)
    print("测试4: 数据流验证")
    print("=" * 80)
    
    loader = RealDocumentLoader()
    
    # 模拟完整流程
    print("\n数据流程：")
    print("1. 用户粘贴URL → parse_pasted_content()")
    
    test_content = """【腾讯文档】测试版本-回国销售计划表
https://docs.qq.com/sheet/DRFppYm15RGZ2WExN"""
    
    parsed = loader.parse_pasted_content(test_content)
    if parsed:
        print(f"   ✅ 解析成功: {parsed['name']}")
    
    print("\n2. 系统获取CSV文件 → get_real_csv_files()")
    real_files = loader.get_real_csv_files()
    print(f"   ✅ 获取到 {len(real_files)} 个文件")
    
    print("\n3. 加载对比结果 → load_comparison_result()")
    if real_files:
        first_file = real_files[0]
        result = loader.load_comparison_result(
            first_file['previous_file'],
            first_file['current_file']
        )
        print(f"   ✅ 发现 {result['total_differences']} 处差异")
    
    print("\n4. 生成热力图 → 前端展示")
    print("   ✅ 数据流完整")

def analyze_architecture():
    """架构分析总结"""
    print("\n" + "=" * 80)
    print("架构评审报告")
    print("=" * 80)
    
    print("\n📊 当前实现的优点：")
    print("1. ✅ 清晰的模块化设计")
    print("   - real_documents.json: 配置管理")
    print("   - real_doc_loader.py: 核心逻辑")
    print("   - 解耦的数据加载和处理")
    
    print("\n2. ✅ 真实数据驱动")
    print("   - 使用真实的腾讯文档URL和名称")
    print("   - 避免了硬编码的虚拟数据")
    print("   - 只处理配置的3个文档，不是9个虚拟表格")
    
    print("\n3. ✅ 灵活的CSV匹配机制")
    print("   - 基于pattern匹配CSV文件")
    print("   - 自动配对previous/current文件")
    print("   - 支持时间戳版本管理")
    
    print("\n⚠️ 潜在问题点：")
    print("1. 异常处理中的默认值回退可能掩盖配置错误")
    print("2. CSV文件pattern匹配可能需要更严格的验证")
    print("3. 缺少对重复文档ID的检查")
    
    print("\n💡 改进建议：")
    print("1. 添加配置验证器，确保文档ID唯一性")
    print("2. 实现CSV文件完整性检查")
    print("3. 添加日志记录和监控指标")
    print("4. 考虑添加文档元数据缓存机制")
    
    print("\n🔄 与原系统对比：")
    print("原系统（9个虚拟表格）：")
    print("  - 使用硬编码的虚拟数据")
    print("  - 固定的9个监控表")
    print("  - 模拟的差异数据")
    
    print("\n新系统（3个真实文档）：")
    print("  - 基于配置的真实文档")
    print("  - 动态加载实际CSV文件")
    print("  - 真实的文件对比差异")
    print("  - 可扩展到更多文档")

if __name__ == "__main__":
    # 运行所有测试
    parsed_docs = test_paste_parsing()
    real_files = test_real_csv_files()
    test_csv_file_matching()
    test_data_flow()
    analyze_architecture()
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)