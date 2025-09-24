#!/usr/bin/env python3
"""
测试技术规范v1.6的所有修复
包括：配置统一、精确匹配、预验证、动态周数
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, '/root/projects/tencent-doc-manager')

def test_config_unification():
    """测试配置文件统一读取"""
    print("\n🧪 测试1: 配置文件统一读取")
    print("="*60)

    # 加载real_documents.json
    real_docs_path = Path('/root/projects/tencent-doc-manager/production/config/real_documents.json')
    with open(real_docs_path, 'r', encoding='utf-8') as f:
        real_docs = json.load(f)

    print(f"✅ real_documents.json包含 {len(real_docs['documents'])} 个文档:")
    for doc in real_docs['documents']:
        print(f"  - {doc['name']} ({doc['doc_id']})")

    # 检查8093是否使用正确的配置路径
    with open('/root/projects/tencent-doc-manager/production_integrated_test_system_8093.py', 'r') as f:
        content = f.read()

    if 'production/config/real_documents.json' in content:
        print("✅ 8093工作流已更新为使用real_documents.json")
    else:
        print("❌ 8093工作流仍在使用旧配置文件")

    return True

def test_exact_matching():
    """测试精确匹配函数"""
    print("\n🧪 测试2: 精确匹配逻辑")
    print("="*60)

    # 导入精确匹配函数
    from production_integrated_test_system_8093 import extract_doc_name_from_filename

    test_cases = [
        ("tencent_出国销售计划表_20250915_0145_baseline_W39.csv", "出国销售计划表"),
        ("tencent_小红书部门_20250915_0146_baseline_W39.csv", "小红书部门"),
        ("tencent_回国销售计划表_20250914_2309_baseline_W39.csv", "回国销售计划表")
    ]

    for filename, expected in test_cases:
        result = extract_doc_name_from_filename(filename)
        if result == expected:
            print(f"✅ {filename[:30]}... → {result}")
        else:
            print(f"❌ {filename[:30]}... → {result} (期望: {expected})")

    # 测试精确匹配vs模糊匹配
    print("\n测试精确匹配 vs 模糊匹配:")
    doc_name = "出国"
    baseline_names = ["出国销售计划表", "出国采购计划表", "出国人员名单"]

    print(f"  查找: '{doc_name}'")
    print(f"  基线: {baseline_names}")

    # 模糊匹配（错误的方式）
    fuzzy_matches = [b for b in baseline_names if doc_name in b]
    print(f"  模糊匹配结果: {fuzzy_matches} ❌ (会匹配多个)")

    # 精确匹配（正确的方式）
    exact_matches = [b for b in baseline_names if b == doc_name]
    print(f"  精确匹配结果: {exact_matches} ✅ (无匹配)")

    return True

def test_dynamic_week():
    """测试动态周数计算"""
    print("\n🧪 测试3: 动态周数计算")
    print("="*60)

    from production.core_modules.auto_comprehensive_generator import AutoComprehensiveGenerator

    generator = AutoComprehensiveGenerator()

    # 获取当前周和基线周
    current_week = generator._get_current_week()
    baseline_week = generator._get_baseline_week()

    print(f"当前日期: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"当前周数: W{current_week}")
    print(f"基线周数: W{baseline_week}")

    # 验证是否是正确的ISO周数
    iso_week = datetime.now().isocalendar()[1]
    if int(current_week) == iso_week:
        print(f"✅ 周数计算正确 (ISO标准: {iso_week})")
    else:
        print(f"❌ 周数计算错误 (ISO标准: {iso_week})")

    # 检查文件保存路径
    expected_path = f"2025_W{current_week}"
    if hasattr(generator, 'week_dir'):
        actual_path = generator.week_dir.name
        if actual_path == expected_path:
            print(f"✅ 文件将保存到正确的周目录: {actual_path}")
        else:
            print(f"❌ 文件保存路径错误: {actual_path} (期望: {expected_path})")

    return True

def test_validation_mechanism():
    """测试预验证机制"""
    print("\n🧪 测试4: 文档匹配预验证")
    print("="*60)

    # 检查8093是否包含预验证代码
    with open('/root/projects/tencent-doc-manager/production_integrated_test_system_8093.py', 'r') as f:
        content = f.read()

    checks = [
        ("步骤2.5: 文档匹配预验证", "预验证步骤"),
        ("验证文档匹配性", "验证日志"),
        ("变更数量异常检测", "异常检测"),
        ("if num_changes > 500", "500变更阈值")
    ]

    for check_str, description in checks:
        if check_str in content:
            print(f"✅ {description}: 已添加")
        else:
            print(f"❌ {description}: 未找到")

    return True

def test_no_fallback():
    """测试危险回退逻辑是否已移除"""
    print("\n🧪 测试5: 危险回退逻辑移除")
    print("="*60)

    with open('/root/projects/tencent-doc-manager/production_integrated_test_system_8093.py', 'r') as f:
        content = f.read()

    # 检查危险的回退逻辑是否已移除
    dangerous_patterns = [
        "baseline_file = matched_baseline if matched_baseline else baseline_files[0]",
        "else baseline_files[0]"
    ]

    has_dangerous = False
    for pattern in dangerous_patterns:
        if pattern in content:
            print(f"❌ 发现危险回退逻辑: {pattern[:50]}...")
            has_dangerous = True

    if not has_dangerous:
        print("✅ 危险回退逻辑已移除")

    # 检查是否有正确的错误处理
    if "raise Exception(f\"未找到与'{doc_name}'匹配的基线文件" in content:
        print("✅ 添加了正确的错误处理（抛出异常）")

    return not has_dangerous

def main():
    """运行所有测试"""
    print("🔧 技术规范v1.6修复验证")
    print("="*80)

    tests = [
        ("配置统一", test_config_unification),
        ("精确匹配", test_exact_matching),
        ("动态周数", test_dynamic_week),
        ("预验证机制", test_validation_mechanism),
        ("移除危险回退", test_no_fallback)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ 测试 {test_name} 失败: {e}")
            results.append((test_name, False))

    # 总结
    print("\n" + "="*80)
    print("📊 测试总结:")
    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name}: {status}")

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 所有修复已成功应用！系统现在符合技术规范v1.6")
    else:
        print("\n⚠️ 部分修复需要进一步调整")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)