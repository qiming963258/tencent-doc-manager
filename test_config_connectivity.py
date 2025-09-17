#!/usr/bin/env python3
"""
配置中心连通性深度测试
测试范围：
1. 配置加载和单例模式
2. 列名标准化和别名处理
3. 风险分级正确性
4. 权重和参数获取
5. 配置一致性验证
6. 模块间配置传播
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple
import traceback

# 添加项目路径
sys.path.insert(0, '/root/projects/tencent-doc-manager')

def test_config_center_basics():
    """测试配置中心基础功能"""
    print("\n" + "="*60)
    print("📌 测试1: 配置中心基础功能")
    print("="*60)

    results = []

    try:
        # 1. 导入测试
        from production.config import get_config_center, STANDARD_COLUMNS
        from production.config.config_center import ConfigCenter
        results.append(("配置中心导入", "✅ 成功"))

        # 2. 单例模式测试
        config1 = get_config_center()
        config2 = get_config_center()
        if config1 is config2:
            results.append(("单例模式", "✅ 正确"))
        else:
            results.append(("单例模式", "❌ 失败 - 不是单例"))

        # 3. 标准列获取
        columns = config1.get_standard_columns()
        if len(columns) == 19:
            results.append(("标准列数量", f"✅ 正确 - 19列"))
        else:
            results.append(("标准列数量", f"❌ 错误 - {len(columns)}列"))

        # 4. 关键列名验证
        key_columns = {
            14: "完成链接",
            15: "经理分析复盘",
            16: "最新复盘时间"
        }

        for idx, expected in key_columns.items():
            actual = columns[idx]
            if actual == expected:
                results.append((f"列{idx}名称", f"✅ {actual}"))
            else:
                results.append((f"列{idx}名称", f"❌ 期望'{expected}'，实际'{actual}'"))

    except Exception as e:
        results.append(("基础功能测试", f"❌ 异常: {str(e)}"))

    return results

def test_column_aliases():
    """测试列名别名处理"""
    print("\n" + "="*60)
    print("📌 测试2: 列名别名和标准化")
    print("="*60)

    results = []

    try:
        from production.config import normalize_column_name

        # 测试旧列名转换
        test_cases = [
            ("形成计划清单", "完成链接"),
            ("进度分析总结", "经理分析复盘"),
            ("复盘时间", "最新复盘时间"),
            ("完成链接", "完成链接"),  # 已经是新名称
            ("序号", "序号")  # 无别名的列
        ]

        for old_name, expected in test_cases:
            actual = normalize_column_name(old_name)
            if actual == expected:
                results.append((f"别名'{old_name}'", f"✅ → '{actual}'"))
            else:
                results.append((f"别名'{old_name}'", f"❌ 期望'{expected}'，实际'{actual}'"))

    except Exception as e:
        results.append(("别名处理测试", f"❌ 异常: {str(e)}"))

    return results

def test_risk_classification():
    """测试风险分级配置"""
    print("\n" + "="*60)
    print("📌 测试3: 风险分级配置")
    print("="*60)

    results = []

    try:
        from production.config import (
            L1_COLUMNS, L2_COLUMNS, L3_COLUMNS,
            get_column_risk_level
        )

        # 1. 分级数量验证
        total = len(L1_COLUMNS) + len(L2_COLUMNS) + len(L3_COLUMNS)
        if total == 19:
            results.append(("风险分级总数", f"✅ {total}列"))
        else:
            results.append(("风险分级总数", f"❌ {total}列，应为19列"))

        results.append(("L1高风险", f"📊 {len(L1_COLUMNS)}列"))
        results.append(("L2中风险", f"📊 {len(L2_COLUMNS)}列"))
        results.append(("L3低风险", f"📊 {len(L3_COLUMNS)}列"))

        # 2. 关键列风险级别验证
        test_columns = {
            "重要程度": "L1",
            "负责人": "L2",
            "完成链接": "L3",
            "经理分析复盘": "L3",
            "最新复盘时间": "L3"
        }

        for col, expected_level in test_columns.items():
            actual_level = get_column_risk_level(col)
            if actual_level == expected_level:
                results.append((f"'{col}'风险级别", f"✅ {actual_level}"))
            else:
                results.append((f"'{col}'风险级别", f"❌ 期望{expected_level}，实际{actual_level}"))

        # 3. 检查是否有重复
        all_risk_columns = L1_COLUMNS + L2_COLUMNS + L3_COLUMNS
        if len(all_risk_columns) == len(set(all_risk_columns)):
            results.append(("列分级重复检查", "✅ 无重复"))
        else:
            results.append(("列分级重复检查", "❌ 存在重复列"))

    except Exception as e:
        results.append(("风险分级测试", f"❌ 异常: {str(e)}"))

    return results

def test_scoring_parameters():
    """测试打分参数配置"""
    print("\n" + "="*60)
    print("📌 测试4: 打分参数配置")
    print("="*60)

    results = []

    try:
        from production.config import get_column_weight
        from production.config.scoring_parameters import (
            BASE_SCORES, FORCE_THRESHOLDS, DIFFUSION_PARAMS
        )

        # 1. 权重获取测试
        test_weights = {
            "重要程度": 1.4,  # L1权重
            "负责人": 1.2,    # L2权重
            "序号": 1.0       # L3权重（默认）
        }

        for col, expected_weight in test_weights.items():
            actual_weight = get_column_weight(col)
            if abs(actual_weight - expected_weight) < 0.01:
                results.append((f"'{col}'权重", f"✅ {actual_weight}"))
            else:
                results.append((f"'{col}'权重", f"❌ 期望{expected_weight}，实际{actual_weight}"))

        # 2. 基础分数配置
        if BASE_SCORES:
            results.append(("基础分数配置", f"✅ {len(BASE_SCORES)}项"))
        else:
            results.append(("基础分数配置", "⚠️ 未配置"))

        # 3. 阈值配置
        if FORCE_THRESHOLDS:
            results.append(("强制阈值配置", f"✅ {len(FORCE_THRESHOLDS)}项"))
        else:
            results.append(("强制阈值配置", "⚠️ 未配置"))

        # 4. 扩散参数
        if DIFFUSION_PARAMS:
            results.append(("扩散算法参数", f"✅ {len(DIFFUSION_PARAMS)}项"))
        else:
            results.append(("扩散算法参数", "⚠️ 未配置"))

    except Exception as e:
        results.append(("打分参数测试", f"❌ 异常: {str(e)}"))

    return results

def test_module_integration():
    """测试各模块的配置集成"""
    print("\n" + "="*60)
    print("📌 测试5: 模块集成测试")
    print("="*60)

    results = []

    # 测试不同模块的配置使用
    modules_to_test = [
        ("comparison_to_scoring_adapter", "对比到打分适配器"),
        ("csv_comparison", "CSV对比模块"),
        ("ai_column_classifier", "AI列分类器"),
        ("scoring_engine", "打分引擎")
    ]

    for module_name, description in modules_to_test:
        try:
            module = __import__(f"production.core_modules.{module_name}", fromlist=[module_name])

            # 检查模块是否有使用配置
            has_config = any([
                hasattr(module, 'STANDARD_COLUMNS'),
                hasattr(module, 'L1_COLUMNS'),
                hasattr(module, 'L2_COLUMNS'),
                hasattr(module, 'L3_COLUMNS'),
                'from production.config' in str(module.__dict__.get('__file__', '')),
                'from standard_columns_config' in str(module.__dict__.get('__file__', ''))
            ])

            if has_config:
                results.append((description, "✅ 使用配置"))
            else:
                results.append((description, "⚠️ 可能未使用配置"))

        except ImportError as e:
            results.append((description, f"⚠️ 导入失败: {str(e)}"))
        except Exception as e:
            results.append((description, f"❌ 异常: {str(e)}"))

    return results

def test_config_consistency():
    """测试配置一致性"""
    print("\n" + "="*60)
    print("📌 测试6: 配置一致性验证")
    print("="*60)

    results = []

    try:
        from production.config import get_config_center

        config = get_config_center()

        # 验证配置一致性
        is_consistent = config.validate_config_consistency()

        if is_consistent:
            results.append(("配置一致性", "✅ 通过"))
        else:
            results.append(("配置一致性", "❌ 不一致"))

        # 获取配置统计
        stats = config.get_config_stats()

        for key, value in stats.items():
            results.append((key, f"📊 {value}"))

    except Exception as e:
        results.append(("一致性验证", f"❌ 异常: {str(e)}"))

    return results

def test_heatmap_server_config():
    """测试热力图服务配置连通性"""
    print("\n" + "="*60)
    print("📌 测试7: 热力图服务配置连通性")
    print("="*60)

    results = []

    try:
        # 检查热力图数据文件
        heatmap_file = Path("/root/projects/tencent-doc-manager/scoring_results/csv_comparison/latest_csv_heatmap.json")

        if heatmap_file.exists():
            with open(heatmap_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 检查列名
            column_names = data.get('column_names', [])

            # 检查是否仍有旧列名
            old_names = ["形成计划清单", "进度分析总结", "复盘时间"]
            has_old_names = any(name in column_names for name in old_names)

            if has_old_names:
                results.append(("热力图数据", "⚠️ 包含旧列名（缓存数据）"))
                for i, name in enumerate(column_names):
                    if name in old_names:
                        results.append((f"  列{i}", f"❌ '{name}' (旧)"))
            else:
                results.append(("热力图数据", "✅ 使用新列名"))

            # 检查列数
            if len(column_names) == 19:
                results.append(("列数量", "✅ 19列"))
            else:
                results.append(("列数量", f"❌ {len(column_names)}列"))

        else:
            results.append(("热力图数据文件", "⚠️ 不存在"))

        # 测试服务器导入
        try:
            # 不实际运行服务器，只测试导入
            sys.path.insert(0, '/root/projects/tencent-doc-manager/production/servers')
            import final_heatmap_server

            # 检查是否使用配置
            server_code = Path("/root/projects/tencent-doc-manager/production/servers/final_heatmap_server.py").read_text()

            if "from standard_columns_config import" in server_code:
                results.append(("服务器配置导入", "✅ 使用standard_columns_config"))
            elif "from production.config import" in server_code:
                results.append(("服务器配置导入", "✅ 使用production.config"))
            else:
                results.append(("服务器配置导入", "⚠️ 可能硬编码"))

        except Exception as e:
            results.append(("服务器导入", f"❌ 异常: {str(e)}"))

    except Exception as e:
        results.append(("热力图服务测试", f"❌ 异常: {str(e)}"))

    return results

def test_backward_compatibility():
    """测试向后兼容性"""
    print("\n" + "="*60)
    print("📌 测试8: 向后兼容性")
    print("="*60)

    results = []

    try:
        # 测试旧的导入方式
        from standard_columns_config import STANDARD_COLUMNS as OLD_COLUMNS
        from production.config import STANDARD_COLUMNS as NEW_COLUMNS

        # 比较是否一致
        if OLD_COLUMNS == NEW_COLUMNS:
            results.append(("旧导入方式", "✅ 完全兼容"))
        else:
            results.append(("旧导入方式", "❌ 不兼容"))

        # 测试其他导入
        from standard_columns_config import (
            L1_COLUMNS as OLD_L1,
            L2_COLUMNS as OLD_L2,
            L3_COLUMNS as OLD_L3
        )
        from production.config import (
            L1_COLUMNS as NEW_L1,
            L2_COLUMNS as NEW_L2,
            L3_COLUMNS as NEW_L3
        )

        if OLD_L1 == NEW_L1:
            results.append(("L1列兼容性", "✅ 一致"))
        else:
            results.append(("L1列兼容性", f"❌ 不一致"))

        if OLD_L2 == NEW_L2:
            results.append(("L2列兼容性", "✅ 一致"))
        else:
            results.append(("L2列兼容性", f"❌ 不一致"))

        if OLD_L3 == NEW_L3:
            results.append(("L3列兼容性", "✅ 一致"))
        else:
            results.append(("L3列兼容性", f"❌ 不一致"))

    except Exception as e:
        results.append(("向后兼容性", f"❌ 异常: {str(e)}"))

    return results

def print_results(test_name: str, results: List[Tuple[str, str]]):
    """打印测试结果"""
    for item, status in results:
        print(f"  {item:30} {status}")

def main():
    """主测试函数"""
    print("\n" + "🔬"*30)
    print("🔬 配置中心连通性深度测试报告 🔬")
    print("🔬"*30)

    all_results = {}

    # 执行所有测试
    tests = [
        ("基础功能", test_config_center_basics),
        ("列名别名", test_column_aliases),
        ("风险分级", test_risk_classification),
        ("打分参数", test_scoring_parameters),
        ("模块集成", test_module_integration),
        ("配置一致性", test_config_consistency),
        ("热力图服务", test_heatmap_server_config),
        ("向后兼容", test_backward_compatibility)
    ]

    total_tests = 0
    passed_tests = 0
    warnings = 0

    for test_name, test_func in tests:
        try:
            results = test_func()
            all_results[test_name] = results
            print_results(test_name, results)

            # 统计结果
            for item, status in results:
                total_tests += 1
                if "✅" in status:
                    passed_tests += 1
                elif "⚠️" in status:
                    warnings += 1

        except Exception as e:
            print(f"\n❌ 测试'{test_name}'执行失败: {str(e)}")
            traceback.print_exc()

    # 打印总结
    print("\n" + "="*60)
    print("📊 测试总结")
    print("="*60)
    print(f"  总测试项: {total_tests}")
    print(f"  ✅ 通过: {passed_tests}")
    print(f"  ⚠️ 警告: {warnings}")
    print(f"  ❌ 失败: {total_tests - passed_tests - warnings}")
    print(f"  通过率: {passed_tests/total_tests*100:.1f}%")

    # 关键建议
    print("\n" + "="*60)
    print("💡 关键建议")
    print("="*60)

    if warnings > 0:
        print("  1. 清理缓存数据：")
        print("     rm -f /root/projects/tencent-doc-manager/scoring_results/csv_comparison/latest_csv_heatmap.json")
        print("  2. 重启热力图服务：")
        print("     systemctl restart heatmap-server 或 重新运行 final_heatmap_server.py")
        print("  3. 重新生成数据以使用新配置")

    if passed_tests == total_tests:
        print("  ✨ 配置中心连通性完美！所有测试通过。")
    elif passed_tests / total_tests > 0.8:
        print("  👍 配置中心连通性良好，建议处理警告项。")
    else:
        print("  ⚠️ 配置中心存在问题，需要修复失败项。")

if __name__ == "__main__":
    main()