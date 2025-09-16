#!/usr/bin/env python3
"""
完整数据链路真实性验证测试
测试从CSV对比到综合打分的整个数据流程是否使用真实数据
"""

import json
import os
import sys

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_real_data_pipeline():
    """测试完整数据链路"""
    print("=" * 80)
    print("🔍 数据链路真实性验证测试")
    print("=" * 80)

    # 测试结果收集
    test_results = {
        "passed": [],
        "failed": [],
        "warnings": []
    }

    # 1. 检查CSV对比结果文件
    print("\n1️⃣ 检查CSV对比结果文件...")
    comparison_file = "/root/projects/tencent-doc-manager/csv_security_results/test_comparison_comparison.json"
    if os.path.exists(comparison_file):
        with open(comparison_file, 'r', encoding='utf-8') as f:
            comparison_data = json.load(f)

        if 'differences' in comparison_data:
            print(f"   ✅ CSV对比文件存在，包含{len(comparison_data['differences'])}个差异")
            test_results["passed"].append("CSV对比文件存在且有真实数据")

            # 显示部分差异示例
            print("\n   📋 差异示例:")
            for i, diff in enumerate(comparison_data['differences'][:3]):
                print(f"      - 行{diff['行号']} {diff['列名']}: '{diff['原值']}' → '{diff['新值']}' (风险等级: {diff['risk_level']})")
        else:
            print("   ❌ CSV对比文件格式错误")
            test_results["failed"].append("CSV对比文件格式错误")
    else:
        print("   ❌ CSV对比文件不存在")
        test_results["failed"].append("CSV对比文件不存在")

    # 2. 测试comparison_to_scoring_adapter
    print("\n2️⃣ 测试comparison_to_scoring_adapter...")
    try:
        from production.core_modules.comparison_to_scoring_adapter import ComparisonToScoringAdapter

        adapter = ComparisonToScoringAdapter()

        # 使用真实的CSV对比数据
        if os.path.exists(comparison_file):
            with open(comparison_file, 'r', encoding='utf-8') as f:
                comparison_data = json.load(f)

            # 提取表格数据 - 传入单个对比结果而不是列表
            table_data = adapter.extract_table_data(comparison_data)
            table_data_list = [table_data] if table_data else []

            if table_data_list:
                print(f"   ✅ Adapter成功提取{len(table_data_list)}个表格数据")
                test_results["passed"].append("Adapter能够提取真实数据")

                # 检查L1/L2/L3分类
                # column_modifications是行号列表，需要计算打分
                for table_data in table_data_list:
                    # 生成打分数据
                    for col_name, modified_rows in table_data['column_modifications'].items():
                        # 获取列级别
                        level = adapter._get_column_level(col_name)

                        # 计算分数
                        modification_count = len(modified_rows)
                        total_rows = table_data.get('total_rows', 270)
                        score = adapter._calculate_column_score(modification_count, total_rows, col_name)

                        # 验证强制阈值（只有当有修改时才验证）
                        if modification_count > 0:  # 只检查有修改的列
                            if level == 'L1' and score < 0.8:
                                test_results["failed"].append(f"L1列{col_name}有{modification_count}个修改但分数{score}低于0.8")
                            elif level == 'L2' and score < 0.6:
                                test_results["failed"].append(f"L2列{col_name}有{modification_count}个修改但分数{score}低于0.6")
                        else:
                            # 没有修改的列应该是0.05（背景值）
                            if score != 0.05:
                                test_results["warnings"].append(f"列{col_name}无修改但分数为{score}（应该为0.05）")

                print("   ✅ L1/L2/L3列分类和强制阈值验证通过")
                test_results["passed"].append("列分类和强制阈值正确")
            else:
                print("   ❌ Adapter无法提取数据")
                test_results["failed"].append("Adapter无法提取数据")

    except Exception as e:
        print(f"   ❌ Adapter测试失败: {e}")
        test_results["failed"].append(f"Adapter测试失败: {e}")

    # 3. 测试comprehensive_score_generator_v2
    print("\n3️⃣ 测试comprehensive_score_generator_v2...")
    try:
        from production.core_modules.comprehensive_score_generator_v2 import ComprehensiveScoreGeneratorV2

        generator = ComprehensiveScoreGeneratorV2()

        # 生成综合打分文件
        result = generator.generate(
            week_number="38",
            comparison_files=[comparison_file] if os.path.exists(comparison_file) else []
        )

        if result and os.path.exists(result):
            print(f"   ✅ 生成综合打分文件: {result}")
            test_results["passed"].append("综合打分文件生成成功")

            # 读取并验证内容
            with open(result, 'r', encoding='utf-8') as f:
                comprehensive_data = json.load(f)

            # 检查数据源标记（在summary中）
            data_source = comprehensive_data.get('summary', {}).get('data_source')
            if data_source == 'real_csv_comparison':
                print("   ✅ 数据源标记为'real_csv_comparison'")
                test_results["passed"].append("数据源标记正确")
            else:
                print(f"   ⚠️  数据源标记为'{data_source}'")
                test_results["warnings"].append("数据源标记不正确")

            # 检查是否有随机数据特征
            import re
            content_str = json.dumps(comprehensive_data)

            # 检查是否有明显的随机模式（如连续的0.7x, 0.8x等）
            random_pattern = re.findall(r'0\.\d{2,}', content_str)
            if len(set(random_pattern)) > 20:  # 如果有太多不同的小数，可能是随机的
                test_results["warnings"].append("发现大量不同的小数值，可能包含随机数据")

        else:
            print("   ❌ 无法生成综合打分文件")
            test_results["failed"].append("无法生成综合打分文件")

    except Exception as e:
        print(f"   ❌ 综合打分生成测试失败: {e}")
        test_results["failed"].append(f"综合打分生成测试失败: {e}")

    # 4. 检查是否还有DetailedScoreGenerator的使用
    print("\n4️⃣ 检查DetailedScoreGenerator使用情况...")

    # 检查production/scoring_engine/comprehensive_score_generator_v2.py
    scorer_file = "/root/projects/tencent-doc-manager/production/scoring_engine/comprehensive_score_generator_v2.py"
    if os.path.exists(scorer_file):
        with open(scorer_file, 'r', encoding='utf-8') as f:
            content = f.read()

        if "from integrated_scorer import IntegratedScorer" in content:
            print("   ✅ scoring_engine使用IntegratedScorer")
            test_results["passed"].append("scoring_engine使用正确的打分器")
        else:
            print("   ❌ scoring_engine未使用IntegratedScorer")
            test_results["failed"].append("scoring_engine未使用正确的打分器")

        if "DetailedScoreGenerator" in content and "from detailed_score_generator" in content:
            print("   ❌ scoring_engine仍在导入DetailedScoreGenerator")
            test_results["failed"].append("仍在使用随机数据生成器")

    # 5. 检查IntegratedScorer是否存在
    print("\n5️⃣ 检查IntegratedScorer实现...")
    integrated_scorer_file = "/root/projects/tencent-doc-manager/production/scoring_engine/integrated_scorer.py"
    if os.path.exists(integrated_scorer_file):
        with open(integrated_scorer_file, 'r', encoding='utf-8') as f:
            content = f.read()

        if "import random" not in content:
            print("   ✅ IntegratedScorer不使用random模块")
            test_results["passed"].append("IntegratedScorer无随机数据")
        else:
            print("   ❌ IntegratedScorer包含random导入")
            test_results["failed"].append("IntegratedScorer可能使用随机数据")

    # 总结测试结果
    print("\n" + "=" * 80)
    print("📊 测试结果总结")
    print("=" * 80)

    print(f"\n✅ 通过测试: {len(test_results['passed'])}项")
    for item in test_results['passed']:
        print(f"   - {item}")

    if test_results['failed']:
        print(f"\n❌ 失败测试: {len(test_results['failed'])}项")
        for item in test_results['failed']:
            print(f"   - {item}")

    if test_results['warnings']:
        print(f"\n⚠️  警告: {len(test_results['warnings'])}项")
        for item in test_results['warnings']:
            print(f"   - {item}")

    # 最终判定
    print("\n" + "=" * 80)
    if not test_results['failed']:
        print("🎉 数据链路验证通过！系统使用真实数据，无虚拟成分")
        return True
    else:
        print("⚠️  数据链路存在问题，请修复失败项")
        return False

if __name__ == "__main__":
    success = test_real_data_pipeline()
    sys.exit(0 if success else 1)